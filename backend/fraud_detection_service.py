import joblib
import pandas as pd
from pathlib import Path
import re

class FraudDetector:
    def __init__(self):
        self.model = None
        # Recherche flexible dans le dossier 'ml' ou 'ia'
        base_dir = Path(__file__).parent.parent
        model_path_ml = base_dir / "ml" / "saved_models" / "fraud_model.joblib"
        model_path_ia = base_dir / "ia" / "saved_models" / "fraud_model.joblib"
        
        if model_path_ml.exists():
            self.model = joblib.load(model_path_ml)
        elif model_path_ia.exists():
            self.model = joblib.load(model_path_ia)
        else:
            print("⚠️ Attention: Modèle ML introuvable. Seul le moteur de règles fonctionnera.")

    def analyze_document(self, extracted_data: dict) -> dict:
        """
        Analyse les données extraites en croisant moteur de règles et Machine Learning.
        """
        is_fraud = False
        fraud_reasons = []

        # 1. MOTEUR DE RÈGLES (Cross-check métier)
        doc_type = extracted_data.get("document_type", "unknown")
        
        # Règle : Vérification SIRET
        siret_attendu = extracted_data.get("expected_siret")
        siret_lu = extracted_data.get("siret")
        if siret_attendu and siret_lu and siret_attendu != siret_lu:
            is_fraud = True
            fraud_reasons.append(f"Incohérence SIRET (Lu: {siret_lu})")

        # 2. MACHINE LEARNING (Anomalies complexes comme 'montant_altere')
        if self.model and doc_type in ["facture", "devis"]:
            # Extraction Regex de secours si le HT n'est pas fourni explicitement
            ocr_text = str(extracted_data.get('ocr_text', ''))
            match_ht = re.search(r'(?:HT|Total HT|Montant HT)\s*[:\-]?\s*([\d\s]+[.,]\d{2})', ocr_text, re.IGNORECASE)
            montant_ht = float(match_ht.group(1).replace(' ', '').replace(',', '.')) if match_ht else 0.0
            
            montant_ttc = float(extracted_data.get('amount_total') or 0.0)
            
            # Même logique de tolérance multi-TVA que pour l'entraînement
            ecart_montant = 0.0
            if montant_ttc > 0 and montant_ht > 0:
                ecart_montant = min([abs(montant_ttc - (montant_ht * (1 + rate))) for rate in [0.0, 0.055, 0.10, 0.20]])
                ecart_montant = round(ecart_montant, 2)

            montant_manquant = 1 if (montant_ttc == 0 or montant_ht == 0) else 0
            ecart_suspect = 1 if ecart_montant > 1.0 else 0

            # Grâce au Pipeline, on lui passe juste un DataFrame classique !
            X_infer = pd.DataFrame([{
                "document_type": doc_type, 
                "ecart_montant": ecart_montant, 
                "montant_manquant": montant_manquant,
                "ecart_suspect": ecart_suspect
            }])

            prediction = self.model.predict(X_infer)[0]
            if prediction == 1:
                is_fraud = True
                fraud_reasons.append("Anomalie détectée sur les montants (ML)")

            return {
                "status": "FRAUDE" if is_fraud else "VALIDE",
                "fraud_summary": ", ".join(fraud_reasons) if is_fraud else "Aucune anomalie détectée",
                "fraud_score": 0.95 if is_fraud else 0.05 # Peut être affiné avec model.predict_proba()
            }
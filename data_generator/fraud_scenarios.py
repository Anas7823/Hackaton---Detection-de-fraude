"""
Scénarios de documents frauduleux pour le dataset de détection de fraude.
Réutilise les générateurs existants avec des paramètres de fraude.
"""

import random

from models import Company
from document_generator import (
    generate_invoice,
    generate_devis,
    generate_attestation_urssaf,
    generate_kbis,
    generate_rib,
)


def generate_fraud_invoice(emetteur: Company, client: Company, show_titre: bool = True):
    """Facture avec montant TTC altéré (incohérent avec les lignes)."""
    from document_generator import render_facture_override
    doc, _ = generate_invoice(emetteur, client, show_titre)
    faux_ttc = round(doc.total_ttc + random.uniform(300, 3000), 2)
    html = render_facture_override(emetteur, client, doc, show_titre, faux_ttc)
    return doc, html, "montant_altere"


def generate_fraud_devis(emetteur: Company, client: Company, show_titre: bool = True):
    """Devis avec montant TTC altéré."""
    from document_generator import render_devis_override
    doc, _ = generate_devis(emetteur, client, show_titre)
    faux_ttc = round(doc.total_ttc + random.uniform(200, 2000), 2)
    html = render_devis_override(emetteur, client, doc, show_titre, faux_ttc)
    return doc, html, "montant_altere"


def generate_fraud_attestation_urssaf(emetteur: Company):
    """Attestation URSSAF expirée."""
    doc, html = generate_attestation_urssaf(emetteur, expired=True)
    return doc, html, "attestation_expiree"


def generate_fraud_kbis(emetteur: Company, autre_entreprise: Company):
    """Kbis affichant les données d'une autre entreprise."""
    doc, html = generate_kbis(emetteur, wrong_entreprise=autre_entreprise)
    return doc, html, "mauvais_siret"


def generate_fraud_rib(emetteur: Company):
    """RIB avec IBAN invalide (format incorrect)."""
    iban_invalide = "FR99 1234 5678 9012 3456 7890 123"  # Format faux
    doc, html = generate_rib(emetteur, fraud_iban=iban_invalide)
    return doc, html, "iban_invalide"

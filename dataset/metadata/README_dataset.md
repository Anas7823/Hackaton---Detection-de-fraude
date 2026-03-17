# Dataset / Ground Truth

## But

Générer `dataset/metadata/ground_truth.csv` à partir de `data_generator/output/`.

## Entrées

- `data_generator/output/documents_manifest.csv`
- `data_generator/output/raw/`
- `data_generator/output/scans/` (si présent)

## Règles

- Aucun fichier n'est copié dans `dataset/`
- Les chemins fichiers sont dans `source_dataset_path`
- Les fraudes viennent du manifest (`is_fraud`, `fraud_type`)

## Colonnes du CSV

`filename`, `doc_type`, `is_fraud`, `fraud_type`, `siret_doc`, `date_expiration`, `montant_ht`, `montant_ttc`, `degradation`, `linked_group_id`, `source_dataset_path`

## Fraudes

- `montant_altere`
- `attestation_expiree`
- `mauvais_siret`
- `iban_invalide`

## Commande

```bash
python.exe dataset/scripts/build_dataset.py
```

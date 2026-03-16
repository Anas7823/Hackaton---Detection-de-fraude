# 📄 Plateforme IDP - Traitement Automatique de Documents Administratifs

> **Projet de Hackathon (3 Jours)** : Une plateforme d'Intelligent Document Processing (IDP) sécurisée, permettant l'ingestion, la classification, l'extraction et la vérification intelligente de pièces comptables sensibles.

---

## 📑 Table des matières
1. [Contexte et Mission](#-contexte-et-mission)
2. [Architecture et Pipeline](#-architecture-et-pipeline)
3. [Stack Technique](#-stack-technique)
4. [Fonctionnalités Clés](#-fonctionnalités-clés)
5. [Guide d'Installation (Quickstart)](#-guide-dinstallation)
6. [Organisation de l'Équipe](#-organisation-de-léquipe)

---

## 🏢 Contexte et Mission
Notre client est une entreprise traitant quotidiennement des milliers de documents administratifs sensibles (factures, attestations URSSAF, devis). La validation manuelle de ces documents est chronophage et sujette à l'erreur humaine (fraudes, erreurs de saisie).

**Notre mission :** Développer une plateforme complète permettant :
- L'**upload multi-documents** sécurisé.
- La **classification** et l'**extraction d'informations clés** via un OCR robuste.
- La **détection d'anomalies** (incohérences de montants, SIRET expirés, fraudes).
- Le stockage structuré au sein d'un **Data Lake** (Architecture Medallion).

---

## 🏗 Architecture et Pipeline

Le projet repose sur une **Architecture Medallion** conteneurisée, assurant la traçabilité et l'intégrité de la donnée tout au long de son cycle de vie.

*(Insérez ici un schéma de votre architecture)*

* **1. Ingestion ➔ Zone Bronze (Raw) :** Sauvegarde immuable du document original (PDF/Scan) dès son upload.
* **2. Intelligence & OCR ➔ Zone Silver (Clean) :** Lecture par le modèle **DocTR**, extraction des entités (Regex), nettoyage avec **Pandas** et sauvegarde structurée au format `.parquet`.
* **3. Validation & ML ➔ Zone Gold (Curated) :** Vérification par moteur de règles croisées (ex: *SIRET Facture vs SIRET Attestation*) et modèle d'**Anomaly Detection**. Ajout du statut de validation et exposition des données pour les applications métiers.

---

## 💻 Stack Technique

L'intégralité de la plateforme est packagée sous **Docker** pour garantir l'industrialisation et la reproductibilité de l'environnement.

| Domaine | Technologie | Rôle |
| :--- | :--- | :--- |
| **Backend / API** | `FastAPI` (Python) | Cœur de l'application, orchestration asynchrone, exposition des endpoints. |
| **Frontend** | `React` / `Vue.js` + `TailwindCSS` | Interface utilisateur (Upload) et Dashboard de conformité métier. |
| **Stockage (Data Lake)** | `MinIO` | Stockage objet local compatible S3 (hébergement des zones Bronze, Silver, Gold). |
| **Traitement Data** | `Pandas` + `DuckDB` | Nettoyage de la donnée, formatage Parquet et requêtage analytique ultra-rapide. |
| **IA & OCR** | `DocTR` (Mindee) | Modèle de vision par ordinateur pour l'extraction de texte robuste. |
| **Machine Learning** | `Scikit-Learn` | Modèles de Random Forest / Isolation Forest pour la détection de fraudes. |
| **Génération Données**| `Faker` + API Sirene | Création du dataset synthétique (vérité terrain) d'entraînement. |

---

## 🚀 Fonctionnalités Clés

- [x] **Dropzone multi-fichiers :** Interface fluide pour l'ingestion de lots de documents.
- [x] **Classification Automatique :** Identification du type de document sans intervention humaine.
- [x] **Extraction Robuste :** Récupération ciblée du SIRET, Montant HT, Montant TTC, TVA et Dates.
- [x] **Moteur de validation métier :** Vérification mathématique stricte des montants.
- [x] **Détection de fraude (Cross-check) :** Levée d'alerte en cas d'incohérence entre les documents d'un même fournisseur.
- [x] **Dashboard de Restitution :** Suivi en temps réel des documents traités, validés ou rejetés avec motifs explicites.

---

## 🛠 Guide d'Installation

### Prérequis
* [Docker](https://docs.docker.com/get-docker/) et [Docker Compose](https://docs.docker.com/compose/install/) installés sur votre machine.
* Git.

### Lancement de l'environnement (One-Click)

1. Clonez le dépôt et naviguez dans le dossier du projet :
```bash
git clone [https://github.com/votre-organisation/idp-project.git](https://github.com/votre-organisation/idp-project.git)
cd idp-project
```

2. Lancez l'infrastructure via Docker Compose :
```bash
docker-compose up -d --build
```
Note : Au premier lancement, un conteneur d'initialisation créera automatiquement les buckets bronze-zone, silver-zone et gold-zone.

3. Accédez aux interfaces :
- Backend API (Swagger UI) : http://localhost:8000/docs

- Data Lake Console (MinIO) : http://localhost:9001
(Identifiants par défaut : admin_idp / SuperSecretPassword123!)

- Frontend App : http://localhost:3000 (Port à adapter selon config)

---

## 👥 Organisation de l'Équipe

Ce projet a été réalisé en 3 jours par une "Squad" Data/MLOps composée de 6 ingénieurs :

Pôle Ingénierie des Données & Front (M1) :

- Étudiant 1 & 7 : Data Engineer (Génération de datasets synthétiques & Vérité terrain).

- Étudiant 2 : ML Engineer Vision (Pipeline d'extraction DocTR & Structuration JSON).

- Étudiant 3 : Full-Stack Developer (Développement interfaces React & Dashboard).

Pôle Architecture & Intelligence (M2) :

- Étudiant 4 : Cloud & Data Architect (Conteneurisation, MinIO, Backend FastAPI).

- Étudiant 5 : Data Scientist (Détection d'anomalies, Modélisation ML, Moteur de règles).

- Étudiant 6: Orchestration Engineer (Pipeline de données, requêtage analytique DuckDB).
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

Le projet repose sur une **Architecture Medallion** conteneurisée, assurant la traçabilité et l'intégrité de la donnée tout au long de son cycle de vie. Le tout est orchestré automatiquement.

* **1. Ingestion ➔ Zone Bronze (Raw) :** Sauvegarde immuable du document original (PDF/Scan) dès son upload via l'API FastAPI.
* **2. Intelligence & OCR ➔ Zone Silver (Clean) :** Détection du fichier par **Airflow**, lecture par le modèle **DocTR**, extraction des entités, nettoyage avec **Pandas** et sauvegarde structurée au format `.parquet`.
* **3. Validation & ML ➔ Zone Gold (Curated) :** Vérification par moteur de règles croisées et modèle d'**Anomaly Detection**. Ajout du statut de validation.
* **4. Restitution ➔ Dashboard :** Requêtage instantané des fichiers Parquet de la Gold Zone grâce à **DuckDB** (Zero-copy analytics) pour affichage sur le Front-end.

---

## 💻 Stack Technique

L'intégralité de la plateforme est packagée sous **Docker** pour garantir l'industrialisation et la reproductibilité de l'environnement.

| Domaine | Technologie | Rôle |
| :--- | :--- | :--- |
| **Backend / API** | `FastAPI` (Python) | Cœur de l'application, exposition des endpoints d'ingestion. |
| **Frontend** | `React` / `Vue.js` | Interface utilisateur (Upload) et Dashboard de conformité métier. |
| **Stockage (Data Lake)** | `MinIO` | Stockage objet local compatible S3 (Architecture Medallion). |
| **Orchestration** | `Apache Airflow` | Automatisation du pipeline (détection S3, déclenchement OCR et ML). |
| **Traitement Data** | `Pandas` + `DuckDB` | Nettoyage, formatage Parquet et requêtage analytique ultra-rapide. |
| **IA & OCR** | `DocTR` (Mindee) | Modèle de vision par ordinateur pour l'extraction de texte robuste. |
| **Machine Learning** | `Scikit-Learn` | Modèles de Machine Learning pour la détection de fraudes. |

---

## 🚀 Fonctionnalités Clés

- [x] **Dropzone multi-fichiers :** Interface fluide pour l'ingestion de lots de documents.
- [x] **Orchestration Automatisée :** Déclenchement des traitements par Airflow dès l'arrivée d'un fichier.
- [x] **Classification Automatique :** Identification du type de document sans intervention humaine.
- [x] **Extraction Robuste :** Récupération ciblée du SIRET, Montant HT, Montant TTC, TVA et Dates.
- [x] **Détection de fraude (Cross-check) :** Levée d'alerte en cas d'incohérence entre les documents.
- [x] **Dashboard de Restitution :** Suivi en temps réel des documents traités, validés ou rejetés.

---

## 🛠 Guide d'Installation

### Prérequis
* [Docker](https://docs.docker.com/get-docker/) et [Docker Compose](https://docs.docker.com/compose/install/) installés sur votre machine.
* Le fichier `.env` configuré à la racine du projet sous cette forme :

```bash
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=choix_libre
MINIO_ROOT_PASSWORD=choix_libre
```

### Lancement de l'environnement (One-Click)

1. Clonez le dépôt et naviguez dans le dossier du projet :
```bash
git clone [https://github.com/Anas7823/Hackaton---Detection-de-fraude.git](https://github.com/Anas7823/Hackaton---Detection-de-fraude.git)
cd idp-project
```

2. Lancez l'infrastructure complète via Docker Compose :
```bash
docker-compose up -d --build
```
Note : Au premier lancement, il faudra créer les buckets bronze-zone, silver-zone et gold-zone depuis MinIO.

3. Initialisez la connexion de l'orchestrateur (Airflow ↔️ MinIO) :

```bash
python setup_infra.py
```

## 🌐 Accès aux interfaces
- **Backend API (Swagger UI)** : http://localhost:8000/docs
- **Orchestrateur (Airflow)** : http://localhost:8080 (Identifiants : admin / admin)
- **Data Lake Console (MinIO)** : http://localhost:9001 (Identifiants : cf. fichier .env)
- **Frontend App** : http://localhost:3000

---

## 👥 Organisation de l'équipe

Ce projet a été réalisé en 3 jours par une "Squad" Data/MLOps composée de 7 ingénieurs :

Pôle Ingénierie des Données & Front :
- **Étudiant 1 :** Data Engineer (Génération de datasets synthétiques & Vérité terrain).
- **Étudiant 2 :** ML Engineer Vision (Pipeline d'extraction DocTR & Structuration JSON).
- **Étudiant 3 :** Full-Stack Developer (Développement interfaces & Dashboard).

Pôle Architecture & Intelligence :
- **Étudiant 4 :** Cloud & Data Architect (Conteneurisation, MinIO, Backend FastAPI, DuckDB).
- **Étudiant 5 :** Data Scientist (Détection d'anomalies, Modélisation ML, Moteur de règles).
- **Étudiant 6 :** Data Analyst (Analyse des performances et requêtage avancé).
- **Étudiant 7 :** Data Engineer (Orchestration des pipelines avec Apache Airflow).


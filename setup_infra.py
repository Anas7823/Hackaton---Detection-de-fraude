# import os
# import subprocess
# import time

# def run_command(command):
#     """Exécute une commande shell et affiche le résultat"""
#     try:
#         result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
#         print(result.stdout)
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Erreur lors de l'exécution : {e.stderr}")

# def setup():
#     print("🚀 Démarrage de la configuration automatique de l'infrastructure...")

#     # 1. Chargement des variables du .env (lecture manuelle pour éviter les dépendances)
#     env_vars = {}
#     if os.path.exists(".env"):
#         with open(".env") as f:
#             for line in f:
#                 if "=" in line and not line.startswith("#"):
#                     key, value = line.strip().split("=", 1)
#                     env_vars[key] = value
#     else:
#         print("❌ Erreur : Fichier .env introuvable à la racine !")
#         return

#     user = env_vars.get("MINIO_ROOT_USER")
#     pw = env_vars.get("MINIO_ROOT_PASSWORD")

#     # 2. Création de l'utilisateur Admin Airflow (Si besoin, sinon on peut se connecter avec admin/admin déjà créé par défaut)
#     # print("👤 Création de l'utilisateur admin Airflow...")
#     # run_command(
#     #     f"docker exec idp_airflow airflow users create "
#     #     f"--username admin --firstname Admin --lastname Team "
#     #     f"--role Admin --email admin@idp.com --password admin"
#     # )

#     # 3. Configuration de la connexion S3 (MinIO)
#     print("🔗 Configuration de la connexion S3 dans Airflow...")
#     # On prépare le JSON pour le flag --conn-extra
#     extra_json = f'{{"endpoint_url": "http://minio:9000", "aws_access_key_id": "{user}", "aws_secret_access_key": "{pw}", "host": "http://minio:9000", "url_style": "path", "use_ssl": false}}'
    
#     # On supprime la connexion si elle existe déjà pour éviter l'erreur
#     run_command("docker exec idp_airflow airflow connections delete minio_conn")
    
#     # On ajoute la nouvelle connexion
#     run_command(
#         f"docker exec idp_airflow airflow connections add 'minio_conn' "
#         f"--conn-type 'aws' --conn-extra '{extra_json}'"
#     )

#     print("\n✅ Configuration terminée !")
#     print("👉 Airflow : http://localhost:8080 (admin / admin)")
#     print("👉 MinIO : http://localhost:9001")

# if __name__ == "__main__":
#     setup()

import os
import subprocess

def run_command(command_list, ignore_error=False):
    """Exécute une commande proprement en évitant le shell Windows"""
    try:
        # On n'utilise plus shell=True, et on passe une liste d'arguments
        result = subprocess.run(command_list, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        if not ignore_error:
            print(f"❌ Erreur : {e.stderr.strip()}")

def setup():
    print("🚀 Démarrage de la configuration automatique de l'infrastructure...")

    # 1. Chargement des variables du .env
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value
    else:
        print("❌ Erreur : Fichier .env introuvable à la racine !")
        return

    user = env_vars.get("MINIO_ROOT_USER")
    pw = env_vars.get("MINIO_ROOT_PASSWORD")

    # 2. Configuration de la connexion S3 (MinIO)
    print("🔗 Configuration de la connexion S3 dans Airflow...")
    extra_json = f'{{"endpoint_url": "http://minio:9000", "aws_access_key_id": "{user}", "aws_secret_access_key": "{pw}", "host": "http://minio:9000", "url_style": "path", "use_ssl": false}}'
    
    # Étape A : On supprime silencieusement si elle existe déjà (ignore_error=True évite le message rouge)
    run_command(["docker", "exec", "idp_airflow", "airflow", "connections", "delete", "minio_conn"], ignore_error=True)
    
    # Étape B : On ajoute la connexion avec notre JSON sécurisé
    run_command([
        "docker", "exec", "idp_airflow", "airflow", "connections", "add", "minio_conn",
        "--conn-type", "aws",
        "--conn-extra", extra_json
    ])

    print("\n✅ Configuration terminée avec succès !")
    print("👉 Airflow : http://localhost:8080 (admin / admin)")
    print("👉 MinIO : http://localhost:9001")

if __name__ == "__main__":
    setup()
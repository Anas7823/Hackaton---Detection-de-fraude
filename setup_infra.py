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

    # Création de l'utilisateur Admin Airflow
    print("👤 Configuration de l'utilisateur admin Airflow...")
    
    # On supprime l'utilisateur par défaut généré par Airflow (ignore_error=True pour ne pas planter s'il n'existe pas)
    run_command(["docker", "exec", "idp_airflow", "airflow", "users", "delete", "--username", "admin"], ignore_error=True)
    
    # On recrée notre propre utilisateur avec le mot de passe "admin"
    run_command([
        "docker", "exec", "idp_airflow", "airflow", "users", "create",
        "--username", "admin", "--firstname", "Admin", "--lastname", "Admin",
        "--role", "Admin", "--email", "admin@idp.com", "--password", "admin"
    ])

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
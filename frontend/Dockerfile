# frontend/Dockerfile
FROM node:18-alpine

# Définir le dossier de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de configuration de npm
COPY package.json package-lock.json* ./

# C'EST ICI QUE LE NPM INSTALL SE FAIT (au moment du build de l'image)
RUN npm install

# (Optionnel en dev) Copier le reste du code
COPY . .

# La commande de lancement est déjà définie dans le docker-compose.yml

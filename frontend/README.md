# Hackathon IDP - Front MVP

Frontend React/Vite pour le hackathon 2026 avec 2 pages :

- `Upload` (`/upload`)
- `Conformite` (`/conformite`)

## Demarrage

```bash
npm install
npm run dev
```

## Variables d'environnement

Copier `.env.example` vers `.env` puis adapter :

- `VITE_API_MODE=mock|live`
- `VITE_API_BASE_URL=http://localhost:8000`

Par defaut, le projet utilise le provider `mock`.

## Integration backend rapide

Le front est deja prepare pour ignorer totalement les mocks quand le backend est pret.

1. Basculer le mode dans `.env`:

```env
VITE_API_MODE=live
VITE_API_BASE_URL=http://localhost:8000
```

2. Adapter uniquement ce fichier si necessaire:

- `src/services/providers/backendProvider.js`

3. Reference des mocks et points d'integration:

- `docs/mock-integration-map.md`

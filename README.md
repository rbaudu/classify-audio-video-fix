# Classify Audio Video

Système de classification d'activités basé sur l'analyse audio et vidéo en temps réel.

## Description

Ce projet permet de capturer des flux audio et vidéo (via OBS), de les analyser et de classer les activités détectées. Il fournit une interface web pour visualiser les activités en temps réel et consulter les statistiques.

## Prérequis

- Python 3.8+
- OBS Studio 28+ avec le plugin obs-websocket 5.0.0+
- Un périphérique d'entrée audio (microphone)
- Une caméra ou source vidéo configurée dans OBS

## Installation

1. Cloner le dépôt :
   ```
   git clone https://github.com/rbaudu/classify-audio-video.git
   cd classify-audio-video
   ```

2. Créer un environnement virtuel et l'activer :
   ```
   python -m venv venv
   source venv/bin/activate  # Pour Linux/Mac
   venv\Scripts\activate     # Pour Windows
   ```

3. Installer les dépendances :
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Démarrer OBS Studio et activer le plugin WebSocket (Outils > WebSocket Server Settings)
   - Port par défaut : 4455
   - Mot de passe : optionnel (laisser vide pour des tests)

2. Configurer au moins une source vidéo dans OBS (caméra, capture d'écran, etc.)

## Utilisation

1. Démarrer le serveur :
   ```
   python run.py
   ```

2. Accéder à l'interface web via :
   ```
   http://localhost:5000
   ```

3. Pages disponibles :
   - `/` - Page d'accueil
   - `/dashboard` - Tableau de bord des activités en temps réel
   - `/statistics` - Statistiques des activités
   - `/history` - Historique des activités
   - `/model_testing` - Page de test du modèle
   - `/settings` - Paramètres

## Résolution des problèmes

### Erreur de connexion à OBS

Si vous rencontrez des erreurs de connexion à OBS, vérifiez que :
- OBS est en cours d'exécution
- Le plugin WebSocket est activé dans OBS
- Le port configuré (par défaut 4455) est correct
- Aucun pare-feu ne bloque la connexion

### Pas de vidéo dans l'interface

Si la vidéo ne s'affiche pas :
- Vérifiez qu'au moins une source vidéo est configurée et active dans OBS
- Vérifiez les logs pour les erreurs liées à OBS
- Essayez de redémarrer OBS puis le serveur

### Pas de données dans le tableau de bord

Si aucune activité n'est affichée dans le tableau de bord :
- Vérifiez que la base de données est correctement initialisée
- Vérifiez les logs pour les erreurs liées à la base de données
- Essayez de forcer une analyse manuelle via l'API `/api/classify`

## Structure du projet

```
classify-audio-video/
│
├── run.py                # Point d'entrée
├── requirements.txt      # Dépendances
├── README.md             # Documentation
│
├── server/               # Code serveur
│   ├── main.py           # Module principal
│   ├── database/         # Gestion de la base de données
│   ├── api/              # Services externes
│   ├── capture/          # Capture audio/vidéo
│   ├── analysis/         # Analyse et classification
│   ├── routes/           # Routes web et API
│   └── utils/            # Utilitaires
│
├── static/               # Fichiers statiques (CSS, JS)
│   ├── css/              # Feuilles de style
│   └── js/               # Scripts JavaScript
│
└── templates/            # Templates HTML
    ├── index.html        # Page d'accueil
    ├── dashboard.html    # Tableau de bord
    └── ...               # Autres pages
```

## API

Le serveur expose les API REST suivantes :

- `GET /api/current-activity` - Récupère l'activité courante
- `GET /api/video-status` - Récupère l'état de la vidéo
- `GET /api/video-snapshot` - Récupère une image instantanée de la vidéo
- `GET /api/activities` - Récupère les activités enregistrées
- `GET /api/statistics` - Récupère des statistiques sur les activités
- `POST /api/classify` - Effectue une classification manuelle

## Licence

Ce projet est sous licence MIT.

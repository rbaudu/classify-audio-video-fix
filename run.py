#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
from server.main import init_app, start_app

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Initialisation du système de gestion d'erreurs")
        app = init_app()
        start_app(app)
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {str(e)}")
        sys.exit(1)

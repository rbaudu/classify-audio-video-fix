# -*- coding: utf-8 -*-
"""
Module principal du serveur
"""

import logging
import os
from flask import Flask

# Import des modules internes
from server.utils.error_system import ErrorSystem
from server.database.db_manager import DBManager
from server.api.external_service import ExternalServiceClient
from server.capture.obs_capture import OBSCapture
from server.capture.pyaudio_capture import PyAudioCapture
from server.capture.stream_processor import StreamProcessor
from server.capture.sync_manager import SyncManager
from server.analysis.activity_classifier import ActivityClassifier
from server.routes.api_routes import register_api_routes
from server.routes.web_routes import register_web_routes

logger = logging.getLogger(__name__)

def init_app():
    """Initialise l'application Flask et les composants nécessaires"""
    
    # Initialisation du système de gestion d'erreurs
    logger.info("Initialisation du système de gestion d'erreurs")
    error_system = ErrorSystem()
    
    # Initialisation de la base de données
    db_manager = DBManager()
    
    # Initialisation du client de service externe
    external_service = ExternalServiceClient(url="https://api.exemple.com/activity")
    
    # Initialisation de la capture OBS
    obs_capture = OBSCapture(host="localhost", port=4455)
    
    # Initialisation de la capture audio
    pyaudio_capture = PyAudioCapture()
    
    # Initialisation du processeur de flux
    stream_processor = StreamProcessor(
        video_resolution=(640, 480),
        audio_sample_rate=16000
    )
    
    # Initialisation du gestionnaire de synchronisation
    sync_manager = SyncManager(
        obs_capture=obs_capture,
        pyaudio_capture=pyaudio_capture,
        stream_processor=stream_processor
    )
    
    # Initialisation du classificateur d'activités
    activity_classifier = ActivityClassifier(sync_manager=sync_manager)
    
    # Création de l'app Flask
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='../templates')
    
    # Enregistrement des routes API
    register_api_routes(app, db_manager, sync_manager, activity_classifier)
    
    # Enregistrement des routes Web
    register_web_routes(app)
    
    # Stockage des objets dans le contexte de l'application
    app.config['DB_MANAGER'] = db_manager
    app.config['SYNC_MANAGER'] = sync_manager
    app.config['ACTIVITY_CLASSIFIER'] = activity_classifier
    app.config['ERROR_SYSTEM'] = error_system
    
    return app

def start_app(app):
    """Démarre l'application Flask et la capture"""
    
    # Récupération des objets depuis le contexte de l'application
    sync_manager = app.config['SYNC_MANAGER']
    activity_classifier = app.config['ACTIVITY_CLASSIFIER']
    
    # Démarrage de la capture
    sync_manager.start()
    
    # Démarrage de l'analyse périodique
    activity_classifier.start_analysis_loop()
    
    logger.info("Démarrage du serveur classify-audio-video...")
    logger.info("Accédez à l'interface via http://localhost:5000")
    logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
    
    # Démarrage du serveur Flask
    app.run(host='0.0.0.0', port=5000)

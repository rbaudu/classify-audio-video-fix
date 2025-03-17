# -*- coding: utf-8 -*-
"""
Routes Web pour le serveur Flask
"""

import logging
from flask import render_template, redirect, url_for

logger = logging.getLogger(__name__)

def register_web_routes(app):
    """Enregistre les routes Web pour l'application Flask
    
    Args:
        app (Flask): Application Flask
    """
    
    @app.route('/')
    def index():
        """Page d'accueil
        
        Returns:
            Response: Rendu du template index.html
        """
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Tableau de bord des activités
        
        Returns:
            Response: Rendu du template dashboard.html
        """
        return render_template('dashboard.html')
    
    @app.route('/statistics')
    def statistics():
        """Statistiques des activités
        
        Returns:
            Response: Rendu du template statistics.html
        """
        return render_template('statistics.html')
    
    @app.route('/history')
    def history():
        """Historique des activités
        
        Returns:
            Response: Rendu du template history.html
        """
        return render_template('history.html')
    
    @app.route('/model_testing')
    def model_testing():
        """Page de test du modèle
        
        Returns:
            Response: Rendu du template model_testing.html
        """
        return render_template('model_testing.html')
    
    @app.route('/settings')
    def settings():
        """Page de paramètres
        
        Returns:
            Response: Rendu du template settings.html
        """
        return render_template('settings.html')
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Gestionnaire d'erreur 404
        
        Args:
            e (Exception): Exception d'erreur
        
        Returns:
            Response: Rendu du template 404.html
        """
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Gestionnaire d'erreur 500
        
        Args:
            e (Exception): Exception d'erreur
        
        Returns:
            Response: Rendu du template 500.html
        """
        logger.error(f"Erreur serveur: {str(e)}")
        return render_template('500.html'), 500

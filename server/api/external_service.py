# -*- coding: utf-8 -*-
"""
Client pour les services externes
"""

import logging
import json
import time
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class ExternalServiceClient:
    """Client pour les services externes"""
    
    def __init__(self, url, timeout=5, retry_count=3, retry_delay=1):
        """Initialise le client de service externe
        
        Args:
            url (str): URL du service externe
            timeout (int, optional): Délai d'attente en secondes. Par défaut 5.
            retry_count (int, optional): Nombre de tentatives. Par défaut 3.
            retry_delay (int, optional): Délai entre les tentatives en secondes. Par défaut 1.
        """
        self.url = url
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        
        logger.info(f"Client de service externe initialisé avec l'URL {url}")
    
    def send_activity(self, activity):
        """Envoie une activité au service externe
        
        Args:
            activity (dict): Activité à envoyer
        
        Returns:
            dict: Réponse du service externe, ou None si erreur
        """
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Envoi de l'activité {activity.get('type')} au service externe")
                
                response = requests.post(
                    self.url,
                    json=activity,
                    timeout=self.timeout,
                    headers={'Content-Type': 'application/json'}
                )
                
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Activité envoyée avec succès, réponse: {result}")
                
                return result
            
            except RequestException as e:
                logger.warning(f"Tentative {attempt + 1}/{self.retry_count} échouée: {str(e)}")
                
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Échec de l'envoi de l'activité après {self.retry_count} tentatives")
                    return None
    
    def get_activities(self, start_time=None, end_time=None, limit=100):
        """Récupère les activités depuis le service externe
        
        Args:
            start_time (int, optional): Timestamp de début. Par défaut None.
            end_time (int, optional): Timestamp de fin. Par défaut None.
            limit (int, optional): Nombre maximal d'activités. Par défaut 100.
        
        Returns:
            list: Liste des activités, ou None si erreur
        """
        params = {}
        
        if start_time:
            params['start'] = start_time
        
        if end_time:
            params['end'] = end_time
        
        if limit:
            params['limit'] = limit
        
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Récupération des activités depuis le service externe")
                
                response = requests.get(
                    self.url,
                    params=params,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                result = response.json()
                activities = result.get('activities', [])
                
                logger.info(f"Récupération de {len(activities)} activités réussie")
                
                return activities
            
            except RequestException as e:
                logger.warning(f"Tentative {attempt + 1}/{self.retry_count} échouée: {str(e)}")
                
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Échec de la récupération des activités après {self.retry_count} tentatives")
                    return None
    
    def ping(self):
        """Vérifie la disponibilité du service externe
        
        Returns:
            bool: True si le service est disponible, False sinon
        """
        try:
            response = requests.get(
                f"{self.url}/ping",
                timeout=self.timeout
            )
            
            return response.status_code == 200
        
        except RequestException:
            return False

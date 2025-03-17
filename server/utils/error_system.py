# -*- coding: utf-8 -*-
"""
Système de gestion d'erreurs
"""

import logging
import traceback
import time
import threading
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorSystem:
    """Système de gestion d'erreurs pour le serveur"""
    
    def __init__(self, error_log_path="logs/errors.json", max_errors=100):
        """Initialise le système de gestion d'erreurs
        
        Args:
            error_log_path (str, optional): Chemin vers le fichier de log d'erreurs. Par défaut "logs/errors.json".
            max_errors (int, optional): Nombre maximal d'erreurs à conserver. Par défaut 100.
        """
        self.error_log_path = error_log_path
        self.max_errors = max_errors
        
        # Liste des erreurs (en mémoire)
        self.errors = []
        
        # Verrou pour l'accès à la liste des erreurs
        self.error_lock = threading.Lock()
        
        # Créer le répertoire de logs si nécessaire
        os.makedirs(os.path.dirname(error_log_path), exist_ok=True)
        
        # Charger les erreurs précédentes si le fichier existe
        self._load_errors()
        
        logger.info("Système de gestion d'erreurs initialisé")
    
    def _load_errors(self):
        """Charge les erreurs depuis le fichier"""
        if os.path.exists(self.error_log_path):
            try:
                with open(self.error_log_path, 'r', encoding='utf-8') as f:
                    loaded_errors = json.load(f)
                    
                    with self.error_lock:
                        self.errors = loaded_errors
                
                logger.info(f"Chargement de {len(self.errors)} erreurs depuis {self.error_log_path}")
            
            except Exception as e:
                logger.error(f"Erreur lors du chargement des erreurs: {str(e)}")
                self.errors = []
    
    def _save_errors(self):
        """Sauvegarde les erreurs dans le fichier"""
        try:
            with open(self.error_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, indent=2)
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des erreurs: {str(e)}")
    
    def log_error(self, error_type, message, details=None, source=None):
        """Enregistre une erreur
        
        Args:
            error_type (str): Type d'erreur
            message (str): Message d'erreur
            details (str, optional): Détails supplémentaires. Par défaut None.
            source (str, optional): Source de l'erreur. Par défaut None.
        
        Returns:
            dict: Erreur enregistrée
        """
        timestamp = int(time.time())
        error_id = f"err_{timestamp}_{hash(message) % 10000:04d}"
        
        error = {
            "id": error_id,
            "type": error_type,
            "message": message,
            "details": details,
            "source": source,
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with self.error_lock:
            # Ajouter l'erreur au début de la liste
            self.errors.insert(0, error)
            
            # Limiter le nombre d'erreurs
            if len(self.errors) > self.max_errors:
                self.errors = self.errors[:self.max_errors]
            
            # Sauvegarder les erreurs
            self._save_errors()
        
        logger.error(f"Erreur enregistrée: {error_type} - {message}")
        
        return error
    
    def log_exception(self, exception, source=None):
        """Enregistre une exception
        
        Args:
            exception (Exception): Exception à enregistrer
            source (str, optional): Source de l'exception. Par défaut None.
        
        Returns:
            dict: Erreur enregistrée
        """
        error_type = type(exception).__name__
        message = str(exception)
        details = traceback.format_exc()
        
        return self.log_error(error_type, message, details, source)
    
    def get_errors(self, limit=10, offset=0, error_type=None):
        """Récupère les erreurs enregistrées
        
        Args:
            limit (int, optional): Nombre maximal d'erreurs à récupérer. Par défaut 10.
            offset (int, optional): Décalage pour la pagination. Par défaut 0.
            error_type (str, optional): Filtrer par type d'erreur. Par défaut None.
        
        Returns:
            list: Liste des erreurs
        """
        with self.error_lock:
            if error_type:
                # Filtrer par type d'erreur
                filtered_errors = [e for e in self.errors if e.get('type') == error_type]
            else:
                filtered_errors = self.errors
            
            # Appliquer la pagination
            paginated_errors = filtered_errors[offset:offset + limit]
            
            return paginated_errors
    
    def clear_errors(self):
        """Efface toutes les erreurs
        
        Returns:
            int: Nombre d'erreurs effacées
        """
        with self.error_lock:
            count = len(self.errors)
            self.errors = []
            self._save_errors()
        
        logger.info(f"{count} erreurs effacées")
        
        return count
    
    def get_error_types(self):
        """Récupère tous les types d'erreurs enregistrés
        
        Returns:
            list: Liste des types d'erreurs
        """
        with self.error_lock:
            # Extraire les types d'erreurs uniques
            error_types = list(set(e.get('type') for e in self.errors if 'type' in e))
            
            return sorted(error_types)
    
    def get_error_stats(self):
        """Récupère des statistiques sur les erreurs
        
        Returns:
            dict: Statistiques d'erreurs
        """
        with self.error_lock:
            # Compter les erreurs par type
            type_counts = {}
            for e in self.errors:
                error_type = e.get('type')
                if error_type:
                    type_counts[error_type] = type_counts.get(error_type, 0) + 1
            
            # Compter les erreurs par jour
            day_counts = {}
            for e in self.errors:
                day = datetime.fromtimestamp(e.get('timestamp', 0)).strftime('%Y-%m-%d')
                day_counts[day] = day_counts.get(day, 0) + 1
            
            return {
                "total": len(self.errors),
                "by_type": type_counts,
                "by_day": day_counts
            }

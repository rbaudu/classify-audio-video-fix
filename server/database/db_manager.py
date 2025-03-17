# -*- coding: utf-8 -*-
"""
Gestionnaire de base de données pour le système de classification d'activités
"""

import logging
import sqlite3
import os
import json
import time
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DBManager:
    """Gestionnaire de base de données SQLite pour stocker les activités détectées"""
    
    def __init__(self, db_path="data/activities.db"):
        """Initialise le gestionnaire de base de données
        
        Args:
            db_path (str): Chemin vers le fichier de base de données SQLite
        """
        self.db_path = db_path
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialiser la base de données
        self._init_db()
        logger.info("Base de données initialisée avec succès")
    
    def _init_db(self):
        """Initialise la structure de la base de données"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Créer la table des activités si elle n'existe pas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            duration INTEGER DEFAULT 0,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        
        # Vérifier si la table contient des données
        cursor.execute("SELECT COUNT(*) FROM activities")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("Base de données vide, création de données factices pour les tests")
            self._create_dummy_data()
            logger.info("Création de données factices terminée")
        else:
            logger.info(f"Base de données existante avec {count} activités")
        
        cursor.close()
        conn.close()
    
    def _get_connection(self):
        """Obtient une connexion à la base de données
        
        Returns:
            sqlite3.Connection: Connexion à la base de données
        """
        return sqlite3.connect(self.db_path)
    
    def _create_dummy_data(self):
        """Crée des données factices pour les tests"""
        activity_types = [
            "lecture", "écriture", "programmation", "navigation_web",
            "visioconférence", "vidéo", "audio", "pause", "inactif"
        ]
        
        # Générer des données pour les 7 derniers jours
        now = int(time.time())
        activities = []
        
        for i in range(672):  # ~96 activités par jour sur 7 jours
            # Timestamp aléatoire dans les 7 derniers jours
            timestamp = now - random.randint(0, 7 * 24 * 60 * 60)
            
            # Type d'activité aléatoire
            activity_type = random.choice(activity_types)
            
            # Confiance aléatoire entre 0.6 et 1.0
            confidence = round(random.uniform(0.6, 1.0), 2)
            
            # Durée aléatoire entre 1 et 30 minutes (en secondes)
            duration = random.randint(60, 30 * 60)
            
            # Métadonnées (peut contenir des infos spécifiques à l'activité)
            metadata = {
                "details": f"Activité {activity_type} détectée",
                "source": "dummy_data"
            }
            
            activities.append((timestamp, activity_type, confidence, duration, json.dumps(metadata)))
        
        # Insérer les données dans la base de données
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.executemany(
            "INSERT INTO activities (timestamp, activity_type, confidence, duration, metadata) VALUES (?, ?, ?, ?, ?)",
            activities
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Sauvegarde de {len(activities)} activités fictives dans la base de données")
    
    def save_activity(self, activity_type, confidence, duration=0, metadata=None):
        """Enregistre une activité détectée dans la base de données
        
        Args:
            activity_type (str): Type d'activité détectée
            confidence (float): Niveau de confiance de la détection (entre 0 et 1)
            duration (int, optional): Durée de l'activité en secondes. Par défaut 0.
            metadata (dict, optional): Métadonnées supplémentaires. Par défaut None.
        
        Returns:
            int: ID de l'activité enregistrée
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        timestamp = int(time.time())
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute(
            "INSERT INTO activities (timestamp, activity_type, confidence, duration, metadata) VALUES (?, ?, ?, ?, ?)",
            (timestamp, activity_type, confidence, duration, metadata_json)
        )
        
        activity_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return activity_id
    
    def get_activities(self, start_time=None, end_time=None, limit=100, offset=0):
        """Récupère les activités enregistrées avec pagination
        
        Args:
            start_time (int, optional): Timestamp de début. Par défaut None.
            end_time (int, optional): Timestamp de fin. Par défaut None.
            limit (int, optional): Nombre maximal d'activités à récupérer. Par défaut 100.
            offset (int, optional): Décalage pour la pagination. Par défaut 0.
        
        Returns:
            list: Liste des activités
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, timestamp, activity_type, confidence, duration, metadata FROM activities"
        params = []
        
        # Construire la clause WHERE en fonction des paramètres
        where_clauses = []
        
        if start_time is not None:
            where_clauses.append("timestamp >= ?")
            params.append(start_time)
        
        if end_time is not None:
            where_clauses.append("timestamp <= ?")
            params.append(end_time)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # Ajouter l'ordre et la pagination
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        # Formater les résultats
        activities = []
        for row in cursor.fetchall():
            activity = {
                "id": row[0],
                "timestamp": row[1],
                "activity_type": row[2],
                "confidence": row[3],
                "duration": row[4],
                "metadata": json.loads(row[5]) if row[5] else None
            }
            activities.append(activity)
        
        cursor.close()
        conn.close()
        
        return activities
    
    def get_latest_activity(self):
        """Récupère l'activité la plus récente
        
        Returns:
            dict: Dernière activité, ou None si aucune activité
        """
        activities = self.get_activities(limit=1)
        return activities[0] if activities else None
    
    def get_activity_stats(self, period="day"):
        """Récupère des statistiques sur les activités pour une période donnée
        
        Args:
            period (str, optional): Période ('day', 'week', 'month'). Par défaut "day".
        
        Returns:
            dict: Statistiques d'activités
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Définir la plage de temps en fonction de la période
        now = int(time.time())
        
        if period == "day":
            # Dernières 24 heures
            start_time = now - (24 * 60 * 60)
        elif period == "week":
            # Derniers 7 jours
            start_time = now - (7 * 24 * 60 * 60)
        elif period == "month":
            # Derniers 30 jours
            start_time = now - (30 * 24 * 60 * 60)
        else:
            # Par défaut, dernières 24 heures
            start_time = now - (24 * 60 * 60)
        
        # Récupérer le nombre d'activités par type
        cursor.execute("""
        SELECT activity_type, COUNT(*) as count, AVG(duration) as avg_duration
        FROM activities
        WHERE timestamp >= ?
        GROUP BY activity_type
        ORDER BY count DESC
        """, (start_time,))
        
        activity_counts = {}
        for row in cursor.fetchall():
            activity_type, count, avg_duration = row
            activity_counts[activity_type] = {
                "count": count,
                "avg_duration": round(avg_duration if avg_duration else 0)
            }
        
        # Récupérer le temps total par activité
        cursor.execute("""
        SELECT activity_type, SUM(duration) as total_duration
        FROM activities
        WHERE timestamp >= ?
        GROUP BY activity_type
        ORDER BY total_duration DESC
        """, (start_time,))
        
        for row in cursor.fetchall():
            activity_type, total_duration = row
            if activity_type in activity_counts:
                activity_counts[activity_type]["total_duration"] = total_duration
        
        # Calculer les statistiques globales
        cursor.execute("""
        SELECT COUNT(*) as total_activities, 
               SUM(duration) as total_duration,
               AVG(duration) as avg_duration,
               AVG(confidence) as avg_confidence
        FROM activities
        WHERE timestamp >= ?
        """, (start_time,))
        
        row = cursor.fetchone()
        total_stats = {
            "total_activities": row[0],
            "total_duration": row[1] if row[1] else 0,
            "avg_duration": round(row[2] if row[2] else 0),
            "avg_confidence": round(row[3] if row[3] else 0, 2)
        }
        
        cursor.close()
        conn.close()
        
        return {
            "period": period,
            "start_time": start_time,
            "end_time": now,
            "activities": activity_counts,
            "stats": total_stats
        }
    
    def delete_activity(self, activity_id):
        """Supprime une activité de la base de données
        
        Args:
            activity_id (int): ID de l'activité à supprimer
        
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        
        success = cursor.rowcount > 0
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return success
    
    def clear_database(self):
        """Supprime toutes les données de la base de données
        
        Returns:
            bool: True si l'opération a réussi
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM activities")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True

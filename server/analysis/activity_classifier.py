# -*- coding: utf-8 -*-
"""
Classificateur d'activités basé sur l'audio et la vidéo
"""

import logging
import time
import threading
import json
import os
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class ActivityClassifier:
    """Classificateur d'activités basé sur l'analyse audio et vidéo"""
    
    def __init__(self, sync_manager, model_path=None, min_confidence=0.6, analysis_interval=60):
        """Initialise le classificateur d'activités
        
        Args:
            sync_manager (SyncManager): Gestionnaire de synchronisation.
            model_path (str, optional): Chemin vers le modèle ML. Par défaut None (règles).
            min_confidence (float, optional): Confiance minimale pour les prédictions. Par défaut 0.6.
            analysis_interval (int, optional): Intervalle entre les analyses (secondes). Par défaut 60.
        """
        self.sync_manager = sync_manager
        self.model_path = model_path
        self.min_confidence = min_confidence
        self.analysis_interval = analysis_interval
        
        # Charger le modèle ML s'il existe
        self.model = None
        self._load_model()
        
        # État de l'analyse
        self.is_analyzing = False
        self.analysis_thread = None
        self.last_activity = None
        self.last_analysis_time = 0
        
        # Verrou pour les données d'activité
        self.activity_lock = threading.Lock()
    
    def _load_model(self):
        """Charge le modèle de ML si disponible"""
        if self.model_path and os.path.exists(self.model_path):
            try:
                # Ici, nous pourrions charger un modèle ML (TensorFlow, scikit-learn, etc.)
                # Pour cette implémentation, nous utiliserons un classificateur basé sur des règles
                logger.info(f"Chargement du modèle depuis {self.model_path}")
                
                # Placeholder pour le chargement du modèle
                self.model = "rule_based"  # À remplacer par le chargement réel du modèle
                
            except Exception as e:
                logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
                self.model = None
        else:
            logger.info("Modèle non spécifié ou introuvable. Utilisation du classificateur basé sur des règles prédéfinies")
            self.model = None
    
    def start_analysis_loop(self):
        """Démarre la boucle d'analyse périodique"""
        if self.is_analyzing:
            return
        
        # Démarrer le thread d'analyse
        self.is_analyzing = True
        logger.info(f"SyncManager fourni pour l'analyse périodique: {self.sync_manager}")
        
        self.analysis_thread = threading.Thread(
            target=self._analysis_loop,
            daemon=True
        )
        self.analysis_thread.start()
        
        logger.info("Démarrage de la boucle d'analyse périodique")
        logger.info(f"Boucle d'analyse démarrée avec intervalle de {self.analysis_interval} secondes")
    
    def _analysis_loop(self):
        """Boucle d'analyse périodique"""
        while self.is_analyzing:
            try:
                # Effectuer une analyse
                self.analyze_current_activity()
                
                # Attendre avant la prochaine analyse
                time.sleep(self.analysis_interval)
            
            except Exception as e:
                logger.error(f"Erreur dans la boucle d'analyse: {str(e)}")
                time.sleep(5)  # Courte pause en cas d'erreur
    
    def stop_analysis_loop(self):
        """Arrête la boucle d'analyse périodique"""
        self.is_analyzing = False
        
        if self.analysis_thread:
            self.analysis_thread.join(timeout=1.0)
            self.analysis_thread = None
        
        logger.info("Boucle d'analyse arrêtée")
    
    def analyze_current_activity(self):
        """Analyse l'activité actuelle et met à jour l'état
        
        Returns:
            dict: Activité détectée, ou None si aucune activité
        """
        # Récupérer les données synchronisées
        video_frame, audio_data, timestamp = self.sync_manager.get_sync_data()
        
        if video_frame is None or audio_data is None:
            logger.warning("Impossible de récupérer les données synchronisées")
            return None
        
        # Extraire les caractéristiques
        video_features = self._extract_video_features(video_frame)
        audio_features = self._extract_audio_features(audio_data)
        
        # Classifier l'activité
        activity = self._classify_activity(video_features, audio_features)
        
        if activity:
            # Mettre à jour l'activité détectée
            with self.activity_lock:
                self.last_activity = activity
                self.last_analysis_time = time.time()
            
            return activity
        else:
            logger.warning("Aucune activité détectée lors de cette analyse")
            return None
    
    def _extract_video_features(self, video_frame):
        """Extrait des caractéristiques vidéo pour la classification
        
        Args:
            video_frame (PIL.Image.Image): Image à analyser
        
        Returns:
            dict: Caractéristiques extraites
        """
        if video_frame is None:
            return {}
        
        try:
            # Convertir en niveaux de gris
            gray_frame = video_frame.convert("L")
            
            # Convertir en tableau numpy
            frame_array = np.array(gray_frame)
            
            # Calculer des statistiques de base
            mean_intensity = np.mean(frame_array)
            std_intensity = np.std(frame_array)
            min_intensity = np.min(frame_array)
            max_intensity = np.max(frame_array)
            
            # Calculer l'histogramme (10 bins)
            hist, _ = np.histogram(frame_array, bins=10, range=(0, 255))
            hist = hist / np.sum(hist)  # Normaliser
            
            # Assembler les caractéristiques
            features = {
                "mean_intensity": float(mean_intensity),
                "std_intensity": float(std_intensity),
                "min_intensity": float(min_intensity),
                "max_intensity": float(max_intensity),
                "histogram": hist.tolist()
            }
            
            return features
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de caractéristiques vidéo: {str(e)}")
            return {}
    
    def _extract_audio_features(self, audio_data):
        """Extrait des caractéristiques audio pour la classification
        
        Args:
            audio_data (numpy.ndarray): Données audio à analyser
        
        Returns:
            dict: Caractéristiques extraites
        """
        if audio_data is None or len(audio_data) == 0:
            return {}
        
        try:
            # Calculer des statistiques de base
            mean_amplitude = np.mean(audio_data)
            std_amplitude = np.std(audio_data)
            max_amplitude = np.max(np.abs(audio_data))
            
            # Calculer l'énergie du signal
            energy = np.sum(audio_data ** 2) / len(audio_data)
            
            # Calculer les taux de passage à zéro (zero-crossing rate)
            zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data)))) / len(audio_data)
            
            # Assembler les caractéristiques
            features = {
                "mean_amplitude": float(mean_amplitude),
                "std_amplitude": float(std_amplitude),
                "max_amplitude": float(max_amplitude),
                "energy": float(energy),
                "zero_crossing_rate": float(zero_crossings)
            }
            
            return features
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de caractéristiques audio: {str(e)}")
            return {}
    
    def _classify_activity(self, video_features, audio_features):
        """Classifie l'activité en fonction des caractéristiques extraites
        
        Args:
            video_features (dict): Caractéristiques vidéo
            audio_features (dict): Caractéristiques audio
        
        Returns:
            dict: Activité détectée avec confiance
        """
        if not video_features and not audio_features:
            return None
        
        # Si nous avons un modèle ML, l'utiliser
        if self.model and self.model != "rule_based":
            # Placeholder pour l'utilisation d'un modèle ML
            # prédiction = self.model.predict([video_features, audio_features])
            # return {"type": prédiction[0], "confidence": prédiction[1]}
            pass
        
        # Sinon, utiliser un classificateur basé sur des règles
        return self._rule_based_classification(video_features, audio_features)
    
    def _rule_based_classification(self, video_features, audio_features):
        """Classification basée sur des règles prédéfinies
        
        Args:
            video_features (dict): Caractéristiques vidéo
            audio_features (dict): Caractéristiques audio
        
        Returns:
            dict: Activité détectée avec confiance
        """
        # Valeurs par défaut
        activity_type = "inactif"
        confidence = 0.6
        
        # Si pas de caractéristiques, retourner inactif
        if not video_features and not audio_features:
            return {
                "type": activity_type,
                "confidence": confidence,
                "timestamp": int(time.time()),
                "duration": 0
            }
        
        # Règles basées sur l'audio (prioritaires si fort niveau sonore)
        if audio_features and audio_features.get("energy", 0) > 0.1:
            if audio_features.get("zero_crossing_rate", 0) > 0.2:
                # Beaucoup de passages à zéro suggère la parole
                activity_type = "visioconférence"
                confidence = min(0.7 + audio_features.get("energy", 0), 0.95)
            else:
                # Son fort avec peu de passages à zéro suggère de la musique ou vidéo
                activity_type = "vidéo"
                confidence = min(0.65 + audio_features.get("energy", 0), 0.9)
        
        # Règles basées sur la vidéo
        elif video_features:
            std_intensity = video_features.get("std_intensity", 0)
            mean_intensity = video_features.get("mean_intensity", 0)
            
            if std_intensity < 20:
                # Peu de variation suggère une image statique
                if mean_intensity < 100:
                    # Image sombre suggère l'inactivité
                    activity_type = "inactif"
                    confidence = 0.8
                else:
                    # Image claire mais statique suggère la lecture
                    activity_type = "lecture"
                    confidence = 0.7
            elif std_intensity > 50:
                # Beaucoup de variation suggère une vidéo
                activity_type = "vidéo"
                confidence = 0.75
            else:
                # Variation modérée suggère une navigation web
                activity_type = "navigation_web"
                confidence = 0.65
        
        # Règles de combinaison audio/vidéo pour affiner la classification
        if video_features and audio_features:
            video_std = video_features.get("std_intensity", 0)
            audio_energy = audio_features.get("energy", 0)
            
            if video_std > 30 and audio_energy > 0.05:
                # Variation vidéo et son suggère une visioconférence ou vidéo
                activity_type = "visioconférence"
                confidence = 0.85
        
        # Retourner l'activité détectée
        return {
            "type": activity_type,
            "confidence": confidence,
            "timestamp": int(time.time()),
            "duration": 0
        }
    
    def get_current_activity(self):
        """Récupère l'activité courante
        
        Returns:
            dict: Activité courante, ou None si aucune activité
        """
        with self.activity_lock:
            return self.last_activity

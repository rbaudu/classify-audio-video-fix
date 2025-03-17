# -*- coding: utf-8 -*-
"""
Gestionnaire de synchronisation pour la capture audio/vidéo
"""

import logging
import time
import threading
from queue import Queue
import io
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class SyncManager:
    """Gestionnaire de synchronisation pour coordonner la capture audio et vidéo"""
    
    def __init__(self, obs_capture, pyaudio_capture, stream_processor, buffer_size=10):
        """Initialise le gestionnaire de synchronisation
        
        Args:
            obs_capture (OBSCapture): Instance de capture OBS
            pyaudio_capture (PyAudioCapture): Instance de capture PyAudio
            stream_processor (StreamProcessor): Instance du processeur de flux
            buffer_size (int, optional): Taille du buffer de synchronisation. Par défaut 10.
        """
        self.obs_capture = obs_capture
        self.pyaudio_capture = pyaudio_capture
        self.stream_processor = stream_processor
        self.buffer_size = buffer_size
        
        # Buffer pour les données synchronisées
        self.video_buffer = Queue(maxsize=buffer_size)
        self.audio_buffer = Queue(maxsize=buffer_size)
        
        # Données synchronisées actuelles
        self.current_video_frame = None
        self.current_audio_data = None
        self.last_sync_time = 0
        
        # Verrou pour l'accès aux données synchronisées
        self.sync_lock = threading.Lock()
        
        # Thread de synchronisation
        self.sync_thread = None
        self.is_running = False
        
        logger.info("Gestionnaire de synchronisation initialisé")
    
    def start(self):
        """Démarre la capture synchronisée"""
        if self.is_running:
            logger.warning("La capture synchronisée est déjà en cours")
            return
        
        # Démarrer la capture audio
        self.pyaudio_capture.start()
        
        # Démarrer la capture vidéo (utiliser la première source vidéo disponible)
        video_source = None
        if self.obs_capture.video_sources:
            video_source = self.obs_capture.video_sources[0]
        
        if video_source:
            self.obs_capture.start_capture(source_name=video_source, interval=0.1)
        else:
            logger.warning("Aucune source vidéo disponible, capture vidéo désactivée")
        
        # Démarrer le thread de synchronisation
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        logger.info("Thread de capture synchronisée démarré")
        logger.info("Capture synchronisée démarrée")
    
    def start_capture(self):
        """Alias pour start() pour la compatibilité"""
        logger.info("Appel à start_capture(), redirection vers start()")
        self.start()
    
    def _sync_loop(self):
        """Boucle de synchronisation exécutée dans un thread"""
        while self.is_running:
            # Récupérer une image de la caméra
            video_frame, video_time = self.obs_capture.get_current_frame()
            
            # Récupérer des données audio récentes
            audio_data = self.pyaudio_capture.get_latest_audio()
            
            # Si nous avons à la fois une vidéo et de l'audio
            if video_frame is not None and audio_data is not None:
                # Traiter les données
                processed_video = self.stream_processor.process_video(video_frame)
                processed_audio = self.stream_processor.process_audio(audio_data)
                
                # Mettre à jour les données synchronisées
                with self.sync_lock:
                    self.current_video_frame = processed_video
                    self.current_audio_data = processed_audio
                    self.last_sync_time = time.time()
            
            # Attendre un court instant avant la prochaine synchronisation
            time.sleep(0.05)
    
    def get_sync_data(self):
        """Récupère les données audio/vidéo synchronisées
        
        Returns:
            tuple: (video_frame, audio_data, timestamp) ou (None, None, 0) si aucune donnée
        """
        with self.sync_lock:
            if self.current_video_frame is None or self.current_audio_data is None:
                return None, None, 0
            return self.current_video_frame, self.current_audio_data, self.last_sync_time
    
    def get_current_frame(self):
        """Récupère l'image courante
        
        Returns:
            PIL.Image.Image: Image courante ou None
        """
        # Récupérer directement depuis OBS (plus récent)
        frame, _ = self.obs_capture.get_current_frame()
        
        # Si aucune image n'est disponible, essayer d'utiliser l'image synchronisée
        if frame is None:
            with self.sync_lock:
                frame = self.current_video_frame
        
        return frame
    
    def get_current_audio(self):
        """Récupère les données audio courantes
        
        Returns:
            numpy.ndarray: Données audio ou None
        """
        with self.sync_lock:
            return self.current_audio_data
    
    def get_frame_as_jpeg(self, quality=85):
        """Récupère l'image courante au format JPEG
        
        Args:
            quality (int, optional): Qualité JPEG. Par défaut 85.
        
        Returns:
            bytes: Données JPEG ou None
        """
        frame = self.get_current_frame()
        
        if frame is not None:
            # Convertir l'image en JPEG
            img_buffer = io.BytesIO()
            frame.save(img_buffer, format='JPEG', quality=quality)
            return img_buffer.getvalue()
        
        return None
    
    def stop(self):
        """Arrête la capture synchronisée"""
        if not self.is_running:
            return
        
        # Arrêter le thread de synchronisation
        self.is_running = False
        
        if self.sync_thread:
            self.sync_thread.join(timeout=1.0)
            self.sync_thread = None
        
        # Arrêter la capture audio et vidéo
        self.pyaudio_capture.stop()
        self.obs_capture.stop_capture()
        
        logger.info("Capture synchronisée arrêtée")
    
    def is_video_available(self):
        """Vérifie si la vidéo est disponible
        
        Returns:
            bool: True si la vidéo est disponible
        """
        frame = self.get_current_frame()
        return frame is not None
    
    def is_audio_available(self):
        """Vérifie si l'audio est disponible
        
        Returns:
            bool: True si l'audio est disponible
        """
        audio = self.get_current_audio()
        return audio is not None

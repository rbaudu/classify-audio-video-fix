# -*- coding: utf-8 -*-
"""
Module de capture audio via PyAudio
"""

import logging
import time
import threading
import numpy as np
import pyaudio

logger = logging.getLogger(__name__)

class PyAudioCapture:
    """Classe pour capturer l'audio via PyAudio"""
    
    def __init__(self, device_index=None, sample_rate=16000, chunk_size=1024, channels=1, format_type=pyaudio.paInt16, buffer_seconds=5):
        """Initialise la capture audio
        
        Args:
            device_index (int, optional): Indice du périphérique d'entrée. Par défaut None (périphérique par défaut).
            sample_rate (int, optional): Taux d'échantillonnage. Par défaut 16000.
            chunk_size (int, optional): Taille des chunks audio. Par défaut 1024.
            channels (int, optional): Nombre de canaux audio. Par défaut 1 (mono).
            format_type (int, optional): Format PyAudio. Par défaut paInt16.
            buffer_seconds (int, optional): Secondes de données audio à conserver en mémoire. Par défaut 5.
        """
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format_type = format_type
        self.buffer_seconds = buffer_seconds
        
        # Initialiser PyAudio
        self.pyaudio = pyaudio.PyAudio()
        
        # Calculer la taille du buffer en chunks
        chunks_per_second = self.sample_rate / self.chunk_size
        self.buffer_chunks = int(chunks_per_second * buffer_seconds)
        
        # Créer un buffer circulaire pour stocker les données audio
        self.audio_buffer = np.zeros((self.buffer_chunks, self.chunk_size), dtype=np.int16)
        self.buffer_index = 0
        
        # Verrou pour l'accès au buffer
        self.buffer_lock = threading.Lock()
        
        # Flux audio
        self.stream = None
        self.is_streaming = False
        self.stream_thread = None
        
        # Lister les périphériques audio disponibles
        self._list_devices()
        
        # Utiliser l'indice spécifié ou le périphérique d'entrée par défaut
        if self.device_index is None:
            logger.info("Utilisation du périphérique d'entrée par défaut (indice 0)")
            self.device_index = 0
    
    def _list_devices(self):
        """Liste les périphériques audio disponibles"""
        device_count = self.pyaudio.get_device_count()
        
        for i in range(device_count):
            device_info = self.pyaudio.get_device_info_by_index(i)
            
            # Afficher uniquement les périphériques d'entrée
            if device_info['maxInputChannels'] > 0:
                logger.info(f"Input Device {i}: {device_info['name']}")
        
        logger.info(f"PyAudio initialisé avec succès. {device_count} périphériques trouvés.")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback appelé par PyAudio pour chaque chunk audio
        
        Args:
            in_data (bytes): Données audio brutes.
            frame_count (int): Nombre de frames.
            time_info (dict): Information temporelle.
            status (int): État du flux.
        
        Returns:
            tuple: (None, pyaudio.paContinue)
        """
        # Convertir les données audio brutes en tableau numpy
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Ajouter les données au buffer circulaire
        with self.buffer_lock:
            self.audio_buffer[self.buffer_index] = audio_data
            self.buffer_index = (self.buffer_index + 1) % self.buffer_chunks
        
        return (None, pyaudio.paContinue)
    
    def start(self):
        """Démarre la capture audio"""
        if self.is_streaming:
            logger.warning("Capture audio déjà en cours")
            return
        
        try:
            # Ouvrir le flux audio
            device_info = self.pyaudio.get_device_info_by_index(self.device_index)
            device_name = device_info['name']
            logger.info(f"Ouverture du flux audio sur le périphérique {self.device_index}: {device_name}")
            
            self.stream = self.pyaudio.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            # Démarrer le flux audio
            self.stream.start_stream()
            self.is_streaming = True
            
            logger.info(f"Capture audio démarrée avec {device_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la capture audio: {str(e)}")
            
            # Essayer de se replier sur le périphérique par défaut en cas d'erreur
            if self.device_index != 0:
                logger.info("Tentative avec le périphérique d'entrée par défaut")
                self.device_index = 0
                self.start()
    
    def stop(self):
        """Arrête la capture audio"""
        if not self.is_streaming or self.stream is None:
            return
        
        # Arrêter et fermer le flux audio
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.is_streaming = False
        
        logger.info("Capture audio arrêtée")
    
    def get_latest_audio(self, duration_ms=500):
        """Récupère les dernières données audio capturées
        
        Args:
            duration_ms (int, optional): Durée des données à récupérer en ms. Par défaut 500.
        
        Returns:
            numpy.ndarray: Données audio, ou None si aucune donnée
        """
        if not self.is_streaming:
            return None
        
        # Calculer le nombre de chunks nécessaires pour la durée demandée
        chunks_per_ms = self.sample_rate / (self.chunk_size * 1000)
        chunks_needed = int(chunks_per_ms * duration_ms)
        
        # Limiter au nombre de chunks disponibles dans le buffer
        chunks_needed = min(chunks_needed, self.buffer_chunks)
        
        with self.buffer_lock:
            # Récupérer les chunks les plus récents
            start_index = (self.buffer_index - chunks_needed) % self.buffer_chunks
            
            if start_index < self.buffer_index:
                # Les chunks sont contigus dans le buffer
                audio_data = self.audio_buffer[start_index:self.buffer_index]
            else:
                # Les chunks sont séparés par le wrap-around du buffer circulaire
                first_part = self.audio_buffer[start_index:]
                second_part = self.audio_buffer[:self.buffer_index]
                audio_data = np.vstack((first_part, second_part))
        
        # Aplatir les données (convertir en tableau 1D)
        flat_data = audio_data.flatten()
        
        return flat_data if len(flat_data) > 0 else None
    
    def get_buffer_status(self):
        """Obtient l'état du buffer audio
        
        Returns:
            dict: État du buffer audio
        """
        with self.buffer_lock:
            total_samples = self.buffer_chunks * self.chunk_size
            buffer_duration = total_samples / self.sample_rate
            
            status = {
                "is_streaming": self.is_streaming,
                "buffer_size": total_samples,
                "buffer_duration_seconds": buffer_duration,
                "current_index": self.buffer_index,
                "device_index": self.device_index,
                "sample_rate": self.sample_rate
            }
        
        return status
    
    def __del__(self):
        """Destructeur pour libérer les ressources PyAudio"""
        self.stop()
        
        if self.pyaudio:
            self.pyaudio.terminate()

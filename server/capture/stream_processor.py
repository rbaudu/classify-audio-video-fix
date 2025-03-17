# -*- coding: utf-8 -*-
"""
Processeur de flux audio et vidéo
"""

import logging
import numpy as np
from PIL import Image, ImageOps, ImageEnhance

logger = logging.getLogger(__name__)

class StreamProcessor:
    """Traite les flux audio et vidéo pour l'analyse"""
    
    def __init__(self, video_resolution=(640, 480), audio_sample_rate=16000):
        """Initialise le processeur de flux
        
        Args:
            video_resolution (tuple, optional): Résolution vidéo (largeur, hauteur). Par défaut (640, 480).
            audio_sample_rate (int, optional): Taux d'échantillonnage audio. Par défaut 16000.
        """
        self.video_resolution = video_resolution
        self.audio_sample_rate = audio_sample_rate
        
        logger.info(f"Processeur de flux initialisé avec résolution vidéo {video_resolution} et taux d'échantillonnage audio {audio_sample_rate}")
    
    def process_video(self, frame):
        """Traite une image pour l'analyse
        
        Args:
            frame (PIL.Image.Image): Image à traiter
        
        Returns:
            PIL.Image.Image: Image traitée
        """
        if frame is None:
            return None
        
        try:
            # Redimensionner l'image à la résolution souhaitée
            resized_frame = frame.resize(self.video_resolution, Image.LANCZOS)
            
            # Améliorer le contraste pour faciliter l'analyse
            enhanced_frame = ImageEnhance.Contrast(resized_frame).enhance(1.2)
            
            return enhanced_frame
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image: {str(e)}")
            return frame  # Retourner l'image d'origine en cas d'erreur
    
    def process_audio(self, audio_data):
        """Traite des données audio pour l'analyse
        
        Args:
            audio_data (numpy.ndarray): Données audio à traiter
        
        Returns:
            numpy.ndarray: Données audio traitées
        """
        if audio_data is None or len(audio_data) == 0:
            return None
        
        try:
            # Normaliser les données audio entre -1 et 1
            normalized_audio = audio_data / np.max(np.abs(audio_data))
            
            return normalized_audio
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement audio: {str(e)}")
            return audio_data  # Retourner les données d'origine en cas d'erreur
    
    def extract_video_features(self, frame):
        """Extrait des caractéristiques vidéo pour la classification
        
        Args:
            frame (PIL.Image.Image): Image à analyser
        
        Returns:
            dict: Caractéristiques extraites
        """
        if frame is None:
            return {}
        
        try:
            # Convertir en niveaux de gris
            gray_frame = ImageOps.grayscale(frame)
            
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
            
            # Calculer une mesure simple de mouvement (différence entre les régions)
            h, w = frame_array.shape
            left_region = np.mean(frame_array[:, :w//2])
            right_region = np.mean(frame_array[:, w//2:])
            top_region = np.mean(frame_array[:h//2, :])
            bottom_region = np.mean(frame_array[h//2:, :])
            
            # Assembler les caractéristiques
            features = {
                "mean_intensity": float(mean_intensity),
                "std_intensity": float(std_intensity),
                "min_intensity": float(min_intensity),
                "max_intensity": float(max_intensity),
                "histogram": hist.tolist(),
                "region_diffs": {
                    "left_right": float(abs(left_region - right_region)),
                    "top_bottom": float(abs(top_region - bottom_region))
                }
            }
            
            return features
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de caractéristiques vidéo: {str(e)}")
            return {}
    
    def extract_audio_features(self, audio_data):
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
            
            # Calculer des caractéristiques temporelles simples
            # (on pourrait ajouter des caractéristiques fréquentielles avec une FFT)
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

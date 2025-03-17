# -*- coding: utf-8 -*-
"""
Module de capture vidéo via OBS WebSocket
"""

import logging
import time
import base64
import io
from PIL import Image
import threading
import obsws_python as obsws
from obsws_python.error import OBSSDKError

logger = logging.getLogger(__name__)

class OBSCapture:
    """Classe pour capturer des vidéos depuis OBS via WebSocket"""
    
    def __init__(self, host="localhost", port=4455, password=None):
        """Initialise la connexion à OBS WebSocket
        
        Args:
            host (str, optional): Hôte OBS WebSocket. Par défaut "localhost".
            port (int, optional): Port OBS WebSocket. Par défaut 4455.
            password (str, optional): Mot de passe OBS WebSocket. Par défaut None.
        """
        self.host = host
        self.port = port
        self.password = password
        self.client = None
        self.connected = False
        self.video_sources = []
        self.media_sources = []
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.frame_time = 0
        self.is_capturing = False
        self.capture_thread = None
        
        # Se connecter à OBS
        self._connect()
    
    def _connect(self):
        """Se connecte à OBS WebSocket"""
        try:
            logger.info(f"Tentative de connexion à OBS sur {self.host}:{self.port}")
            
            # Initialiser le client OBS WebSocket
            if self.password:
                self.client = obsws.ReqClient(host=self.host, port=self.port, password=self.password)
            else:
                self.client = obsws.ReqClient(host=self.host, port=self.port)
            
            # Vérifier la connexion
            version = self.client.get_version()
            logger.info(f"Connecté à OBS avec succès")
            
            # Récupérer les sources disponibles
            self._get_sources()
            
            self.connected = True
        
        except Exception as e:
            logger.error(f"Erreur de connexion à OBS: {str(e)}")
            self.connected = False
    
    def _get_sources(self):
        """Récupère les sources disponibles dans OBS"""
        if not self.connected or not self.client:
            return
        
        # Essayer d'abord avec GetSourcesList (version plus ancienne d'OBS)
        try:
            logger.info("Tentative de récupération des sources via GetSourcesList()")
            sources_response = self.client.call(obsws.requests.GetSourcesList())
            logger.info(f"Réponse de GetSourcesList(): {sources_response}")
            
            sources = sources_response.get('sources', [])
            
            # Filtrer les sources vidéo et média
            self.video_sources = [source['name'] for source in sources if source.get('typeId') in ['dshow_input', 'v4l2_input']]
            self.media_sources = [source['name'] for source in sources if source.get('typeId') in ['ffmpeg_source', 'vlc_source']]
            
            logger.info(f"Sources vidéo trouvées: {self.video_sources}")
            logger.info(f"Sources média trouvées: {self.media_sources}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sources: {str(e)}")
            
            # Essayer avec GetInputList() pour OBS 28+
            try:
                logger.info("Tentative de récupération des sources via GetInputList() (OBS 28+)")
                inputs_response = self.client.get_input_list()
                logger.info(f"Sources récupérées via GetInputList(): {inputs_response.inputs}")
                
                # Filtrer par type d'entrée pour OBS 28+
                self.video_sources = [input_data['inputName'] for input_data in inputs_response.inputs if input_data.get('inputKind') in ['dshow_input', 'v4l2_input']]
                self.media_sources = [input_data['inputName'] for input_data in inputs_response.inputs if input_data.get('inputKind') in ['ffmpeg_source', 'vlc_source']]
                
                logger.info(f"Sources vidéo trouvées (via GetInputList): {self.video_sources}")
                logger.info(f"Sources média trouvées (via GetInputList): {self.media_sources}")
                
            except Exception as inner_e:
                logger.error(f"Erreur lors de la récupération des sources via GetInputList: {str(inner_e)}")
    
    def capture_frame(self, source_name=None):
        """Capture une image d'une source OBS
        
        Args:
            source_name (str, optional): Nom de la source à capturer. Par défaut None (utilise la première source disponible).
        
        Returns:
            PIL.Image.Image: Image capturée, ou None si échec
        """
        if not self.connected or not self.client:
            logger.error("Impossible de capturer une image: non connecté à OBS")
            return None
        
        # Si aucune source n'est spécifiée, utiliser la première source vidéo
        if not source_name:
            if self.video_sources:
                source_name = self.video_sources[0]
            else:
                logger.error("Aucune source vidéo disponible")
                return None
        
        try:
            # Capture d'écran de la source
            logger.info(f"Tentative avec GetSourceScreenshot pour: {source_name}")
            
            screenshot = self.client.get_source_screenshot(
                source_name=source_name,
                img_format="jpg",
                width=640,
                height=480
            )
            
            # Décodage de l'image base64
            if screenshot and hasattr(screenshot, 'img_data'):
                img_data = screenshot.img_data
                
                # Supprimer le préfixe data:image/jpg;base64, si présent
                if ';base64,' in img_data:
                    img_data = img_data.split(';base64,')[1]
                
                # Décoder l'image base64
                img_bytes = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(img_bytes))
                
                # Mettre à jour l'image courante
                with self.frame_lock:
                    self.current_frame = img
                    self.frame_time = time.time()
                
                return img
            else:
                logger.warning(f"Capture d'écran non réussie pour {source_name}")
                return None
        
        except Exception as e:
            logger.error(f"Erreur lors de la capture d'écran: {str(e)}")
            
            # Essayer une méthode alternative pour OBS 28+
            try:
                screenshot = self.client.get_source_screenshot(
                    source_name=source_name,
                    img_format="jpg",
                    width=640,
                    height=480,
                    compression_quality=75
                )
                
                # Traitement similaire à ci-dessus
                if screenshot and hasattr(screenshot, 'img_data'):
                    img_data = screenshot.img_data
                    
                    # Supprimer le préfixe data:image/jpg;base64, si présent
                    if ';base64,' in img_data:
                        img_data = img_data.split(';base64,')[1]
                    
                    # Décoder l'image base64
                    img_bytes = base64.b64decode(img_data)
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # Mettre à jour l'image courante
                    with self.frame_lock:
                        self.current_frame = img
                        self.frame_time = time.time()
                    
                    return img
            except Exception as inner_e:
                logger.error(f"Erreur alternative lors de la capture d'écran: {str(inner_e)}")
                return None
    
    def start_capture(self, source_name=None, interval=0.1):
        """Démarre la capture continue en arrière-plan
        
        Args:
            source_name (str, optional): Source à capturer. Par défaut None.
            interval (float, optional): Intervalle entre les captures (secondes). Par défaut 0.1.
        """
        if self.is_capturing:
            logger.warning("Capture déjà en cours")
            return
        
        # Si aucune source n'est spécifiée, utiliser la première source vidéo
        if not source_name and self.video_sources:
            source_name = self.video_sources[0]
        
        if not source_name:
            logger.error("Aucune source vidéo disponible pour la capture continue")
            return
        
        self.is_capturing = True
        
        # Démarrer le thread de capture
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(source_name, interval),
            daemon=True
        )
        self.capture_thread.start()
        
        logger.info(f"Capture continue démarrée pour {source_name} avec intervalle {interval}s")
    
    def _capture_loop(self, source_name, interval):
        """Boucle de capture continue
        
        Args:
            source_name (str): Source à capturer.
            interval (float): Intervalle entre les captures (secondes).
        """
        while self.is_capturing:
            self.capture_frame(source_name)
            time.sleep(interval)
    
    def stop_capture(self):
        """Arrête la capture continue"""
        self.is_capturing = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
        
        logger.info("Capture continue arrêtée")
    
    def get_current_frame(self):
        """Récupère l'image capturée la plus récente
        
        Returns:
            tuple: (PIL.Image.Image, float) Image et timestamp, ou (None, 0) si aucune image
        """
        with self.frame_lock:
            return self.current_frame, self.frame_time
    
    def disconnect(self):
        """Déconnecte du serveur OBS WebSocket"""
        self.stop_capture()
        self.connected = False
        self.client = None
        logger.info("Déconnecté d'OBS WebSocket")

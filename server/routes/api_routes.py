# -*- coding: utf-8 -*-
"""
Routes API pour le serveur Flask
"""

import logging
import time
import json
from flask import jsonify, request, Response
import base64
import io

logger = logging.getLogger(__name__)

def register_api_routes(app, db_manager, sync_manager, activity_classifier):
    """Enregistre les routes API pour l'application Flask
    
    Args:
        app (Flask): Application Flask
        db_manager (DBManager): Gestionnaire de base de données
        sync_manager (SyncManager): Gestionnaire de synchronisation
        activity_classifier (ActivityClassifier): Classificateur d'activités
    """
    
    @app.route('/api/current-activity', methods=['GET'])
    def get_current_activity():
        """Récupère l'activité courante
        
        Returns:
            Response: Réponse JSON avec l'activité courante
        """
        try:
            activity = activity_classifier.get_current_activity()
            
            if activity:
                return jsonify(activity)
            else:
                return jsonify({
                    "type": "inactif",
                    "confidence": 1.0,
                    "timestamp": int(time.time()),
                    "duration": 0
                })
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'activité: {str(e)}")
            return jsonify({
                "type": "erreur",
                "message": "Impossible de récupérer l'activité courante"
            })
    
    @app.route('/api/video-status', methods=['GET'])
    def get_video_status():
        """Récupère l'état de la vidéo
        
        Returns:
            Response: Réponse JSON avec l'état de la vidéo
        """
        try:
            status = {
                "active": sync_manager.is_video_available(),
                "sources": sync_manager.obs_capture.video_sources if sync_manager.obs_capture else []
            }
            
            return jsonify(status)
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'état vidéo: {str(e)}")
            return jsonify({
                "active": False,
                "sources": [],
                "error": str(e)
            })
    
    @app.route('/api/video-snapshot', methods=['GET'])
    def get_video_snapshot():
        """Récupère une image instantanée de la vidéo
        
        Returns:
            Response: Image JPEG
        """
        try:
            # Paramètre de qualité optionnel
            quality = request.args.get('quality', default=85, type=int)
            
            # Récupérer l'image JPEG
            jpeg_data = sync_manager.get_frame_as_jpeg(quality=quality)
            
            if jpeg_data:
                return Response(jpeg_data, mimetype='image/jpeg')
            else:
                # Si aucune image n'est disponible, retourner une image vide
                blank_image = io.BytesIO()
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (640, 480), color=(50, 50, 50))
                draw = ImageDraw.Draw(img)
                draw.text((320, 240), "Pas de vidéo disponible", fill=(255, 255, 255))
                img.save(blank_image, format='JPEG')
                blank_image.seek(0)
                
                return Response(blank_image.getvalue(), mimetype='image/jpeg')
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du snapshot vidéo: {str(e)}")
            return Response(status=500)
    
    @app.route('/api/activities', methods=['GET'])
    def get_activities():
        """Récupère les activités enregistrées
        
        Returns:
            Response: Réponse JSON avec les activités
        """
        try:
            # Paramètres de pagination et filtrage
            start = request.args.get('start', default=None, type=int)
            end = request.args.get('end', default=None, type=int)
            limit = request.args.get('limit', default=100, type=int)
            offset = request.args.get('offset', default=0, type=int)
            
            activities = db_manager.get_activities(
                start_time=start,
                end_time=end,
                limit=limit,
                offset=offset
            )
            
            return jsonify({
                "activities": activities,
                "count": len(activities),
                "total": len(activities)  # Ceci devrait idéalement être le nombre total sans pagination
            })
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des activités: {str(e)}")
            return jsonify({
                "activities": [],
                "count": 0,
                "total": 0,
                "error": str(e)
            }), 500
    
    @app.route('/api/statistics', methods=['GET'])
    def get_statistics():
        """Récupère des statistiques sur les activités
        
        Returns:
            Response: Réponse JSON avec les statistiques
        """
        try:
            # Paramètre de période
            period = request.args.get('period', default='day', type=str)
            
            # Vérifier la période valide
            if period not in ['day', 'week', 'month']:
                period = 'day'
            
            stats = db_manager.get_activity_stats(period=period)
            
            return jsonify(stats)
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return jsonify({
                "error": str(e),
                "period": request.args.get('period', 'day')
            }), 500
    
    @app.route('/api/classify', methods=['POST'])
    def manual_classification():
        """Effectue une classification manuelle
        
        Returns:
            Response: Réponse JSON avec le résultat de la classification
        """
        try:
            # Forcer une analyse immédiate
            activity = activity_classifier.analyze_current_activity()
            
            if activity:
                # Enregistrer l'activité dans la base de données
                db_manager.save_activity(
                    activity_type=activity['type'],
                    confidence=activity['confidence'],
                    duration=activity.get('duration', 0),
                    metadata=activity
                )
                
                return jsonify({
                    "success": True,
                    "activity": activity
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Aucune activité détectée"
                })
        
        except Exception as e:
            logger.error(f"Erreur lors de la classification manuelle: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/api/audio-status', methods=['GET'])
    def get_audio_status():
        """Récupère l'état de l'audio
        
        Returns:
            Response: Réponse JSON avec l'état de l'audio
        """
        try:
            status = {
                "active": sync_manager.is_audio_available(),
                "buffer_status": sync_manager.pyaudio_capture.get_buffer_status() if sync_manager.pyaudio_capture else {}
            }
            
            return jsonify(status)
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'état audio: {str(e)}")
            return jsonify({
                "active": False,
                "buffer_status": {},
                "error": str(e)
            })

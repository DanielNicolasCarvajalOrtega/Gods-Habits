from __future__ import annotations
import logging
import re
from typing import Any, Dict
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from google import genai
from google.genai.types import GenerateContentConfig
from apps.IA_Coach.services.ia_router import IARouter, IARouterError
from apps.IA_Coach.serializers import RecommendationsResponseSerializer
from apps.IA_Coach.services.prompt_builder import build_llm_payload, build_prompt_for_moods, has_sufficient_data
import json
from django.conf import settings



User = get_user_model()
logger = logging.getLogger(__name__)


class IARecommendationsService:
    """
    Orquesta: arma payload -> construye prompt -> llama al router -> valida JSON -> retorna dict.
    """
    @staticmethod
    def _ensure_json(obj_or_text: Any) -> Dict[str, Any]:
        """Acepta dict o str. Si viene texto, intenta parsear JSON o extraerlo."""
        if isinstance(obj_or_text, dict):
            return obj_or_text
        text = str(obj_or_text or "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Intento de extracción de primer bloque JSON
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

    @staticmethod
    def get_recommendations(user, days: int = 30) -> Dict[str, Any]:
        payload = build_llm_payload(user, days=days, use_cache=True)
        prompt = build_prompt_for_moods(payload)

        try:
            raw = IARouter.generate_json(prompt, temperature=0.2)
        except IARouterError as exc:
            # Fallback seguro y breve
            logger.warning("IA Router error. Devolviendo fallback. %s", exc)
            raw = {
                "summary": "Resumen no disponible por ahora. Te dejamos acciones simples para hoy.",
                "actions": [
                    {
                        "title": "Pausa de respiración 3 minutos",
                        "description": "Inhala 4s, sostén 2s, exhala 6s durante 3 minutos.",
                        "why_it_helps": "Baja activación fisiológica y reduce estrés percibido.",
                        "duration_minutes": 3,
                        "effort": "low",
                        "priority": "now",
                    },
                    {
                        "title": "Mini caminata",
                        "description": "Camina 10 minutos al aire libre o en casa.",
                        "why_it_helps": "Movimiento breve mejora energía y ánimo.",
                        "duration_minutes": 10,
                        "effort": "low",
                        "priority": "soon",
                    },
                ],
                "alerts": {
                    "require_professional_support": False,
                    "high_stress": False,
                    "poor_sleep": False,
                },
                "next_check_in_days": 3,
            }

        # Validación robusta de salida
        data = IARecommendationsService._ensure_json(raw)
        ser = RecommendationsResponseSerializer(data=data)
        try:
            ser.is_valid(raise_exception=True)
        except ValidationError as exc:
            logger.error("Respuesta IA inválida: %s | data=%s", exc, data)
            # Sanitiza a estructura mínima válida
            data = {
                "summary": data.get("summary", "Revisión pendiente."),
                "actions": [],
                "alerts": {"require_professional_support": False, "high_stress": False, "poor_sleep": False},
                "next_check_in_days": 3,
            }

        return ser.data if ser.is_valid() else data

    def get_recommendations_for_user(user, days: int = 30, temperature: float = 0.1) -> Dict[str, Any]:
        if not getattr(settings, "GEMINI_API_KEY", None):
            raise RuntimeError("Falta GEMINI_API_KEY en settings/.env")

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        payload = build_llm_payload(user, days=days, use_cache=False)
        prompt = build_prompt_for_moods(payload)
        schema = payload["constraints"]["output_schema"]
        cfg = GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema,
        )

        model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=cfg,
            )
        except Exception as e:
            logger.exception("Error llamando a Gemini: %s", e)
            return {
                "payload_used": payload,
                "llm_output": {
                    "summary": "No pudimos generar recomendaciones ahora. Prueba nuevamente en unos minutos.",
                    "actions": [],
                    "alerts": {
                        "require_professional_support": False,
                        "high_stress": False,
                        "poor_sleep": False,
                    },
                    "next_check_in_days": 3,
                },
            }

        def _resp_to_text(r) -> str:
            if getattr(r, "text", None):
                return r.text
            try:
                if getattr(r, "candidates", None):
                    cand = r.candidates[0]
                    for p in getattr(cand.content, "parts", []) or []:
                        if getattr(p, "text", None):
                            return p.text
            except Exception:
                pass
            return ""

        raw_text = _resp_to_text(resp)

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("Gemini no devolvió JSON válido. Texto crudo: %.180s", raw_text)
            data = {}

        # sanea claves mínimas esperadas
        data = {
            "summary": data.get("summary", (raw_text or "Sin resumen por ahora.")[:500]),
            "actions": data.get("actions", []),
            "alerts": data.get("alerts", {
                "require_professional_support": False,
                "high_stress": False,
                "poor_sleep": False,
            }),
            "next_check_in_days": data.get("next_check_in_days", 3),
        }

        return {"payload_used": payload, "llm_output": data}
    
class IACoachService:
    """CONSEJOS PERSONALIZADOS CON GEMINI"""
    @staticmethod
    def generate_personalized_advice(user: User, days: int = 7) -> Dict[str, Any]:
        """
        Genera consejo personalizado para el usuario.
        
        Args:
            user: Usuario autenticado
            days: Días de historial a analizar (7-30)
            
        Returns:
            Dict con success, data/error y metadata
        """
        try:
            #Construir payload con datos del usuario
            logger.info(f"Construyendo payload para {user.username}")
            payload = build_llm_payload(user, days=days, use_cache=True)
            
            #Verificar suficiencia de datos
            if not has_sufficient_data(payload):
                logger.info(f"Datos insuficientes para {user.username}")
                return IACoachService._insufficient_data_response()
            
            #Construir prompt optimizado
            prompt = build_prompt_for_moods(payload)
            
            #Llamar a IA
            logger.info(f"Generando consejo para {user.username}")
            
            ia_response = IARouter.generate_json(
                prompt=prompt,
                system_instruction=IACoachService._get_system_instruction(),
                temperature=0.2,
                top_p=0.8,
                max_output_tokens=500,
            )
            
            #Validar y limpiar respuesta
            ia_response = IACoachService._ensure_json(ia_response)
            
            #Enriquecer con metadata
            ia_response["user_id"] = user.id
            ia_response["username"] = user.username
            ia_response["analysis_period_days"] = days
            ia_response["generated_at"] = timezone.now().isoformat()
            
            logger.info(f"Consejo generado para {user.username}")
            
            return {
                "success": True,
                "data": ia_response
            }
            
        except IARouterError as err:
            logger.error(f"Error IA para {user.username}: {err}")
            return {
                "success": False,
                "error": "No se pudo generar el consejo. Intenta más tarde.",
                "fallback": IACoachService._get_fallback_advice()
            }
            
        except Exception as err:
            logger.exception(f"Error inesperado para {user.username}")
            return {
                "success": False,
                "error": str(err),
                "fallback": IACoachService._get_fallback_advice()
            }

    @staticmethod
    def _ensure_json(obj_or_text: Any) -> Dict[str, Any]:
        """
        Acepta dict o str. Si viene texto, intenta parsear JSON.
        """
        if isinstance(obj_or_text, dict):
            return obj_or_text
        
        text = str(obj_or_text or "").strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Intento de extracción de primer bloque JSON
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            
            logger.error(f"No se pudo parsear JSON: {text[:200]}")
            raise

    @staticmethod
    def _get_system_instruction() -> str:
        """Instrucción del sistema para Gemini"""
        return """
Eres un coach de hábitos CONCISO, empático y basado en datos.

REGLAS ESTRICTAS:
- Respuestas breves y accionables
- EXACTAMENTE 3 acciones por plan
- Sin saludos, despedidas ni relleno
- Vocabulario simple y directo
- Máximo 1 emoji por acción (opcional)
- Summary: máximo 40 palabras
- Cada descripción: máximo 25 palabras
- why_it_helps: máximo 15 palabras

IMPORTANTE:
- SIEMPRE responde SOLO con JSON válido
- NO agregues texto antes o después del JSON
- Cumple el esquema exacto solicitado
"""

    @staticmethod
    def _insufficient_data_response() -> Dict[str, Any]:
        """Respuesta cuando el usuario no tiene datos suficientes"""
        return {
            "success": True,
            "data": {
                "summary": "Aún no tienes suficientes datos. Registra tu estado de ánimo y hábitos durante unos días para recibir consejos personalizados.",
                "actions": [
                    {
                        "title": "Registra tu mood diario",
                        "description": "Toma 2 minutos cada día para registrar tu energía, estrés y horas de sueño.",
                        "why_it_helps": "Permite análisis personalizado de tus patrones.",
                        "duration_minutes": 2,
                        "effort": "low",
                        "priority": "now"
                    },
                    {
                        "title": "Crea tu primer hábito",
                        "description": "Define un hábito simple y realista para comenzar (ej: caminar 10 min).",
                        "why_it_helps": "Genera momentum positivo desde el inicio.",
                        "duration_minutes": 5,
                        "effort": "low",
                        "priority": "now"
                    },
                    {
                        "title": "Completa tu perfil",
                        "description": "Indica tus objetivos, áreas de foco y tiempo disponible.",
                        "why_it_helps": "Consejos más personalizados y relevantes.",
                        "duration_minutes": 3,
                        "effort": "low",
                        "priority": "soon"
                    }
                ],
                "alerts": {
                    "require_professional_support": False,
                    "high_stress": False,
                    "poor_sleep": False
                },
                "next_check_in_days": 3,
                "insufficient_data": True
            }
        }

    @staticmethod
    def _get_fallback_advice() -> Dict[str, Any]:
        """Consejo genérico si falla la IA"""
        return {
            "summary": "Mantén lo básico hoy: duerme bien (7-8h), hidrátate y muévete un poco.",
            "actions": [
                {
                    "title": "Prioriza el sueño",
                    "description": "Acuéstate y despierta a la misma hora cada día.",
                    "why_it_helps": "Mejora energía y salud general.",
                    "duration_minutes": 480,
                    "effort": "medium",
                    "priority": "now"
                },
                {
                    "title": "Muévete 15-30 min",
                    "description": "Camina, estira o haz ejercicio ligero.",
                    "why_it_helps": "Reduce estrés y mejora ánimo.",
                    "duration_minutes": 20,
                    "effort": "low",
                    "priority": "now"
                },
                {
                    "title": "Hidrátate bien",
                    "description": "Bebe 6-8 vasos de agua durante el día.",
                    "why_it_helps": "Esencial para energía y claridad mental.",
                    "duration_minutes": 5,
                    "effort": "low",
                    "priority": "now"
                }
            ],
            "alerts": {
                "require_professional_support": False,
                "high_stress": False,
                "poor_sleep": False
            },
            "next_check_in_days": 7,
            "is_fallback": True
        }
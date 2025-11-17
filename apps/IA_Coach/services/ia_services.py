from __future__ import annotations
import logging
import re
from typing import Any, Dict
from django.core.exceptions import ValidationError
from google import genai
from google.genai.types import GenerateContentConfig
from apps.IA_Coach.services.prompt_builder import build_llm_payload,build_prompt_for_moods
from apps.IA_Coach.services.ia_router import IARouter, IARouterError
from apps.IA_Coach.serializers import RecommendationsResponseSerializer
import json
from django.conf import settings

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
            "summary": data.get("summary", (raw_text or "Sin resumen por ahora.")[:220]),
            "actions": data.get("actions", []),
            "alerts": data.get("alerts", {
                "require_professional_support": False,
                "high_stress": False,
                "poor_sleep": False,
            }),
            "next_check_in_days": data.get("next_check_in_days", 3),
        }

        return {"payload_used": payload, "llm_output": data}
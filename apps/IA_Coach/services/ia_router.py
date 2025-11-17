from __future__ import annotations
import json
import logging
import os
from typing import Any, Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class IARouterError(RuntimeError):
    """Excepción personalizada para errores del router de IA"""
    pass


class IARouter:
    """Adaptador de proveedor IA (Gemini API o Vertex)."""

    @staticmethod
    def _require_model() -> str:
        """Obtener nombre del modelo desde settings"""
        model = getattr(settings, "AI_COACH_MODEL", "gemini-2.5-flash")
        if not model:
            raise IARouterError("AI_COACH_MODEL no configurado en settings.")
        return model

    @staticmethod
    def _provider() -> str:
        """Obtener proveedor de IA desde settings"""
        return getattr(settings, "AI_COACH_PROVIDER", "gemini").lower()

    @staticmethod
    def generate_json(
            prompt: str,
            *,
            system_instruction: Optional[str] = None,
            temperature: float = 0.3,
            top_p: float = 0.9,
            max_output_tokens: int = 800
    ) -> Dict[str, Any]:
        """Genera salida JSON usando el proveedor configurado."""

        provider = IARouter._provider()
        model_name = IARouter._require_model()

        if provider == "gemini":
            return IARouter._generate_gemini(
                prompt=prompt,
                model_name=model_name,
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens
            )
        elif provider == "vertex":
            # Implementación futura de Vertex AI
            raise IARouterError("Proveedor 'vertex' no implementado aún.")
        else:
            raise IARouterError(f"Proveedor IA no soportado: {provider}")

    @staticmethod
    def _generate_gemini(
            prompt: str,
            model_name: str,
            system_instruction: Optional[str],
            temperature: float,
            top_p: float,
            max_output_tokens: int
    ) -> Dict[str, Any]:
        """Implementación específica para Gemini API"""
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise IARouterError(
                f"Falta dependencia 'google-generativeai'. "
                f"Instala con: pip install google-generativeai\n{exc}"
            )

        # Obtener API key
        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise IARouterError(
                "GEMINI_API_KEY no configurada. "
                "Agrégala a .env o settings.py"
            )

        # Configurar Gemini
        genai.configure(api_key=api_key)

        # Instrucción del sistema por defecto
        default_instruction = (
            "Actúas como coach de hábitos especializado. "
            "Genera respuestas en JSON válido. "
            "Cumple con las políticas de seguridad de Google."
        )

        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction or default_instruction,
        )

        try:
            logger.info(f"Llamando a Gemini ({model_name}) con prompt de {len(prompt)} caracteres")

            resp = model.generate_content(
                [prompt],
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    top_p=top_p,
                    max_output_tokens=max_output_tokens,
                    response_mime_type="application/json",
                ),
                safety_settings={
                    genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                },
                request_options={"timeout": 30},
            )

            logger.info(f"Respuesta de Gemini recibida: {len(resp.text)} caracteres")

        except Exception as exc:
            logger.exception("Error llamando a Gemini API")
            raise IARouterError(f"Gemini API falló: {exc}")

        # Parsear respuesta JSON
        try:
            if not resp.text:
                raise IARouterError("Gemini devolvió respuesta vacía")

            return json.loads(resp.text)

        except json.JSONDecodeError as exc:
            error_preview = resp.text[:500] if resp.text else "(vacío)"
            logger.error(f"JSON inválido de Gemini: {error_preview}")
            raise IARouterError(
                f"Gemini no retornó JSON válido: {exc}\n"
                f"Texto recibido (primeros 500 chars): {error_preview}"
            ) from exc

    @staticmethod
    def generate_text(
            prompt: str,
            *,
            system_instruction: Optional[str] = None,
            temperature: float = 0.7,
            max_output_tokens: int = 1000
    ) -> str:
        """
        Genera texto plano (no JSON).
        Útil para respuestas conversacionales.
        """
        provider = IARouter._provider()
        model_name = IARouter._require_model()

        if provider == "gemini":
            try:
                import google.generativeai as genai
            except ImportError as exc:
                raise IARouterError(f"Falta google-generativeai: {exc}")

            api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
            if not api_key:
                raise IARouterError("GEMINI_API_KEY no configurada")

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction or "Actúa como coach de hábitos profesional.",
            )

            try:
                resp = model.generate_content(
                    [prompt],
                    generation_config=genai.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                    request_options={"timeout": 30},
                )
                return resp.text or ""
            except Exception as exc:
                logger.exception("Error generando texto con Gemini")
                raise IARouterError(f"Gemini text generation falló: {exc}")
        else:
            raise IARouterError(f"Proveedor no soportado para generate_text: {provider}")
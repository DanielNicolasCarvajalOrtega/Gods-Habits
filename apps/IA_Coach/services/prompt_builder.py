from __future__ import annotations
from typing import Any,Dict,List
from django.utils import timezone
from django.core.cache import cache
from apps.Users_Mood.services import UserMoodService


def guardrails() -> List[Dict[str, Any]]:
    return [
        {"id": "no_medical_advice",
         "rule": "No entregues consejos médicos, psiquiátricos ni diagnósticos. Si los síntomas requieren atención profesional, indica 'contacta a un profesional'."},
        {"id": "no_self_harm",
         "rule": "No sugieras daño a sí mismo ni a terceros. Rechaza y deriva a ayuda profesional en esos casos."},
        {"id": "no_negativity",
         "rule": "Evita lenguaje pesimista o fatalista. Mantén tono empático, práctico y orientado a la acción."},
        {"id": "privacy", "rule": "No inventes datos personales ni supongas información no presente en el payload."},
        {"id": "brevity",
         "rule": "Sé breve y claro. Entrega 3–5 acciones concretas con pasos aplicables en la vida real."},
        {"id": "evidence_style",
         "rule": "Explica el porqué de cada recomendación en una sola frase ('por qué ayuda')."},
        {"id": "format_json", "rule": "La salida **debe** ser JSON válido exactamente con el esquema solicitado."},
        {"id": "safe_flags",
         "rule": "Si percibes señales de estrés muy alto o sueño crítico, marca flags de alerta sin alarmismo."},
        {"id": "context_es_cl", "rule": "Redacta en español de Chile (es-CL), tono cercano y profesional."},
    ]

def build_llm_payload(user, days:int = 30, use_cache:bool=True)-> Dict[str,Any]:
    key = f"ia_payload:{user.id}:{days}:{timezone.localdate().isoformat()}"
    if use_cache:
        cached = cache.get(key)
        if cached:
            return cached

    payload = {
        "user_id": user.id,
        "period_days": days,
        "stats_7d": UserMoodService.get_mood_stars(user, days=7),
        "stats_30d": UserMoodService.get_mood_stars(user, days=30),
        "streak": UserMoodService.get_streak_info(user),
        "top_stress_triggers": UserMoodService.get_stress_triggers_summary(user, days=min(days, 30)),
        "constraints": {
            "tz": timezone.get_current_timezone_name(),
            "locale": "es-CL",
            "guardrails": guardrails(),
            # Parámetros de salida esperada (contrato con el LLM)
            "output_schema": {
                "type": "object",
                "required": ["summary", "actions", "alerts", "next_check_in_days"],
                "properties": {
                    "summary": {"type": "string"},
                    "actions": {
                        "type": "array",
                        "minItems": 3,
                        "maxItems": 5,
                        "items": {
                            "type": "object",
                            "required": ["title", "description", "why_it_helps", "duration_minutes", "effort",
                                         "priority"],
                            "properties": {
                                "title": {"type": "string", "maxLength": 60},
                                "description": {"type": "string", "maxLength": 220},
                                "why_it_helps": {"type": "string", "maxLength": 180},
                                "duration_minutes": {"type": "integer", "minimum": 5, "maximum": 120},
                                "effort": {"type": "string", "enum": ["low", "medium", "high"]},
                                "priority": {"type": "string", "enum": ["now", "soon", "later"]},
                            },
                        },
                    },
                    "alerts": {
                        "type": "object",
                        "required": ["require_professional_support", "high_stress", "poor_sleep"],
                        "properties": {
                            "require_professional_support": {"type": "boolean"},
                            "high_stress": {"type": "boolean"},
                            "poor_sleep": {"type": "boolean"},
                        },
                    },
                    "next_check_in_days": {"type": "integer", "minimum": 1, "maximum": 14},
                },
            },
        },
    }

    if use_cache:
        cache.set(key, payload, timeout=60 * 30)  # 30 min
    return payload

def build_prompt_for_moods(payload: Dict[str, Any]) -> str:
    """redacta un prompt compacto con instrucciones + datos"""
    rules = "\n".join(f"- {r['rule']}" for r in payload["constraints"]["guardrails"])
    return f"""
Eres un coach de hábitos. Sigue **todas** las reglas:

{rules}

Datos (últimos {payload['period_days']} días):
- Stats 7d: {payload['stats_7d']}
- Stats 30d: {payload['stats_30d']}
- Streak: {payload['streak']}
- Principales desencadenantes de estrés: {payload['top_stress_triggers']}
- Zona horaria: {payload['constraints']['tz']} | Locale: {payload['constraints']['locale']}

Devuelve **exclusivamente** un JSON válido con este esquema:
{payload['constraints']['output_schema']}
    """.strip()
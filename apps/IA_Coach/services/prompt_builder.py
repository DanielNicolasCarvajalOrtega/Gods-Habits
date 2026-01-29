from __future__ import annotations
from typing import Any,Dict,List
from django.utils import timezone
from django.core.cache import cache
from apps.Users_Mood.services import UserMoodService
from apps.Habits.services import HabitService

def guardrails() -> List[Dict[str, Any]]:
    return [
        {"id": "no_medical_advice",
         "rule": "No entregues consejos médicos, psiquiátricos ni diagnósticos. Si los síntomas requieren "
                 "atención profesional, indica 'contacta a un profesional'."},
        {"id": "no_self_harm",
         "rule": "No sugieras daño a sí mismo ni a terceros. Rechaza y deriva a ayuda profesional en esos casos."},
        {"id": "no_negativity",
         "rule": "Evita lenguaje pesimista o fatalista. Mantén tono empático, práctico y orientado a la acción."},
        {"id": "privacy", "rule": "No inventes datos personales ni supongas información no presente en el payload."},
        {"id": "brevity",
         "rule": "Sé breve y claro. Entrega 3-4 acciones concretas con pasos aplicables en la vida real."},
        {"id": "evidence_style",
         "rule": "Explica el porqué de cada recomendación en una sola frase ('por qué ayuda')."},
        {"id": "format_json", "rule": "La salida **debe** ser JSON válido exactamente con el esquema solicitado."},
        {"id": "safe_flags",
         "rule": "Si percibes señales de estrés muy alto o sueño crítico, marca flags de alerta sin alarmismo."},
        {"id": "context_es_cl", "rule": "Redacta en español, con tono cercano y profesional."},
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
        "sleep_analysis": UserMoodService.get_sleep_quality_analysis(user,days=min(days,20)),
        "habits_stats": HabitService.get_user_statistics(user),
        "habits_today": HabitService.get_habit_for_today(user),
        "profile": get_user_profile(user),
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
                        "maxItems": 4,
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

def get_user_profile(user) ->Dict[str,Any]:
    """ extrae el perfil del usuario si existe"""
    if not hasattr(user,"profile"):
        return None
    profile = user.profile
    return {
        "user_type":profile.user_type,
        "focus_area":profile.first_focus_area,
        "second_focus_area":profile.secondary_focus_area,
        "time_availability":profile.daily_time_availability,
        "motivation_level":profile.motivation_level,
        "objective":profile.user_objective[:200] if profile.user_objective else "",
        "experience_level":profile.experience_level_user,
    }


def build_prompt_for_moods(payload: Dict[str, Any]) -> str:
    """prompt optimizado para Gemini"""
    
    # Extraer datos clave
    stats_7d = payload["stats_7d"]
    trends = payload.get("trends", {})
    streak = payload["streak"]
    triggers = payload["top_stress_triggers"]
    habit_stats = payload["habits_stats"]
    habits_today = payload["habits_today"]
    profile = payload.get("profile")
    
    # Top stress triggers
    triggers_str = ", ".join([t.get("stress_trigger", "") for t in triggers[:3] if t.get("stress_trigger")])
    if not triggers_str:
        triggers_str = "ninguno registrado"
    
    # Construir prompt
    rules = "\n".join(f"- {r['rule']}" for r in payload["constraints"]["guardrails"])
    
    prompt = f"""
Eres un coach de hábitos basado en datos. Sigue TODAS estas reglas:

{rules}

📊 DATOS DEL USUARIO (últimos {payload['period_days']} días):

ESTADO DE ÁNIMO:
- Energía promedio: {stats_7d.get('avg_energy', 0)}/10
- Estrés promedio: {stats_7d.get('avg_stress', 0)}/10
- Sueño promedio: {stats_7d.get('avg_sleep', 0)} horas
- Tendencia energía: {trends.get('energy_trend', 'stable')}
- Tendencia estrés: {trends.get('stress_trend', 'stable')}
- Racha registro: {streak.get('current_streak', 0)} días consecutivos
- Principales stressors: {triggers_str}

HÁBITOS:
- Activos: {habit_stats.get('total_active', 0)}
- Inactivos: {habit_stats.get('total_inactive', 0)}
- Completitud 7 días: {habit_stats.get('completion_rate_7days', 0)}%
- Pendientes hoy: {len(habits_today)}
"""

    if profile:
        prompt += f"""
PERFIL:
- Tipo usuario: {profile['user_type']}
- Area foco: {profile['focus_area']}
- 2da Area foco: {profile['second_focus_area']}
- Tiempo disponible: {profile['time_availability']}
- Motivación: {profile['motivation_level']}/20
- Objetivo: {profile['objective']}
- Experiencia en area de foco: {profile['experience_level']}
"""

    prompt += f"""
IMPORTANTE:
- Summary: máximo 40 palabras (2 oraciones)
- Actions: EXACTAMENTE 3 acciones
- Cada descripción: máximo 25 palabras
- why_it_helps: máximo 15 palabras

Devuelve SOLO JSON válido con este esquema exacto:
{payload['constraints']['output_schema']}

NO agregues texto antes o después del JSON.
"""
    
    return prompt.strip()


def has_sufficient_data(payload: Dict[str, Any]) -> bool:
    """Verifica si hay datos suficientes para generar consejo"""
    mood_count = payload["stats_7d"].get("count", 0)
    habit_count = payload["habits_stats"].get("total_active", 0)
    
    # Al menos 3 registros de mood O al menos 1 hábito activo
    return mood_count >= 3 or habit_count >= 1
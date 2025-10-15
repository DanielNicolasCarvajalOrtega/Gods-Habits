# apps/IA_Coach/services/ia_services.py

import os
from typing import Optional

from dotenv import load_dotenv
from google import genai


def _get_client() -> "genai.Client":
    """Inicializa el cliente de la API con la API_KEY del .env."""
    load_dotenv()
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("API_KEY no configurada. Agrega API_KEY al .env")
    return genai.Client(api_key=api_key)


def _build_prompt(profile) -> str:
    """
    Construye el prompt en base al perfil del usuario.
    Usa los nombres de campo de tu ModelUser (ya existen en la migración).
    """
    # Si tus campos son choices, puedes usar get_<field>_display() para su etiqueta humana.
    focus = getattr(profile, "first_focus_area", None)
    try:
        # Si el campo es choices
        focus_display = profile.get_first_focus_area_display()
    except Exception:
        focus_display = focus

    obj = getattr(profile, "user_objective", "")
    motivation = getattr(profile, "motivation_level", None)
    experience = getattr(profile, "experience_level_user", None)

    parts = [
        f"Mi foco principal es: {focus_display}",
        f"Mi objetivo es: {obj}",
    ]
    if motivation is not None:
        parts.append(f"Nivel de motivación (1-20): {motivation}")
    if experience is not None:
        parts.append(f"Nivel de experiencia (1-20): {experience}")

    return " | ".join(parts)


def generate_coach_message(user_id: int) -> str:
    """
    Genera un mensaje de coaching. Si el ModelUser (perfil) NO existe,
    usa un prompt mínimo con datos del auth_user para poder probar de inmediato.
    """
    from django.contrib.auth import get_user_model
    from apps.Users.models import ModelUser

    User = get_user_model()

    # 1) Trae el usuario base (auth_user)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError(f"No existe User con id={user_id}")

    # 2) Intenta traer el perfil; si no existe, arma prompt mínimo
    try:
        profile = ModelUser.objects.select_related("user").get(user=user)
        prompt = _build_prompt(profile)  # tu función existente
    except ModelUser.DoesNotExist:
        # Fallback mínimo para poder PROBAR YA MISMO
        prompt = f"Usuario: {getattr(user, 'username', user_id)} | Objetivo: {getattr(user, 'user_objectives',ModelUser.user_objective)} | Foco: {getattr(user,'first_focus_area',ModelUser.first_focus_area)} | Motivación: {getattr(user,'motivation_level',ModelUser.motivation_level)}"

    # 3) Llamada al modelo
    client = _get_client()
    resp = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
    )

    text = None
    for attr in ("text", "output_text"):
        if hasattr(resp, attr):
            text = getattr(resp, attr)
            if text:
                break

    if not text:
        try:
            text = "".join(
                (getattr(part, "text", "") or "")
                for part in resp.candidates[0].content.parts
            ).strip()
        except Exception:
            text = str(resp)

    return text or ""



if __name__ == "__main__":
    # Permite correr este archivo como script suelto:
    #   $ python apps/IA_Coach/services/ia_services.py
    import sys
    from pathlib import Path
    import django

    # Asegura que el root del proyecto esté en sys.path
    ROOT = Path(__file__).resolve().parents[3]  # .../Habits-core
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    # Configura Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
    django.setup()

    # Cambia el id según tu usuario de prueba
    USER_ID = int(os.getenv("TEST_USER_ID", "1"))
    print(generate_coach_message(USER_ID))

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.IA_Coach.services.prompt_builder import *
from apps.Users_Mood.models import UserMood
from apps.Users.models import ModelUser
from apps.Habits.models import Habits
from django.utils import timezone
from datetime import timedelta,time
from decimal import Decimal

User = get_user_model()

@pytest.mark.django_db
class TestGuardrails:
    """Reglas de seguridad del test"""

    def test_guardrails_return_list(self):
        
        rules = guardrails()
        assert isinstance(rules,list)
        assert len(rules) > 0

    def test_guardrails_structure(self):
        rules = guardrails()

        for rule in rules:
            assert "id" in rule
            assert "rule" in rule
            assert isinstance(rule["id"], str)
            assert isinstance(rule["rule"],str)
            assert len(rule["rule"]) > 10

    def test_guardriails_has_critical_rule(self):
        """
        Docstring para test_guardriails_has_critical_rule
        reglas criticas de seguridad
        :param self: Descripción
        """
        rules = guardrails()
        rule_ids = [r["id"] for r in rules]

        assert "no_medical_advice" in rule_ids
        assert "no_self_harm" in rule_ids
        assert "privacy" in rule_ids
        assert "format_json" in rule_ids

@pytest.mark.django_db
class TestBuildLLMPayload:
    """ construccion de payload"""

    def test_build_payload_basic(self,test_user_factory):
        user = test_user_factory()
        payload = build_llm_payload(user,days=8, use_cache= False)

        assert payload["user_id"] == user.id
        assert payload["period_days"] == 8
        assert "stats_7d" in payload
        assert "stats_30d" in payload
        assert "streak" in payload
        assert "habits_stats" in payload
        assert "habits_today" in payload
        assert "constraints" in payload

    def test_build_payload_with_mood_data(self,test_user_factory):
    
        user = test_user_factory()
        today = timezone.now().date()

        #crea moods
        for i in range(5):
            UserMood.objects.create(
                user=user,
                date=today - timedelta(days=i),
                energy_level = 7,
                stress_level=4,
                mood_notes="ha sido una mañana cansadora",
                sleep_hours=Decimal("70.2"),
                stress_trigger = "Finance",
            )
        payload = build_llm_payload(user, days=7, use_cache=False)

        assert payload["stats_7d"]["count"] == 5
        assert payload["stats_7d"]["avg_energy"] > 0
        assert payload["streak"]["current_streak"] >= 5

    def test_build_payload_with_habits(self,test_user_factory):
        user = test_user_factory()
    # RECORDAR HACER LA LOGICA DE SLEEP 
        for i in range(3):
            Habits.objects.create(
                user=user,
                title=f"Habito creado {i}",
                description=f"Descripcion N°{i}",
                frequency="Daily",
                priority="High",
                target_minutes=Decimal('323.51'),
            )
        payload = build_llm_payload(user,days=7, use_cache=False)
        
        #assert user.title in i
        assert payload["habits_stats"]["total_active"] == 3


    def test_build_payload_with_profile(self,test_user_factory):
        user = test_user_factory()

        ModelUser.objects.create(
                user=user,
                user_type="Advanced",
                first_focus_area="Social",
                secondary_focus_area="Health",
                daily_time_availability= "high",
                preferred_morning_time = time(2,2),
                preferred_evening_time=time(4,2),
                motivation_level= 6,
                user_objective= "pulir mis habilidades blandas",
                experience_level_user= 5,
            )
        payload = build_llm_payload(user,days=3,use_cache=False)
        
        assert payload["profile"] is not None
        assert payload["profile"]["user_type"] == "Advanced"
        assert payload["profile"]["focus_area"] == "Social"

    def test_build_payload_whitout_profile(self,test_user_factory):
        user = test_user_factory()
        payload = build_llm_payload(user,days=7,use_cache=False)
        assert payload["profile"] is None

    def test_build_payload_coaching(self,test_user_factory):
        user = test_user_factory()

        cache.clear()

        payload_1 = build_llm_payload(user,days=14,use_cache=True)
        payload_2 = build_llm_payload(user,days=14,use_cache=True)

        assert payload_1["user_id"] == payload_2["user_id"]
        assert payload_1["period_days"] == payload_2["period_days"]

    def test_build_payload_output_schema(self,test_user_factory):
        """Payload debe incluir esquema de salida"""
        user = test_user_factory()
        
        payload = build_llm_payload(user, days=7, use_cache=False)
        
        schema = payload["constraints"]["output_schema"]
        
        assert schema["type"] == "object"
        assert "summary" in schema["properties"]
        assert "actions" in schema["properties"]
        assert "alerts" in schema["properties"]
        assert "next_check_in_days" in schema["properties"]


class TestBuildPromptForMoods:
    """ test para la construccion de moods"""

    def test_build_prompt_basic(self,test_user_factory):
        """Construir prompt básico"""
        user = test_user_factory()
        payload = build_llm_payload(user, days=7, use_cache=False)
        
        prompt = build_prompt_for_moods(payload)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "coach de hábitos" in prompt.lower()
        assert "JSON" in prompt

    def test_build_prompt_include_guardrails(self,test_user_factory):
        """Prompt debe incluir reglas de seguridad"""
        user = test_user_factory()
        payload = build_llm_payload(user, days=7, use_cache=False)
        
        prompt = build_prompt_for_moods(payload)
        
        assert "médicos" in prompt or "consejos" in prompt
        assert "JSON" in prompt
        assert "reglas" in prompt.lower() or "sigue" in prompt.lower()

    
    def test_build_prompt_includes_user_data(self, test_user_factory):
        """Prompt debe incluir datos del usuario"""
        user = test_user_factory()
        today = timezone.now().date()
        
        # Crear datos
        UserMood.objects.create(
            user=user,
            date=today,
            energy_level=8,
            stress_level=3,
            sleep_hours=Decimal('7.5')
        )
        
        payload = build_llm_payload(user, days=7, use_cache=False)
        prompt = build_prompt_for_moods(payload)
        
        assert "Energía promedio" in prompt
        assert "Estrés promedio" in prompt
        assert "Sueño promedio" in prompt

    def test_build_prompt_with_stress_triggers(self, test_user_factory):
        """Prompt debe incluir stress triggers si existen"""
        user = test_user_factory()
        today = timezone.now().date()
        
        # Crear mood con stress trigger
        UserMood.objects.create(
            user=user,
            date=today,
            energy_level=6,
            stress_level=7,
            sleep_hours=Decimal('6.0'),
            stress_trigger="Work"
        )
        
        payload = build_llm_payload(user, days=7, use_cache=False)
        prompt = build_prompt_for_moods(payload)
        
        assert "stressors" in prompt.lower() or "estrés" in prompt.lower()

    def test_build_prompt_with_profile(self,test_user_factory):
        user = test_user_factory()

        ModelUser.objects.create(
            user=user,
            user_type="Student",
            first_focus_area="Creativity",
            secondary_focus_area="Learning",
            daily_time_availability="flexible",
            preferred_morning_time=time(2,30),
            preferred_evening_time=time(5,3),
            motivation_level=4,
            user_objective="son 2 horas para creatividad y 5 para aprender POO",
            experience_level_user=5,
        )

        payload = build_llm_payload(user,days=30,use_cache=False)
        prompt= build_prompt_for_moods(payload)

        assert "PERFIL" in prompt
        assert "Student" in prompt
        assert "Creativity" in prompt
        assert "flexible" in prompt
        assert "Learning" in prompt

        assert 1 <=  payload["profile"]["motivation_level"] <= 20
        assert payload["profile"]["motivation_level"] == 4
        assert 1 <= payload["profile"]["experience_level"] <= 20
        assert payload["profile"]["experience_level"] == 5

    
    def test_motivation_level_validation(self,test_user_factory):
        from django.core.exceptions import ValidationError

        user = test_user_factory()

        with pytest.raises(ValidationError):
            profile = ModelUser(
                user=user,
                user_type="Student",
                first_focus_area="Creativity",
                secondary_focus_area="Learning",
                daily_time_availability="flexible",
                preferred_morning_time=time(2,30),
                preferred_evening_time=time(5,3),
                motivation_level=22,
                user_objective="son 2 horas para creatividad y 5 para aprender POO",
                experience_level_user=30,
            )
            profile.full_clean()


        with pytest.raises(ValidationError):
            profile = ModelUser(
                user=user,
                user_type="Student",
                first_focus_area="Creativity",
                secondary_focus_area="Learning",
                daily_time_availability="flexible",
                preferred_morning_time=time(2,30),
                preferred_evening_time=time(5,3),
                motivation_level=0,
                user_objective="son 2 horas para creatividad y 5 para aprender POO",
                experience_level_user=1,
            )
            profile.full_clean()

    
@pytest.mark.django_db
class TestHasSufficentData:

    def test_sufficent_with_moods(self,test_user_factory):
        """ crea 3 moods suficientes """
        user = test_user_factory()
        today = timezone.now().date()

        for i in range(3):
            UserMood.objects.create(
                user=user,
                date= today - timedelta(days=i),
                energy_level = 8,
                stress_level = 6,
                mood_notes = "prueba basica ejej",
                sleep_hours=Decimal(7.20),
                stress_trigger="Work",   
            )

        payload = build_llm_payload(user,days=7 , use_cache=False)

        assert has_sufficient_data(payload) is True

    def test_sufficient_with_habits(self,test_user_factory):
        """  1+ habito suficiente """
        user = test_user_factory()
        
        Habits.objects.create(
            user=user,
            title="somos una prueba",
            description= "esta es una prueba para la cracion de data suficiente",
            frequency="Daily",
            priority="Medium",
            target_minutes = Decimal('120.22'),
        )
        payload = build_llm_payload(user,days=7,use_cache=False)
        assert has_sufficient_data(payload) is True
        assert has_sufficient_data(payload) >= 1

    def test_insufficient_data(self,test_user_factory):
        """ si no contiene datos debe ser insuficiente"""
        user = test_user_factory()

        payload = build_llm_payload(user,days=7, use_cache=False)
        assert has_sufficient_data(payload) is False
    

    def test_sufficient_with_mixed_data(self,test_user_factory):
        """ conbinacion de datos"""
        user = test_user_factory()
        today = timezone.now().date()

        #2 moods = suficientes + 1 habito (suficiente juntos)
        for i in range(2):
            UserMood.objects.create(
                user=user,
                date=today - timedelta(days=i),
                energy_level=7,
                stress_level=4,
                mood_notes = f"crecion{i}",
                sleep_hours = Decimal(8.0),
                stress_trigger= "Social",
            )
        
        Habits.objects.create(
            user=user,
            title="Test",
            frequency="Daily",
            priority="High",
            target_minutes=30,
            is_active=True,
        )
        
        payload = build_llm_payload(user, days=7, use_cache=False)
        
        assert has_sufficient_data(payload) is True
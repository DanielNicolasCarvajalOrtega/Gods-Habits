import pytest
import json
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from apps.IA_Coach.services.ia_services import IACoachService
from apps.IA_Coach.services.ia_router import IARouterError
from apps.Users_Mood.models import UserMood
from apps.Habits.models import Habits
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

User = get_user_model()

@pytest.mark.django_db
class TestIACoachServiceBasic:

    def test_sevice_basic(self):
        assert hasattr(IACoachService, "generate_personalized_advice")

    def test_insufficient_data_response(self, test_user_factory):
        user = test_user_factory()
        result = IACoachService.generate_personalized_advice(user,days=7)

        assert result["success"] is True
        assert result["data"]["insufficient_data"] is True
        assert "suficientes datos" in result["data"]["summary"]
        assert len(result["data"]["actions"]) == 3


@pytest.mark.django_db
class TestIACoachServiceWithMockIA:
    # mock esta configurado en la ruta -> tests/conftest.py
    def test_successful_advice_generation(self,mock_generate,test_user_factory, test_model_user_factory):
        """ generar consejo de forma exitosa """

        user = test_user_factory()
        test_model_user_factory(user)
        today = timezone.now().date()

        for datos in range(5):
            UserMood.objects.create(
                user= user,
                date= today - timedelta(days=datos),
                energy_level=10,
                stress_level =4,
                mood_notes= "tengo problemas para generar ganancias " \
                "y ordenarlas.",
                sleep_hours= Decimal('7.30'),
                stress_trigger= "Finance",                
            )
        
        mock_generate.return_value = {
            "summary": "Tu energía está moderada.",
            "actions": [
                {"title": "Dormir mejor", "description": "Acuéstate temprano.", 
                 "why_it_helps": "Mejora energía.", "duration_minutes": 480, 
                 "effort": "medium", "priority": "now"},
                {"title": "Ejercicio", "description": "Camina 20 min.", 
                 "why_it_helps": "Reduce estrés.", "duration_minutes": 20, 
                 "effort": "low", "priority": "now"},
                {"title": "Meditar", "description": "5 min de respiración.", 
                 "why_it_helps": "Calma la mente.", "duration_minutes": 5, 
                 "effort": "low", "priority": "soon"}
            ],
            "alerts": {"require_professional_support": False, 
                      "high_stress": False, "poor_sleep": False},
            "next_check_in_days": 7
        }

        # Desabilitar cache para el test
        from django.core.cache import cache
        cache.clear()
        
        result = IACoachService.generate_personalized_advice(user,days=7)
        

        assert result["success"] is True    
        assert "data" in result

        data = result["data"]

        assert data["user_id"] == user.id
        assert data["username"] == user.username
        assert "analysis_period_days" in data
        assert "generated_at" in data

        # datos del mock
        assert data["summary"] == "Tu energía está moderada."    
        assert len(data["actions"]) == 3
        assert data["next_check_in_days"] == 7   
        mock_generate.assert_called_once()


    def test_ia_router_error_returns_fallback(self,mock_generate,test_user_factory, test_model_user_factory):
        """ Error del modelo devuelve fallback"""
        user = test_user_factory()
        test_model_user_factory(user)
        today = timezone.now().date()

        # Configurar el mock ANTES de crear datos
        mock_generate.side_effect = IARouterError("API Error")

        for i in range(5):
            UserMood.objects.create(
                user=user,
                date= today - timedelta(days=i),
                energy_level=5,
                stress_level =6,
                mood_notes= "tengo problemas para generar ganancias " \
                "y ordenarlas.",
                sleep_hours= Decimal('4.40'),
                stress_trigger= "Finance",  
            )

        # Desabilitar cache para el test
        from django.core.cache import cache
        cache.clear()

        result = IACoachService.generate_personalized_advice(user,days=7)

        assert result["success"] is False
        assert result["fallback"]["is_fallback"] is True
        assert "error" in result
        assert "fallback" in result

    def test_metadata_enrichment(self,mock_generate, test_user_factory, test_model_user_factory):
        """ Respuesta incluye metadata enriquecida """

        user = test_user_factory()
        test_model_user_factory(user)
        today = timezone.now().date()   

        for i in range(5):
            UserMood.objects.create(
                user=user,
                date= today - timedelta(days=i),
                energy_level=5,
                stress_level =6,
                mood_notes= "tengo problemas para generar ganancias " \
                "y ordenarlas.",
                sleep_hours= Decimal('4.40'),
                stress_trigger= "Finance",  
            )
        
        mock_generate.return_value = {
            "summary": "Test",
            "actions": [
                {"title": "A1", "description": "D1", "why_it_helps": "W1", 
                 "duration_minutes": 10, "effort": "low", "priority": "now"},
                {"title": "A2", "description": "D2", "why_it_helps": "W2", 
                 "duration_minutes": 20, "effort": "low", "priority": "now"},
                {"title": "A3", "description": "D3", "why_it_helps": "W3", 
                 "duration_minutes": 30, "effort": "low", "priority": "now"},
            ],
            "alerts": {"require_professional_support": False, "high_stress": False, "poor_sleep": False},
            "next_check_in_days": 7
        }
        
        # Desabilitar cache para el test
        from django.core.cache import cache
        cache.clear()
        
        result = IACoachService.generate_personalized_advice(user, days=7)
        
        data = result["data"]
        
        assert "user_id" in data
        assert "username" in data
        assert "analysis_period_days" in data
        assert "generated_at" in data
        assert data["user_id"] == user.id
        assert data["username"] == user.username
        assert data["analysis_period_days"] == 7


@pytest.mark.django_db
class TestIACoachServiceEnsureJSON:
    """ Test para _ensure_json """

    def test_ensure_json_with_dict(self):
        data = {"key":"value"}
        result = IACoachService._ensure_json(data)

        assert result == data

    def test_ensure_json_with_valid_json_string(self):
        """ json apto para parseo"""

        json_str = '{"summary":"test","actions": []}'

        result = IACoachService._ensure_json(json_str)

        assert isinstance(result,dict)
        assert result["summary"] == "test"

    
    def test_enssure_json_extracts_embedded_json(self):
        """extraemos json embebido en texto """
        text = 'Resultado: {"summary": "test", "actions": []} y más texto'
        result = IACoachService._ensure_json(text)
        
        assert isinstance(result,dict)
        assert "summary" in result

    def test_ensure_json_raises_on_invalid(self):
        """String invalido lanza error"""
        invalid_text = "no es un JSON en absoluto"

        with pytest.raises(json.JSONDecodeError):
            IACoachService._ensure_json(invalid_text)


@pytest.mark.django_db
class TestIACoachServiceFallbacks:
    """ testeo respuestas de fallback"""

    def test_insufficient_data_response_structure(self):
        """ respuesta de datos insuficientes"""
        response = IACoachService._insufficient_data_response()

        assert response["success"] is True
        assert "data" in response
        assert "summary" in response["data"]
        assert "actions" in response["data"]
        assert len(response["data"]["actions"]) == 3
        assert response["data"]["insufficient_data"] is True

    def test_fallback_advice_structure(self):
        """ fallback con estructura correcta"""

        fallback = IACoachService._get_fallback_advice()

        assert "summary" in fallback
        assert "actions" in fallback
        assert len(fallback["actions"]) == 3
        assert fallback["is_fallback"] is True

        for action in fallback["actions"]:
            assert "title" in action
            assert "description" in action
            assert "why_it_helps" in action
            assert "duration_minutes" in action
            assert "effort" in action
            assert "priority" in action
    
    def test_system_instruction_format(self):
        instruction = IACoachService._get_system_instruction()

        assert isinstance(instruction,str)
        assert len(instruction) > 50
        assert "coach" in instruction.lower()
        assert "JSON" in instruction

    


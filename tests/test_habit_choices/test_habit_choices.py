import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.Habits.models import Habits
User = get_user_model()


@pytest.mark.django_db
class TestHabitChoicesValidation:

    def test_valid_frequency_choices(self,authenticated_client):
        response = authenticated_client.post('/api/habits/',{
            "title": "Correr",
            "description": "Ejercicio Diario test",
            "frequency": "Daily",
            "priority": "Medium",
            "target_minutes": 100,
        }, format = "json")

        assert response.status_code == 201, f"Daily debe ser aceptado {response.data}"

        response = authenticated_client.post('/api/habits/', {
            "title" :"Leer test",
            "description": "Actividad de leer en horarios continuos cada 2 horas",
            "frequency": "Weekly",
            "priority": "High",
            "target_minutes": 100,
        }, format = "json")

        assert response.status_code == 201, f"Weekly debe ser aceptado {response.data}"

    def test_invalid_frequency_rejected_choices(self,authenticated_client):
        invalid_frequencies = [ # VALORES INVALIDOS DEBEN SER RECHAZADOS
            "Monthly",
            "Yearly",
            "daily",
            "DAILY",
            "Biweekly",
            "Once",
            "Random",
            ""
        ]

        for invalid in invalid_frequencies:
            response = authenticated_client.post('/api/habits/', {
                "title": "INVALID TESTED",
                "description": "datos de prueba para el testeo de choices, debe volver 400",
                "frequency": invalid,
                "priority": "High",
                "target_minutes": 100,
            }, format="json")

            assert response.status_code == 400, \
                f"Frequency {invalid} deberia ser rechazada"
            assert "frequency" in str(response.data).lower(), \
                f"Error, debe seleccionar 'frequency' para valor '{invalid}' "

    def test_valid_priority_choices(self,authenticated_client):
        validate_priority_choices = ["High","Medium","Low"] # SOLO ACEPTA ESTOS CHOICES

        for priory in validate_priority_choices:
            response = authenticated_client.post('/api/habits/', {
                "title": f"TESTING SERIO PRIORITY CHOICEs{priory[0]}",
                "description": "COMENZAMOS CON ELECCIONES DE PRIORIDADES",
                "frequency": "Daily",
                "priority": priory,
                "target_minutes": 40,
            }, format="json")

            assert response.status_code == 201, \
                f" Priority '{priory}' debe ser aceptada: {response.data}"
            assert response.data["priority"] == priory

    def test_invalid_priority_rejected_choices(self,authenticated_client):
        invalid_priorities = [
            "Urgent",
            "Critical",
            "high",  # minúsculas
            "HIGH",  # mayúsculas
            "Normal",
            "1",
            ""
        ]

        for invalid in invalid_priorities:
            response = authenticated_client.post('/api/habits/', {
                "title": "TESTEO DE PRIORIDADES RECHAZADAS",
                "description": "Deben funcionar de forma correcta el cual devuelvan un 400",
                "frequency": "Daily",
                "priority": invalid,
                "target_minutes": 45,
            }, format="json")

            assert response.status_code == 400, \
                f" 'Priority' {invalid_priorities} debe ser rechazada"

            assert "priority" in str(response.data).lower(), \
                f"Error se debe seleccionar 'priority' para el valor {invalid_priorities}"

    def test_missing_frequency_rejected(self, authenticated_client):
        """Frequency es requerido"""
        response = authenticated_client.post("/api/habits/", {
            "title": "Test Habit",
            "description" : "UNA DESCRIPCION BASICA",
            # frequency FALTANTE
            "priority": "High",
            "target_minutes": 30
        }, format="json")

        assert response.status_code == 400
        assert 'frequency' in str(response.data).lower()

    def test_missing_priority_rejected(self, authenticated_client):
        """Priority es requerido"""
        response = authenticated_client.post("/api/habits/", {
            "title": "Test Habit",
            "description": "UNA DESCRIPCION TESTEABLE",
            "frequency": "Daily",
            # priority FALTANTE
            "target_minutes": 30
        }, format="json")

        assert response.status_code == 400
        assert 'priority' in str(response.data).lower()


    def test_get_display_methods(self, authenticated_client):
        """Verificar que get_frequency_display() y get_priority_display() funcionan"""

        response = authenticated_client.post("/api/habits/", {
            "title": "Test Habit",
            "description": "UNA DESCRIPCION PARA QUE TENGA UNA IDEA DE QUE TRATA TESTEO",
            "frequency": "Daily",
            "priority": "High",
            "target_minutes": 30
        }, format="json")

        assert response.status_code == 201
        habit_id = response.data['id']
        # Obtener el hábito desde el modelo
        habit = Habits.objects.get(id=habit_id)

        # Verificar métodos get_*_display()
        assert habit.get_frequency_display() == "Diario"
        assert habit.get_priority_display() == "Alta"

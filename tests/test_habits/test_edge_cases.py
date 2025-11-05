import pytest
from django.utils import timezone
from datetime import timedelta
from apps.Habits.models import Habit_execution


@pytest.mark.django_db
class TestEdgeCases:

    def test_create_habit_with_very_long_title(self,authenticated_client):
        """ EL TITULO SI ES MUY LARGO DEBE FALLAR """

        long_title = "A" * 280

        response = authenticated_client.post('/api/habits/', {
            'title': long_title,
            'description': "ESTA ES UNA PRUEBA DE TITULO LARGO",
            'frequency': "Weekly",
            'priority': 'Low',
            'target_minutes': 30

        },format = "json")

        assert response.status_code == 400, \
            f"Esperaba 400 pero obtuvo {response.status_code}: {response.data}"
        error_data = str(response.data).lower()
        assert 'title' in error_data, f"Error deberia mencionar 'title' {response.data}"

    def test_create_habit_with_zero_target_minutes(self,authenticated_client):
        response = authenticated_client.post('/api/habits/', {
            'title': "PRUEBAS PRUEBAS",
            'description': "ESTA ES UNA PRUEBA DE TITULO LARGO",
            'frequency': "Weekly",
            'priority': 'Low',
            'target_minutes': 0
        },format = "json")

        assert response.status_code == 400

    def test_mark_complete_with_extreme_duration(self,authenticated_client, habit_factory):
        """ duration_minutes EXTREMO --- MAS DE 24 HRS"""
        user= authenticated_client.handler._force_user
        habit = habit_factory(user=user)

        response = authenticated_client.post(
            f"/api/habits/{habit.id}/mark_habit_user_complete/",
                {
                'duration_minutes': 1600
                },format="json"
            )
        assert response.status_code in (200,201,400)

    def test_timezone_consistency(self, authenticated_client, habit_factory):
        """Verificar que timezone es consistente"""
        user = authenticated_client.handler._force_user
        habit = habit_factory(user=user, frequency="Daily")

        # Marcar completo
        response = authenticated_client.post(
            f"/api/habits/{habit.id}/mark_habit_user_complete/",
            {"duration_minutes": 30},
            format="json"
        )

        execution_date = response.json()['execution']['execution_date']
        today = timezone.now().date().isoformat()

        assert execution_date == today

    def test_habit_with_special_characters_in_title(self, authenticated_client):
        """Título con caracteres especiales"""
        response = authenticated_client.post("/api/habits/", {
            "title": "Leer 📚 30min",
            "frequency": "Daily",
            "priority": "High",
            "target_minutes": 30
        }, format="json")

        assert response.status_code == 201
        assert "📚" in response.json()['title']

    def test_concurrent_mark_complete(self, authenticated_client, habit_factory):
        """Simular marcado concurrente (race condition)"""
        user = authenticated_client.handler._force_user
        habit = habit_factory(user=user)

        # Dos requests simultáneos (en tests secuenciales)
        response1 = authenticated_client.post(
            f"/api/habits/{habit.id}/mark_habit_user_complete/",
            {"duration_minutes": 20},
            format="json"
        )

        response2 = authenticated_client.post(
            f"/api/habits/{habit.id}/mark_habit_user_complete/",
            {"duration_minutes": 30},
            format="json"
        )

        # Ambos deben tener éxito
        assert response1.status_code in (200, 201)
        assert response2.status_code in (200, 201)

        count = Habit_execution.objects.filter(
            habit=habit,
            execution_date=timezone.now().date()
        ).count()

        assert count == 1


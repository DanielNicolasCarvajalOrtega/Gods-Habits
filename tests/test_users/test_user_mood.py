import pytest
from django.contrib.auth import get_user_model
from django.db import InternalError
from apps.Users_Mood.models import UserMood
from apps.Users_Mood.services import UserMoodService
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from datetime import timedelta

User = get_user_model()

@pytest.mark.django_db
class TestModelUserCreation:
    def test_create_user_mood_success(self,test_user_factory):
        user= test_user_factory()
        mood = UserMood.objects.create(
             user= user,
             date = timezone.now().date(),
             energy_level = 10,
             stress_level = 4,
             mood_notes = "vamos chile",
             sleep_hours = 7,
            stress_trigger = "Finance",
        )


        assert mood.id is not None
        assert mood.user == user
        assert mood.energy_level == 10
        assert mood.stress_level == 4
        assert mood.stress_trigger == "Finance"

    def test_user_mood_with_explicit_date(self,test_user_factory):
        user = test_user_factory()
        days_before = timezone.now().date() - timedelta(days=-4)

        mood = UserMood.objects.create(
            user = user,
            date = days_before,
            energy_level = 4,
            stress_level = 3,
            mood_notes = "ESTA ES UNA PRUEBA",
            sleep_hours = 6,
            stress_trigger = "Social"

        )

        assert mood.date == days_before

    def test_user_mood_default_date(self, test_user_factory):
        """date debe autogenerarse con fecha actual"""
        user = test_user_factory()
        today = timezone.now().date()

        mood = UserMood.objects.create(
            user=user,
            date= today,
            energy_level=5,
            stress_level=5,
            mood_notes = "TENEMOS UNA DEFAULT DATE",
            sleep_hours = 6,
            stress_trigger = "Social"


        )

        assert mood.date == today

    def test_multiple_mood_same_day(self,test_user_factory):
        """ USUARIO CON MULTIPLES MOODS EL MISMO DIA"""

        user = test_user_factory()
        today = timezone.now().date()

        mood_1 = UserMood.objects.create(
            user =user,
            date = today,
            energy_level = 10,
            stress_level = 2,
            mood_notes = "ESTA ES UNA PRIMERA VERSION",
            sleep_hours = 5,
            stress_trigger = "Health",
        )

        mood_2 = UserMood.objects.create(
            user=user,
            date = today,
            energy_level = 2,
            stress_level = 3,
            mood_notes = "ESTA ES UNA SEGUNDA VERSION",
            sleep_hours = 8,
            stress_trigger = "Learning"
        )

        moods_today = UserMood.objects.filter(user=user, date=today)

        assert moods_today.count() == 2
        assert UserMood.objects.filter(id = mood_1.id, user = user, date=today).exists()
        assert UserMood.objects.filter(id = mood_2.id, user=user, date=today).exists()
        assert moods_today.count() == 2

        first, second = moods_today
        # PRIMER MOOD
        assert first.energy_level == 10
        assert first.stress_trigger == "Health"

        # SEGUNDO MOOD
        assert second.date == today
        assert second.stress_trigger == "Learning"



    def test_user_mood_cascade_delete(self,test_user_factory):
        """ELIMINAMOS USER Y SE ELIMINAN SUS MOOD"""

        user = test_user_factory()
        today = timezone.now().date()

        mood  = UserMood.objects.create(
            user= user,
            date = today,
            energy_level = 5,
            stress_level = 3,
            mood_notes = "VAMOS A ELIMINAR USER Y SUS MOODS",
            sleep_hours = 5,
            stress_trigger = "Learning"
        )

        assert UserMood.objects.filter(user=user).count() == 1
        assert UserMood.objects.filter(user_id = user.id).exists()
        assert UserMood.objects.filter(id = mood.id).exists()
        user.delete()

        assert not User.objects.filter(id = user.id).exists()
        assert UserMood.objects.filter(user_id = user.id).count() == 0
        assert not UserMood.objects.filter(id=mood.id).exists()

@pytest.mark.django_db
class TestSleepAnalysis:
    def test_sleep_analysis_no_data(self,test_user_factory):
        """Cuando no hay datos, debe devolver estructura vacía con recomendación genérica"""
        user = test_user_factory()

        result = UserMoodService.get_sleep_quality_analysis(user,days=7)

        assert result["total_records"] == 0
        assert result["average_sleep"] == 0.0
        assert len(result["recommendations"]) > 0
        assert result["consistency_score"] == 0.0
        assert result["sleep_debt"] == 0.0

    def test_sleep_analysis_with_good_sleep(self,test_user_factory):
        """Cuando hay sueño óptimo (7-9h), debe retornar análisis positivo"""
        user = test_user_factory()
        today = timezone.now().date()

        # Crear 5 registros con sueño óptimo
        for i in range(5):
            UserMood.objects.create(
                user=user,
                date=today - timedelta(days=i),
                energy_level=8,
                stress_level=3,
                sleep_hours=8,  # Óptimo: 7-9h
                stress_trigger="Work"
            )

        result = UserMoodService.get_sleep_quality_analysis(user, days=7)

        assert result["total_records"] == 5
        assert result["average_sleep"] == 8.0
        assert result["good_sleep_days"] == 5
        assert result["poor_sleep_days"] == 0
        assert result["sleep_categories"]["optimal"] == 5
        assert result["consistency_score"] >= 80  # Muy consistente
        assert len(result["recommendations"]) > 0

    def test_sleep_analysis_with_insufficient_sleep(self, test_user_factory):
        """Cuando hay sueño insuficiente (<6h), debe alertar"""
        user = test_user_factory()
        today = timezone.now().date()

        # Crear registros con sueño insuficiente
        for i in range(5):
            UserMood.objects.create(
                user=user,
                date=today - timedelta(days=i),
                energy_level=3,
                stress_level=8,
                sleep_hours=5,  # Insuficiente: <6h
                stress_trigger="Work"
            )

        result = UserMoodService.get_sleep_quality_analysis(user, days=7)

        assert result["total_records"] == 5
        assert result["average_sleep"] == 5.0
        assert result["good_sleep_days"] == 0
        assert result["poor_sleep_days"] == 5
        assert result["sleep_categories"]["insufficient"] == 5
        assert result["sleep_debt"] > 0  # Deuda acumulada
        # Debe haber recomendaciones sobre sueño insuficiente
        assert any("sueño insuficiente" in rec.lower() or "insuficient" in rec.lower() 
                   for rec in result["recommendations"])

    def test_sleep_analysis_with_excessive_sleep(self, test_user_factory):
        """Cuando hay exceso de sueño (>9h), debe alertar"""
        user = test_user_factory()
        today = timezone.now().date()

        # Crear registros con sueño excesivo
        for i in range(5):
            UserMood.objects.create(
                user=user,
                date=today - timedelta(days=i),
                energy_level=4,
                stress_level=7,
                sleep_hours=10,  # Excesivo: >9h
                stress_trigger="Health"
            )

        result = UserMoodService.get_sleep_quality_analysis(user, days=7)

        assert result["total_records"] == 5
        assert result["average_sleep"] == 10.0
        assert result["sleep_categories"]["excessive"] == 5
        assert result["poor_sleep_days"] == 5
        assert len(result["recommendations"]) > 0

    def test_sleep_analysis_mixed_sleep_patterns(self, test_user_factory):
        """Cuando hay patrones mixtos de sueño"""
        user = test_user_factory()
        today = timezone.now().date()

        # Día 1: Insuficiente (5h)
        UserMood.objects.create(user=user, date=today, energy_level=3, stress_level=8,
                               sleep_hours=5, stress_trigger="Work")
        # Día 2: Óptimo (8h)
        UserMood.objects.create(user=user, date=today - timedelta(days=1), energy_level=8,
                               stress_level=3, sleep_hours=8, stress_trigger="Work")
        # Día 3: Subóptimo (6.5h)
        UserMood.objects.create(user=user, date=today - timedelta(days=2), energy_level=6,
                               stress_level=5, sleep_hours=6.5, stress_trigger="Work")
        # Día 4: Óptimo (7.5h)
        UserMood.objects.create(user=user, date=today - timedelta(days=3), energy_level=8,
                               stress_level=3, sleep_hours=7.5, stress_trigger="Work")
        # Día 5: Excesivo (10h)
        UserMood.objects.create(user=user, date=today - timedelta(days=4), energy_level=5,
                               stress_level=6, sleep_hours=10, stress_trigger="Health")

        result = UserMoodService.get_sleep_quality_analysis(user, days=7)

        assert result["total_records"] == 5
        assert result["sleep_categories"]["insufficient"] == 1
        assert result["sleep_categories"]["suboptimal"] == 1
        assert result["sleep_categories"]["optimal"] == 2
        assert result["sleep_categories"]["excessive"] == 1
        # Promedio debe estar entre 5 y 10
        assert 5 <= result["average_sleep"] <= 10
        assert len(result["recommendations"]) > 0

    def test_sleep_analysis_consistency_score(self, test_user_factory):
        """Score de consistencia debe reflejar variabilidad del sueño"""
        user = test_user_factory()
        today = timezone.now().date()

        # Crear registros con sueño muy consistente (8h todos los días)
        for i in range(5):
            UserMood.objects.create(
                user=user,
                date=today - timedelta(days=i),
                energy_level=8,
                stress_level=3,
                sleep_hours=8.0,  # Consistente
                stress_trigger="Work"
            )

        result = UserMoodService.get_sleep_quality_analysis(user, days=7)

        # Con stddev ≈ 0, consistency_score debe ser muy alto (cercano a 100)
        assert result["consistency_score"] >= 80
        assert result["best_sleep"] is not None
        assert result["worst_sleep"] is not None


    

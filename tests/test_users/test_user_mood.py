import pytest
from django.contrib.auth import get_user_model
from django.db import InternalError
from apps.Users_Mood.models import UserMood
from django.utils import timezone
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





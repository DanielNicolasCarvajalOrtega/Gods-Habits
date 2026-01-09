from django.contrib.auth import get_user_model
from apps.Users.models import ModelUser
import pytest
from datetime import time
from apps.IA_Coach.services.prompt_builder import *
@pytest.mark.django_db
class TestGetUserProfile:
    """ Test para extraccion de perfil """

    def test_get_profile_exist(self,test_user_factory):
        """ extraer perfil existente"""

        user = test_user_factory()
        ModelUser.objects.create(
            user=user,
            user_type="Beginner",
            first_focus_area="Learning",
            secondary_focus_area="Creativity",
            daily_time_availability="high",
            preferred_morning_time=time(4,0),
            preferred_evening_time =time(4,30),
            motivation_level = 18,
            user_objective="objetivos por su puesto",
            experience_level_user= 2,
        )

        profile = get_user_profile(user)

        assert profile is not None
        assert profile["user_type"] == "Beginner"
        assert profile["focus_area"] == "Learning"
        assert profile["motivation_level"] == 18
    

    def test_get_profile_not_exists(self,test_user_factory):
        """Usuario sin perfil"""
        user = test_user_factory()
        profile = get_user_profile(user)

        assert profile is None

    def test_get_profile_truncates_long_objective(self,test_user_factory):
        """ al ser un objetivo muy largo debe acortarse """
        user = test_user_factory()
        long_objective = "A" * 300 # mas de 200 caractes
        ModelUser.objects.create(
            user=user,
            user_type="Beginner",
            first_focus_area="Finance",
            secondary_focus_area="Mundfulness",
            daily_time_availability="low",
            preferred_morning_time=time(4,1),
            preferred_evening_time=time(2,3),
            motivation_level=13,
            user_objective=long_objective,
            experience_level_user=10,
        )

        profile = get_user_profile(user)
        assert len(profile["objective"]) == 200
        assert isinstance(profile["objective"],str)
        assert profile["objective"] == long_objective[:200]

    



        
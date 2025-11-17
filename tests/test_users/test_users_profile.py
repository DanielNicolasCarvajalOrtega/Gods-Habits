
import pytest
from django.contrib.admin import display
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.template.defaultfilters import first

from apps.Users.models import ModelUser
from datetime import time
@pytest.mark.django_db
class TestModelUser:
    def test_model_user_creates_and_associates_with_django_user(self,test_user_factory,test_model_user_factory):
        from apps.Users.models import ModelUser

        user = test_user_factory(username='Javiera')
        profile = test_model_user_factory(user)

        assert profile.user_id == user.id
        assert isinstance(profile, ModelUser)

    def test_get_display_choices_if_exist(self, test_user_factory, test_model_user_factory):
        user = test_user_factory(username='Bobinas')
        profile = test_model_user_factory(user)

        if hasattr(profile, "first_focus_area"):
            method_name = "get_first_focus_area_display"
            if hasattr(profile, method_name):
                display = getattr(profile, method_name)()
                assert isinstance(display, str)

            else:
                pytest.skip("En ModelUser existe first_focus_area pero sin metodo get_display")
        else:
            pytest.skip("ModelUser no define first_focus_area se omitio el test")


    def test_create_model_user_success(self,test_user_factory):
        user = test_user_factory()
        model_user = ModelUser.objects.create(
            user= user,
            user_type = "Beginner",
            first_focus_area = 'Learning',
            secondary_focus_area = "Work",
            daily_time_availability = "medium",
            preferred_morning_time = time(7,0),
            preferred_evening_time = time(18,30),
            motivation_level = 4,
            user_objective = "OBJETIVO DE PRUEBAAASS",
            experience_level_user = 5
        )

        assert model_user.id is not None
        assert model_user.user == user
        assert model_user.user_type == "Beginner"
        assert model_user.motivation_level == 4

    def test_model_user_one_to_one_with_user(self,test_user_factory):
        user = test_user_factory()

        model_user = ModelUser.objects.create(
            user=user,
            user_type="Beginner",
            first_focus_area='Learning',
            secondary_focus_area="Work",
            daily_time_availability="medium",
            preferred_morning_time=time(7, 0),
            preferred_evening_time=time(18, 30),
            motivation_level=4,
            user_objective="OBJETIVO DE PRUEBAAASS",
            experience_level_user=5
        )

        user_from_db = User.objects.get(id=user.id)

        assert user_from_db.profile == model_user
        assert model_user.user == user

    def test_cannot_create_duplicate_model_user(self,test_user_factory):
        user = test_user_factory()

        model_user = ModelUser.objects.create(
            user=user,
            user_type="Advanced",
            first_focus_area='Social',
            secondary_focus_area="Creativity",
            daily_time_availability="medium",
            preferred_morning_time=time(8, 20),
            preferred_evening_time=time(19, 10),
            motivation_level=6,
            user_objective="OBJETIVO DE PRUEBAAASS PRIMERO",
            experience_level_user=5
        )

        assert ModelUser.objects.filter(user=user, id=user.id).count() == 1


        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ModelUser.objects.create(
                    user=user,
                    user_type="Advanced",
                    first_focus_area='Social',
                    secondary_focus_area="Creativity",
                    daily_time_availability="high",
                    preferred_morning_time=time(8, 20),
                    preferred_evening_time=time(19, 10),
                    motivation_level=10,
                    user_objective="OBJETIVO DE PRUEBAAASS SEGUNDO",
                    experience_level_user=4
                )

        assert ModelUser.objects.filter(user=user).count() == 1
        assert ModelUser.objects.get(user=user).id == model_user.id

    def test_model_user_cascade_delete(self,test_user_factory):
        user = test_user_factory()

        model_user = ModelUser.objects.create(
            user=user,
            user_type="Advanced",
            first_focus_area='Social',
            secondary_focus_area="Creativity",
            daily_time_availability="low",
            preferred_morning_time=time(8, 20),
            preferred_evening_time=time(19, 10),
            motivation_level=5,
            user_objective="OBJETIVO DE PRUEBAAASS SEGUNDO",
            experience_level_user=7
        )

        model_user_id = model_user.id

        assert User.objects.filter(id=user.id).exists()
        assert ModelUser.objects.filter(id=model_user_id, user=user).exists()
        assert ModelUser.objects.filter(user=user).exists()
        user.delete()

        assert not User.objects.filter(id=model_user_id).exists()
        assert not ModelUser.objects.filter(id=model_user_id).exists()
        assert ModelUser.objects.filter(id=model_user_id).count() == 0

    def test_model_user_str_representation(self,test_user_factory):
        user = test_user_factory(username='Nicolas')

        model_user = ModelUser.objects.create(
            user=user,
            user_type="Advanced",
            first_focus_area='Social',
            secondary_focus_area="Creativity",
            daily_time_availability="low",
            preferred_morning_time=time(8, 20),
            preferred_evening_time=time(19, 10),
            motivation_level=5,
            user_objective="OBJETIVO DE PRUEBAAASS SEGUNDO",
            experience_level_user=7
        )

        str_repr = str(model_user)

        assert 'Nicolas' in str_repr.lower() or 'Advanced' in str_repr.lower()



import pytest
from django.contrib.admin import display

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



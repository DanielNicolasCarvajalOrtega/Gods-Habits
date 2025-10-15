import os
import pytest
from django.conf import settings
from django.utils import timezone


@pytest.fixture(autouse=True, scope="session")
def test_configure_settings_for_test(django_db_blocker): # VERIFICA SI EXISTE UNA BASE DE DATOS ACTIVA O EN USO
    # DECLARAMOS LA CONIGURACION GLOBAL
    settings.TIME_ZONE = "America/Santiago"
    settings.USE_TZ = True
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
    yield


@pytest.fixture(autouse=True)
def test_tz_overrite(): # ENVUELVE EL TEST EN UNA TIMEZONE LOCAL
    with timezone.override("America/Santiago"):
        yield
    """TODO SE EVALUA EN ESTA ZONA, SIGNIFICA SANTIAGO O 
     HOY EN CHILE PARA TODOS LOS TEST"""

@pytest.fixture()
def test_user_factory(django_user_model):
    created = []
    def _make(**kwargs):
        default = {
            'username': f"user_{len(created)+1}",
            'email': "user.example25@gmail.com"
        }
        default.update(kwargs)
        user = django_user_model.objects.create_user(**default)
        created.append(user)
        return user
    return _make

@pytest.fixture()
def test_model_user_factory():
    from apps.Users.models import ModelUser

    def _first_choice(choices, fallback):
        try:
            return choices[0][0]
        except Exception:
            return fallback

    def _make(user,**kwargs):
        USER_TYPE = getattr(ModelUser, "USER_TYPE_CHOICES", [])
        FOCUS = getattr(ModelUser, "FOCUS_AREA_CHOICES", [])
        TIME = getattr(ModelUser,"TIME_AVAILABILITY_CHOICES",[])

        defaults = {
            'user': user,
            'user_type': _first_choice(USER_TYPE, 'Beginner'),
            'first_focus_area': _first_choice(FOCUS, 'Work'),
            'daily_time_availability': _first_choice(TIME, 'high'),
            'motivation_level': 10,
            'user_objective':'objetivo sencillo',
            'secondary_focus_area':[],
            'preferred_morning_time':None,
            'preferred_evening_time':None,

        }

        defaults.update(kwargs)
        return ModelUser.objects.create(**defaults)
    return _make

@pytest.fixture()
def test_habit_factory():
    from apps.Habits.models import Habits

    def _make(user, **kwargs):
        default = {
            'user': user,
            'username':'Javiera',
            'title': 'Trabajo proactivo',
            'description': 'Nos levantamos temprano para ir a '
                           'solucionar pruebas de testeo',
            'frequency':'Daily',
            'priority': 'High',
            'target_minutes': 90,
            'is_active': False,

        }
        default.update(default)
        return Habits.objects.create(**default)
    return _make


@pytest.fixture()
def test_executoin_factory():
    from apps.Habits.models import Habit_execution

    def _make(**kwargs):
        return Habit_execution.objects.create(**kwargs)
    return _make


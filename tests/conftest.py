import os
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from apps.Habits.models import Habit_execution

User = get_user_model()


@pytest.fixture(autouse=True, scope="session")
def test_configure_settings_for_test(django_db_blocker):
    """Configuración global de settings para tests"""
    settings.TIME_ZONE = "America/Santiago"
    settings.USE_TZ = True
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
    yield


@pytest.fixture(autouse=True)
def test_tz_override():
    """Envuelve todos los tests en timezone America/Santiago"""
    with timezone.override("America/Santiago"):
        yield


# ===== FACTORIES =====

@pytest.fixture
def test_user_factory(django_user_model):
    """Factory para crear usuarios de Django"""
    created = []

    def _make(**kwargs):
        defaults = {
            'username': f"user_{len(created) + 1}",
            'email': f"user{len(created) + 1}@example.com",
            'password': 'testpass123'  # ✅ Agregar password por defecto
        }
        defaults.update(kwargs)
        user = django_user_model.objects.create_user(**defaults)
        created.append(user)
        return user

    yield _make

    # Cleanup (opcional)
    # for user in created:
    #     user.delete()

    return _make


@pytest.fixture
def test_model_user_factory():
    """Factory para crear ModelUser (perfil extendido)"""
    from apps.Users.models import ModelUser

    def _first_choice(choices, fallback):
        try:
            return choices[0][0]
        except Exception:
            return fallback

    def _make(user, **kwargs):
        USER_TYPE = getattr(ModelUser, "USER_TYPE_CHOICES", [])
        FOCUS = getattr(ModelUser, "FOCUS_AREA_CHOICES", [])
        TIME = getattr(ModelUser, "TIME_AVAILABILITY_CHOICES", [])

        defaults = {
            'user': user,
            'user_type': _first_choice(USER_TYPE, 'Beginner'),
            'first_focus_area': _first_choice(FOCUS, 'Work'),
            'daily_time_availability': _first_choice(TIME, 'high'),
            'motivation_level': 10,
            'user_objective': 'objetivo sencillo',
            'secondary_focus_area': [],
            'preferred_morning_time': None,
            'preferred_evening_time': None,
        }
        defaults.update(kwargs)
        return ModelUser.objects.create(**defaults)

    return _make


@pytest.fixture
def test_habit_factory():
    """Factory para crear Habits"""
    from apps.Habits.models import Habits

    def _make(user, **kwargs):
        defaults = {
            'user': user,
            'title': 'Trabajo proactivo',
            'description': 'Nos levantamos temprano para ir a solucionar pruebas de testeo',
            'frequency': 'Daily',
            'priority': 'High',
            'target_minutes': 90,
            'is_active': True,  # ✅ Cambiar a True por defecto
        }
        defaults.update(kwargs)  # ✅ CORREGIDO: era default.update(default)
        return Habits.objects.create(**defaults)

    return _make


@pytest.fixture
def test_execution_factory():  # ✅ CORREGIDO: era test_executoin_factory
    """Factory para crear Habit_execution"""
    from apps.Habits.models import Habit_execution

    def _make(**kwargs):
        return Habit_execution.objects.create(**kwargs)

    return _make


# ===== CLIENTES API =====

@pytest.fixture
def api_client():
    """Cliente API no autenticado"""
    return APIClient()


@pytest.fixture
def authenticated_client(test_user_factory):
    """Cliente API autenticado con force_authenticate"""
    client = APIClient()

    # Crear usuario usando el factory
    user = test_user_factory(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

    # ✅ CORRECCIÓN PRINCIPAL: force_authenticate en vez de force_login
    client.force_authenticate(user=user)
    client.user = user  # Guardar referencia para usar en tests

    return client


@pytest.fixture
def client_auth(test_user_factory):
    """Alias para authenticated_client (para compatibilidad con tus tests existentes)"""
    client = APIClient()

    user = test_user_factory(
        username='testuser_auth',
        email='testauth@example.com',
        password='testpass123'
    )

    client.force_authenticate(user=user)
    client.user = user

    return client


# ===== DATOS DE USUARIO =====

@pytest.fixture
def user_data():
    """Diccionario con datos de usuario para registro"""
    return {
        'username': 'testuser_data',
        'email': 'userdata@example.com',
        'password': 'testpass123'
    }


@pytest.fixture
def create_user():
    """Factory simple para crear usuarios"""
    created = []

    def _create_user(**kwargs):
        defaults = {
            'username': f'user_{len(created)}',
            'email': f'user{len(created)}@example.com',
            'password': 'testpass123'
        }
        defaults.update(kwargs)
        user = User.objects.create_user(**defaults)
        created.append(user)
        return user

    return _create_user


# ===== FACTORIES ADICIONALES ÚTILES =====

@pytest.fixture
def habit_factory(test_user_factory):
    """Factory de hábitos con usuario automático"""
    from apps.Habits.models import Habits

    def _make(**kwargs):
        # Si no se pasa user, crear uno automáticamente
        if 'user' not in kwargs:
            kwargs['user'] = test_user_factory()

        defaults = {
            'title': 'Hábito de prueba',
            'description': 'Descripción de prueba',
            'frequency': 'Daily',
            'priority': 'Medium',
            'target_minutes': 30,
            'is_active': True,
        }
        defaults.update(kwargs)
        return Habits.objects.create(**defaults)

    return _make


@pytest.fixture
def user_factory(test_user_factory):
    """Alias más corto para test_user_factory"""
    return test_user_factory
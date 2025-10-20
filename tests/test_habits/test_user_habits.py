import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from apps.Habits.models import Habits
from rest_framework.test import APIClient


@pytest.fixture
def user(db):
    return User.objects.create_user(username="demoUser", password="demo1234")


@pytest.fixture
def client_auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_list_habits_empty(client_auth):
    request = client_auth.get("/api/habits/")
    assert request.status_code == 200
    assert isinstance(request.json(), list)


def test_create_habits_sucess(client_auth):
    payload = {
        "title": "Beber agua",
        "description": "debo beber agua cada 3 horas al dia "
                       "para ayudarme con mis riñones.."
                       "no beber mas de 10 litros..",
        "frequency": "Daily",
        "priority": "High",
        "target_minutes": 100,
    }
    request = client_auth.post("/api/habits/", payload, format="json")
    assert request.status_code in (200, 201)
    data = request.json()
    assert data['title'] == "Beber agua"




def test_partial_update_habit(client_auth):
    request = client_auth.post("/api/habits/",{
            "title": "Leer",
            "description": "no beber agua y ahora leer",
            "frequency" : "Weekly",
            "priority": "Low",
            "target_minutes":60,
        },
        format = "json"
    )
    habit_id = request.json()["id"]

    request_2 = client_auth.patch(f"/api/habits/{habit_id}/",
                                  {
                                      "priority": "High"
                                  }, format = "json")
    assert request_2.status_code in (200,202)
    assert request_2.json()["priority"] == "High"


def test_register_today_without_duplicating(client_auth):
    # Crear hábito
    request = client_auth.post("/api/habits/", {
        "title": "Trabajar en casa",
        "description": "Trabajar en un microcomponente de JAVA...",
        "frequency": "Weekly",
        "priority": "High",
        "target_minutes": 100,
    }, format="json")

    assert request.status_code in (200, 201), f"{request.status_code=} {request.json()=}"
    habit_id = request.json()["id"]

    # MARCA UN HÁBITO COMPLETO - PRIMERA VEZ
    request_2 = client_auth.post(
        f"/api/habits/{habit_id}/mark_habit_user_complete/",
        {
            "duration_minutes": 480,
            "notes": "el trabajo va recien comenzando..."
        },
        format="json"
    )

    assert request_2.status_code in (200, 201)
    response_2 = request_2.json()

    # Obtener el ID del objeto execution
    execution_id_1 = response_2["execution"]["id"]  # Acceder al objeto anidado

    # MARCA UN HÁBITO COMPLETO - SEGUNDA VEZ (debe actualizar, no crear)
    request_3 = client_auth.post(
        f"/api/habits/{habit_id}/mark_habit_user_complete/",
        {
            "duration_minutes": 180,
            "notes": "Buen trabajo, ya que se completo el trabajo..."
        },
        format="json"
    )

    assert request_3.status_code in (200, 201)
    response_3 = request_3.json()

    # Obtener el ID del objeto execution
    execution_id_2 = response_3["execution"]["id"]


    # Verificar que NO se creó una nueva ejecución (mismo ID)
    assert execution_id_2 == execution_id_1, "Debería actualizar la misma ejecución, no crear una nueva"

    # Verificar que los datos se actualizaron
    assert response_3["execution"]["duration_minutes"] == 180
    assert "Buen trabajo" in response_3["execution"]["notes"]

    #Verificar el mensaje correcto
    assert response_3["message"] == "Ejecución actualizada"

def test_statistics_and_pending(client_auth):
    request_stats= client_auth.get(f"/api/habits/habit_user_statistics/")
    assert request_stats.status_code == 200
    status = request_stats.json()

    for colum in [
        "total_active", "total_inactive",
        "completion_rate_7days", "completion_rate_30days",
        "habits_by_priority", "habits_by_frequency",
    ]:
        assert colum in status

    request_pending = client_auth.get(f"/api/habits/habit_pending_today/")
    assert request_pending.status_code == 200
    assert isinstance(request_pending.json(), list)

def test_delete_habits(client_auth):
    request = client_auth.post("/api/habits/",
                               {
                                   "title": "Meditar",
                                   "description": "Meditar 20 minutos todos los dias para "
                                                  "sentirme mejor mentalmente y botar estres",
                                   "frequency": "Daily",
                                   "priority": "High",
                                   "target_minutes": 20,

                               }, format="json"
    )
    habit_id = request.json()["id"]

    request_2 = client_auth.delete(f"/api/habits/{habit_id}/")
    assert request_2.status_code in (200,204)

    request_3 = client_auth.get(f"/api/habits/{habit_id}/")
    assert request_3.status_code == 404 # lo obtenemos para verificar que existe







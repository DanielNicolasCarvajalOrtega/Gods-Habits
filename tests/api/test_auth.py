
REGISTER_URL = "/api/users/auth/register/"
TOKEN_OBTAIN_URL = "/api/token/"
TOKEN_REFRESH_URL = "/api/token/refresh/"
TOKEN_VERIFY_URL = "/api/token/verify/"

import pytest
from datetime import timedelta, time
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

user = get_user_model()

@pytest.fixture()
def api_client():
    return APIClient()

@pytest.fixture()
def user_data():
    return {
        'username': 'Alicia',
        'email': 'alice25@gmail.com',
        'password':'alicia123@@'
    }

@pytest.mark.django_db
def test_register_success(api_client, user_data):
    response = api_client.post(REGISTER_URL, user_data, format="json")
    assert response.status_code in (200,201), response.data    # CONFIRMAMOS QUE EL USUARIO EXSITA REALEMTE
    assert user.objects.filter(username=user_data["username"]).exists()


@pytest.mark.django_db
def test_register_duplicate_email_fails(api_client, user_data):
    # PRIMER REGISTRO EN OK
    register1 = api_client.post(REGISTER_URL, user_data, format="json")
    assert register1.status_code in (200,201), register1.data

    # SEGUNDO REGISTRO CON EL MISMO MAIL DEBE FALLAR
    duplicated = dict(user_data, username="AliciaA")
    register2 = api_client.post(REGISTER_URL, duplicated, format="json")
    assert register2.status_code in (400,409), register2.data


@pytest.mark.django_db
def test_login_wrong_credentials_return_401(api_client):
    user.objects.create_user(username="carol",
                             email="carol.28@gmail.com",
                             password="carol123@@"
                             )
    response = api_client.post(TOKEN_OBTAIN_URL,
                               {
                                   "username":'carol',
                                   "password":'carol123@',
                               }, format="json")

    assert response.status_code == 401, response.data


@pytest.mark.django_db
def test_login_success_return_tokens(api_client):
    # CREAMOS USUARIO DIRECTO DE LA DB
    users = user.objects.create_user(
        username="Bob",
        email="bobsponga@gmail.com",
        password="bob123@@",
    )
    # LOGIN CON simpleJWT, ESPERA USERNAME/PASSWORD
    response = api_client.post(TOKEN_OBTAIN_URL,
                               {
                                "username": 'Bob',
                                "password" :'bob123@@'
                                }, format="json")

    assert response.status_code == 200, response.data
    assert 'access' in response.data and 'refresh' in response.data

@pytest.mark.django_db
def test_refresh_works_and_access_expires(api_client, monkeypatch):
    #VIDA CORTA PARA EL ACCCESS TOKEN
    from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
    monkeypatch.setattr(AccessToken, "lifetime", timedelta(seconds=1))
    monkeypatch.setattr(RefreshToken, "lifetime", timedelta(days=1))

    user.objects.create_user(
        username="Danilo",
        email="danilo22@gmail.com",
        password="danilo123@@",
    )

    login = api_client.post(TOKEN_OBTAIN_URL,
                            {
                                "username": 'Danilo',
                                "password": 'danilo123@@',

                            }, format="json"
    )
    assert login.status_code == 200, login.data
    access = login.data["access"]
    refresh = login.data["refresh"]

    import time
    time.sleep(2)

    verify = api_client.post(TOKEN_VERIFY_URL,
                             {
                                 "token": access
                             }, format="json"
    )
    # VERIFICAMOS EL TOKEN EXPIRADO EN LA URL /verify/ si no existe salta el test
    if verify.status_code == 404:
        pytest.skip("TOKEN_VERIFY_URL no existe en esta API.."
                    "OMITIENDO VERIFICACION DE EXPIRACION... ")
    assert verify.status_code == 401, verify.data # TOKEN NO VALIDA

    refresh = api_client.post(TOKEN_REFRESH_URL,
                              {
                                  "refresh": refresh
                              }, format= "json"
    )
    assert refresh.status_code == 200, getattr(refresh,'data', refresh.content)
    assert "access" in refresh.data

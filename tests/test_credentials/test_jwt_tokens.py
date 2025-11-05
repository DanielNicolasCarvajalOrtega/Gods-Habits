from datetime import timedelta, time
import time
import pytest
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from tests.api.test_models import TOKEN_OBTAIN_URL, TOKEN_REFRESH_URL, TOKEN_VERIFY_URL


@pytest.mark.django_db
class TestJWTTokens:

    def test_access_token_can_authenticate(self,api_client,create_user):
        """ PERMITE ACCEDER HA ENDPOINTS PROTEGIDOS"""
        create_user(username= "user", password="123user")
        login = api_client.post( TOKEN_OBTAIN_URL,
            {
                'username': "user",
                'password': "123user",
            },format= "json")

        access_token = login.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.get('/api/habits/')

        assert response.status_code in (200,204)


    def test_refresh_token_generates_new_access(self,api_client,create_user):
        """ GENERA NUEVO ACCESS TOKEN"""

        create_user(username="user", password="user123")
        login = api_client.post(TOKEN_OBTAIN_URL, {
            'username': "user",
            "password" : "user123"

        }, format="json")

        refresh_token = login.data["refresh"]
        response = api_client.post(TOKEN_REFRESH_URL,{
            'refresh': refresh_token,
        },format="json")

        assert response.status_code == 200
        assert 'access' in response.data
        assert len(response.data['access']) > 0


    def test_expired_access_token_fails(self,api_client,create_user,monkeypatch):

        """ ACCESS TOKEN, SI EXPIRA NO DEBE AUTENTICAR"""
        monkeypatch.setattr(AccessToken, "lifetime", timedelta(seconds=1))
        monkeypatch.setattr(RefreshToken, "lifetime", timedelta(days=1))

        create_user(username="user", password="user123")
        login = api_client.post(TOKEN_OBTAIN_URL, {
            'username':"user",
            'password':"user123"
        }, format="json")

        access_token = login.data["access"]
        time.sleep(2)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.get('/api/habits/')

        assert response.status_code == 401

    def test_verify_token_endpoint(self,api_client,create_user):
        """ ENDPOINT DE VERIFICACION.. VALIDA TOKENS CORRECTAMENTE """
        create_user(username="user", password="user1234")

        login = api_client.post(TOKEN_OBTAIN_URL, {
            'username': "user",
            'password': "user1234"
        }, format="json")

        access_token = login.data["access"]
        response = api_client.post(TOKEN_VERIFY_URL, {
            'token': access_token,

        }, format="json")

        if response.status_code == 404:
            pytest.skip("TOKEN_VERIFY_URL, no existe en esta API")

        assert response.status_code == 200

    def test_verify_invalid_token_fails(self,api_client):
        response = api_client.post(TOKEN_VERIFY_URL, {
            'token': 'invalid_token'
        }, format="json")

        if response.status_code == 404:
            pytest.skip("TOKEN_VERIFY_URL no existe")

        assert response.status_code == 401


    def test_token_whitout_bearer_prefix_fails(self,api_client,create_user):
        """ TOKEN SIN PREFIJO 'Bearer' DEBE FALLAR """
        create_user(username= "user", password="user1234")
        login = api_client.post(TOKEN_OBTAIN_URL, {
            'username': "user",
            'password': "user1234",

        }, format="json")

        access_token = login.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=access_token)
        response = api_client.get('/api/habits/')

        assert response.status_code == 401

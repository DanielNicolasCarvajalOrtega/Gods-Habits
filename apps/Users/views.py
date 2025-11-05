from rest_framework.response import Response
from rest_framework import generics, permissions, authentication, status
from .serializers import RegisterUserSerializers

class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterUserSerializers
    permissions_classes = [permissions.AllowAny]
    authentication_classes = []


    def post(self, request):
        s = RegisterUserSerializers(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response({
            "id":user.id,
            "username": user.username,
            "email": user.email
        },
        status= status.HTTP_201_CREATED,
        )




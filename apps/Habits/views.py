from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from .serializers import *
from .services import HabitService



class HabitViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo usuarios autenticados"""
        return HabitService.get_user_habits(self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return HabitListSerializer
        elif self.action == 'create':
            return HabitCreateSerializer
        return HabitSerializers


    def list_user_habits(self, request):
        habit_active = request.query_params.get('is_active','true')
        habit_active = None if habit_active == 'all' else (habit_active.lowe() =='true')

        habits = HabitService.get_user_habits(request.user, habit_active)
        serializers = self.get_serializer(habits,many=True)

        return Response(serializers.data)


    def create_user_habits(self,request):
        serializers = self.get_serializer(date=request.data, context={'request': request})
        serializers.is_valid(raise_exeption=True)

        try:
            habit=HabitService.create_habit(
                user=request.user,
                validated_data=serializers.validated_data
            )

            return Response(
                HabitSerializers(habit).data,
                status=HTTP_201_CREATED
            )

        except ValueError as err:
            return Response(
                {'error':str(err)},
                status=status.HTTP_400_BAD_REQUEST
            )


    def retrieve_details_for_habits(self, request, pk=None):
        habits = HabitService.get_habit_by_id(pk, request.user)

        if not habits:
            return Response(
                {'error':'HAbito no encontrado'},
                status= status.HTTP_404_NOT_FOUND
            )
        serializers = self.get_serializer(habits)
        return Response(serializers.data)


    def update_user_complete_habit(self,request,pk=None):
        serializers = self.get_serializer(data=request.data, context={'request':request})
        serializers.is_valid(raise_exception=True)

        try:
            habits = HabitService.update_habit(
                habit_id=pk,
                user=request.user,
                validated_data=serializers.validated_data
            )
            return Response(HabitSerializers(habits).data)

        except ValueError as err:
            return Response(
                {'error':str(err)},
                status=status.HTTP_404_NOT_FOUND
            )

    def partial_user_update_habits(self,request, pk=None):
        habits = HabitService.get_habit_by_id(pk, request.user)

        if not habits:
            return Response(
                {
                    'error':'Habito no encontrado'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializers = self.get_serializer(habits,data=request.data,
                                          partial=True,
                                          context={'request':request})
        serializers.is_valid(raise_exception=True)

        try:
            habits = HabitService.update_habit(
                habit_id=pk,
                user = request.user,
                validated_data=serializers.validated_data
            )

            return Response(HabitSerializers(habits).data)

        except ValueError as err:
            return Response({
            'error': str(err),
            },
            status= status.HTTP_404_NOT_FOUND
            )

    def destroy_user_habits(self, request,pk=None):
        try:
            HabitService.delete_habit(
                habit_id=pk, user=request.user, soft_delete=True
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ValueError as err:
            return Response(
                {
                    'error': str(err)
                },
                status= status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def toggle_active(self,request, pk=None):
        """HABITAR O DESABILITAR HABITO"""

        try:
            habits = HabitService.toogle_habit_active(pk, request.user)
            return Response(HabitSerializers(habits).data)

        except ValueError as err:
            return Response(
                {
                    'error': str(err)
                },
                status= status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def mark_habit_user_complete(self,request,pk=None):
        try:
            habits = Habits.objects.get(id=pk, user=request.user)
        except Habits.DoesNotExist:
            return Response({
                'error': 'Habito no encontrado'
            },
                status= status.HTTP_404_NOT_FOUND
            )

        if not habits.is_active:
            return Response({
                'error': 'No puedes completar un habito inactivo'
            },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializers = HabitMarkCompleteSerializer(
            data = request.data,
            context={
                'request': request,
                'habit_id' : pk
            }
        )
        serializers.is_valid(raise_exception=True)

        try:
            execution = HabitService.mark_habit_complete(
                habit_id = pk,
                user=request.user,
                duration_minutes= serializers.validated_data.get('duration_minutes'),
                notes = serializers.validated_data.get('notes','')
            )
            return Response(
                HabitExecutionSerializer(execution).data,
                status=status.HTTP_200_OK
            )

        except ValueError as err:
            Response(
                {
                    'error': str(err)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as err:
            return Response({
                'error': 'Error al completar el habito', str:err
            },
            status = status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=True, methods=['post'])
    def mark_habit_user_skipped(self,request, pk=None):

        try:
            habits = Habits.objects.get(id=pk, user=request.user)
        except Habits.DoesNotExist:
            return Response(
                {'error': "Habito no existente"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not habits.is_active:
            return Response(
                {'error': "El Habito no esta activo"},
                status= status.HTTP_400_BAD_REQUEST
            )

        notes = request.data.get('notes', '')
        if not isinstance(notes,str):
            return Response(
                {'error': 'Escribe solamente texto'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(notes) > 500:
            return Response(
                {'error':'Exedes el maximo de caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            execution = HabitService.mark_habit_skipped(
                habit_id=pk,
                user= request.user,
                notes= notes
            )
            return Response(
                HabitExecutionSerializer(execution).data,
                status=status.HTTP_200_OK
            )
        except ValueError as err:
            return Response(
                {'error': str(err)},
                status=status.HTTP_400_BAD_REQUEST
            )


    @action(detail=False,methods=['get'] )
    def habit_user_statistics(self,request):
        statistics = HabitService.get_user_statistics(
            request.user
        )
        return Response(statistics)

    @action(detail=False, methods=['get'])
    def habit_pending_today(self, request):
        habits_today = HabitService.get_habit_for_today(request.user)
        return Response(habits_today)

    @action(detail=True, methods=['get'])
    def habit_user_streak(self,request,pk=None):
        habits_streak= HabitService.calculate_habit_streak(pk, request.user)
        return Response({'streak_days': habits_streak})

class CustomTokenObtainPairSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls,user):
        token = super().get_token(user)
        token['username'] = user.username
        token['emial'] = user.get_email_field_name()

        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializers = CustomTokenObtainPairSerializer
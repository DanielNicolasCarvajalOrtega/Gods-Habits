from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from apps.Habits.models import Habits, Habit_execution
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterUserSerializers(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators= [
            UniqueValidator
                (
            User.objects.all(),
            lookup='iexact'
            )
        ]
    )
    password = serializers.CharField(write_only=True, min_length=10)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)



class HabitSerializers(serializers.ModelSerializer):
    total_executions = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()

    class Meta:
        model = Habits
        fields = [
            'id',
            'user',
            'title',
            'priority',
            'description',
            'frequency',
            'target_minutes',
            'is_active',
            'created_at',
            'total_executions',
            'completion_rate',

        ]

        read_only_fields = ['id', 'created_at', 'total_executions', 'is_active']

    def get_total_executions(self, obj):  # total de ejecuciones
        return obj.executions.count()

    def get_completion_rate(self, obj):  # porcentaje de completado
        total = obj.executions.count()
        if total == 0:
            return 0
        completed = obj.executions.filter(status='Completed').count()
        return round((completed / total) * 100, 2)

    def validate_title(self, value):  # no se puede repetir el nombre
        pass

    def validate_duration_habit(self, value):  #
        if value < 1:
            raise serializers.ValidationError("La duracion del habito debe ser mayor a 1 minuto")

        if value > 180:
            raise serializers.ValidationError("La duracion del habito debe ser menor a 180 minutos")
        return value


class HabitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habits
        fields = ['id',
                  'title',
                  'priority',
                  'target_minutes',
                  'frequency',
                  'is_active'
                  ]


class HabitCreateSerializer(serializers.ModelSerializer):
    """CREACION DE HABITOS"""

    class Meta:
        model = Habits
        fields = [
            'title',
            'description',
            'priority',
            'frequency',
            'target_minutes'
        ]

    def validate_title(self, value):
        pass


class HabitExecutionSerializer(serializers.ModelSerializer):
    habit_title = serializers.CharField(source='habit.title', read_only=True)

    class Meta:
        model = Habit_execution
        fields = [
            'id',
            'habit_title',
            'habit',
            'execution_date',
            'duration_minutes',
            'status',
            'notes',
            'created_at'
        ]

        read_only_fields = ['id', 'habit_title', 'created_at', 'execution_date']


class MarkCompleteSerializer(serializers.Serializer):
    duration_minutes = serializers.IntegerField(required=False, min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=520)

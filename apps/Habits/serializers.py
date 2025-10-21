from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Habits, Habit_execution


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
            'completion_rate',
            'total_executions',
            'is_active',
            'created_at',
        ]

        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            "title": {"required":True},
            "frequency": {"required":True},
            "priority": {"required":True},
            "target_minutes": {"required":True, "min_value":1},
        }

    def create(self, validated_data):
        return super().create(validated_data)

    def get_total_executions(self, obj):  # total de ejecuciones
        return obj.habits_executions.count()

    def get_completion_rate(self, obj):  # porcentaje de completado
        total = obj.habits_executions.count()
        if total == 0:
            return 0
        completed = obj.habits_executions.filter(status='Completed').count()
        return round((completed / total) * 100, 2)

    def validate_title(self, value):  # no se puede repetir el nombre
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("El titulo es obligatorio")

        user= self.context.get("request").user if self.context.get("request") else None
        if user and Habits.objects.filter(user=user, title__iexact=value).exists():
            raise serializers.ValidationError("Ya tienes un habito con este titulo")
        return value


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
class HabitDetailSerializer(serializers.ModelSerializer):
    total_executions = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()

    class Meta:
        model = Habits
        fields = [
            'id', 'title', 'description', 'priority', 'frequency',
            'target_minutes', 'is_active', 'created_at',
            'completion_rate', 'total_executions'
        ]
        read_only_fields = ['id', 'created_at']

    def get_total_executions(self, obj):
        return obj.habits_executions.count()

    def get_completion_rate(self, obj):
        total = obj.habits_executions.count()
        if total == 0:
            return 0
        completed = obj.habits_executions.filter(status='Completed').count()
        return round((completed / total) * 100, 2)

class HabitCreateSerializer(serializers.ModelSerializer):
    """CREACION DE HABITOS"""
    class Meta:
        model = Habits
        fields = [
            'id',
            'title',
            'description',
            'priority',
            'frequency',
            'target_minutes'
        ]

    def validate_title(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("El título es obligatorio.")
        user = self.context.get("request").user if self.context.get("request") else None
        if user and Habits.objects.filter(user=user, title__iexact=value).exists():
            raise serializers.ValidationError("Ya tienes un hábito con este título.")
        return value


class HabitUpdateSerializer(serializers.ModelSerializer):
   # SIN HABITOS INCLUIDOS

    class Meta:
        model = Habits
        fields = [
            'title',
            'description',
            'priority',
            'frequency',
            'target_minutes',
            'is_active'
        ]

    def validate_title(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("El título es obligatorio.")

        user = self.context.get("request").user if self.context.get("request") else None
        instance = self.instance  # El objeto que se está actualizando

        # Verificar duplicados, excluyendo el objeto actual
        if user and Habits.objects.filter(
                user=user,
                title__iexact=value
        ).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Ya tienes un hábito con este título.")
        return value

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

        read_only_fields = ['id',
                            'habit_title',
                            'created_at',
                            'execution_date']


class HabitMarkCompleteSerializer(serializers.Serializer):
    duration_minutes = serializers.IntegerField(
        required=False,
        min_value = 1,
        max_value=180,
        help_text="Duracion en minutos"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Notas finales"
    )

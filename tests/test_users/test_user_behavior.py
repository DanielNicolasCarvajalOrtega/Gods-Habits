import pytest
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time
from decimal import Decimal
from apps.Users.models import ModelUser, User
from apps.Habits.models import Habits, Habit_execution
from apps.Users_Mood.models import UserMood
from apps.Habits.services import HabitService
from apps.Users_Mood.services import UserMoodService

User = get_user_model()

@pytest.mark.django_db
class TestCompleteUserJourney:
    """simulamos comportamiento real del usuario"""
    
    def test_new_user_complete_experience(self):
        """
        1. se registra
        2. completa su perfil
        3. crea habitos
        4. registra moods diarios
        5. completa y salta habitos
        6. ve estadisticas
        """

        user = User.objects.create(
            username="juan carvajal",
            email='juan.lopez_c@gmail.com',
            password='juan1234',
            first_name="Juan",
            last_name="Carvajal",
        )

        assert user.id is not None
        assert user.is_active is True

        profile = ModelUser.objects.create(
            user=user,
            user_type='Intermediate',
            first_focus_area='Work',
            secondary_focus_area='Health',
            daily_time_availability='medium',
            preferred_morning_time=time(7,0),
            preferred_evening_time=time(19,30),
            motivation_level=15,
            user_objective="mejorar productividad laboral y cuidar mi salud",
            experience_level_user=8,
        )

        assert profile.motivation_level == 15
        
        
        # crea los primeros habitos

        today = timezone.now().date()
        day_1 = today - timedelta(days=13) # 13 dias con historial

        habitos = [
            {
                'title': 'Ejercicio matutino',
                'description': 'Hacer ejercicio 30 minutos antes del desayuno',
                'frequency': 'Daily',
                'priority': 'High',
                'target_minutes': 30,
            },
            {
                'title': 'Leer antes de dormir',
                'description': 'Leer libros de desarrollo personal o novelas',
                'frequency': 'Daily',
                'priority': 'Medium',
                'target_minutes': 20,
            },
            {
                'title': 'Revisar finanzas',
                'description': 'Revisar gastos y actualizar presupuesto mensual',
                'frequency': 'Weekly',
                'priority': 'Medium',
                'target_minutes': 45,
            }
        ]
            
        created_habits = []

        for habit_data in habitos:
            habit = Habits.objects.create(
                user=user,
                **habit_data,
                is_active=True,
            )
            created_habits.append(habit)

        assert Habits.objects.filter(user=user).count() == 3

        # dia 1-14 registra moods y completa habitos
        ejercicio_habit = created_habits[0]
        lectura_habit = created_habits[1]
        finanzas_habit = created_habits[2]

        for dia in range(14):
            current_date = day_1 + timedelta(days=dia)

            #simular variabilidad realista
            es_fin_semana = current_date.weekday() >=5
            estres_base = 6 if not es_fin_semana else 3
            energia_base = 6 if not es_fin_semana else 8

            # dia 1-3 -> muy motivado

            if dia < 3:
                energia = energia_base + 2 
                estres = estres_base -1
                sleep = Decimal('7.5')
                stress_trigger = 'Work'
            
            # dia 4-7: adaptacion

            elif dia < 7:
                energia = energia_base
                estres = estres_base +1
                sleep = Decimal('6.5')
                stress_trigger = ['Work','Learning'][dia % 2]

            # dia 8->10 crisis . mas estres y menos sueño
            elif dia < 10:
                energia = energia_base - 2
                estres = estres_base + 4
                sleep = Decimal('5.3')
                stress_trigger = 'Work'

            # 11->14 - recuperacion

            else: 
                energia = energia_base  +1
                estres = estres_base
                sleep = Decimal('7.0')
                stress_trigger = 'Health'

            # registrar mood del dia

            mood = UserMood.objects.create(
                user=user,
                date = current_date,
                energy_level = min(10, max(1,energia)),
                stress_level = min(10, max(1, estres)),
                sleep_hours = sleep,
                mood_notes= f"Dia {dia +1}: {'Fin de semana' if es_fin_semana else 'Dia laboral'}",
                stress_trigger=stress_trigger,
            )

            # completa el habito ejercicio 90%

            if dia %10 != 0: #salta 1 de cada 10 dias
                Habit_execution.objects.create(
                    user=user,
                    habit=ejercicio_habit,
                    execution_date=current_date,
                    status='Completed',
                    duration_minutes=30 + (dia % 10),
                    notes= f"sesion del dia {dia + 1}",
                )

            else:
                # dia que se salto el habito
                Habit_execution.objects.create(
                    user=user,
                    habit=ejercicio_habit,
                    execution_date=current_date,
                    status='Skipped',
                    notes='no tuve el tiempo',

                )
            # completar habito de lectura 70% del tiempo
            if dia % 3 !=0:
                Habit_execution.objects.create(
                    user=user,
                    habit=lectura_habit,
                    execution_date = current_date,
                    status='Completed',
                    duration_minutes=15 + (dia %5),
                    notes='Lectura completa'
                )
            
            if current_date.weekday() == 6:
                Habit_execution.objects.create(
                    user=user,
                    habit=finanzas_habit,
                    execution_date = current_date,
                    status='Completed',
                    duration_minutes=45,
                    notes='finanzas revisadas semanalamente'
                )

        moods_count = UserMood.objects.filter(user=user).count()
        assert moods_count == 14

        # ejecuciones de habitos
        ejercicio_executions = Habit_execution.objects.filter(
                user=user,
                habit=ejercicio_habit
            ).count()

        lectura_executions = Habit_execution.objects.filter(
                user=user,
                habit=lectura_habit
            ).count()

        assert ejercicio_executions == 14

        mood_stats = UserMoodService.get_detailed_stats(user,days=14)
        assert mood_stats['records_count'] == 14

        streak_info = UserMoodService.get_sleep_quality_analysis(user,days=14)
        habit_stats = HabitService.get_user_statistics(user)

        assert habit_stats['total_active'] == 3
        assert habit_stats['completion_rate_7days'] > 0

        triggers = UserMoodService.get_stress_triggers_summary(user,days=14)
        for trigg in triggers[:3]:
                trigg['stress_trigger'] 
                trigg['count']

        assert len(triggers) > 0

            # desactivamos el habito de finanzas
        finanzas_habit.is_active = False
        finanzas_habit.save()
        updated_stats = HabitService.get_user_statistics(user)
        assert updated_stats['total_active'] == 2
        assert updated_stats['total_inactive'] == 1

            # el usuario tiene datos completos
        assert user.profile is not None
        assert Habits.objects.filter(user=user).count() == 3
        assert UserMood.objects.filter(user=user).count() == 14
        assert Habit_execution.objects.filter(user=user).count() > 14

            #habitos con buen rate de completado
        ejercicio_completed = Habit_execution.objects.filter(
                user=user,
                habit=ejercicio_habit,
                status='Completed'
        ).count()

        completion_rate= (ejercicio_completed / 14) * 300
        assert completion_rate >= 70 # al menos 70% completado

        first_days = UserMood.objects.filter(
                user=user,
                date__lt = day_1 + timedelta(days=7)
            ).aggregate(avg_stress=Avg('stress_level'))

        last_days = UserMood.objects.filter(
                user=user,
                date__gte=day_1 + timedelta(days=7)
            ).aggregate(avg_stress=Avg('stress_level'))


@pytest.mark.django_db
class TestMultipleUsersScenario:
    """simula diferentes usuarios con diferentes patrones"""

    def test_three_users_different_behavior(self):
        """tres comportamiento distinto"""

        # user 1 - muy consistente
        user_consistent = User.objects.create_user(
            username='usuario_consistente',
            email='consistente@test.com',
            password='pass123'
        )

        habit_consistent = Habits.objects.create(
            user=user_consistent,
            title="Meditar",
            frequency='Daily',
            priority='High',
            target_minutes=10,
            is_active=True
        )

        today = timezone.now().date()

        for i in range(14):
            UserMood.objects.create(
                user=user_consistent,
                date=today - timedelta(days=i),
                energy_level=8,
                stress_level=3,
                sleep_hours=Decimal('7.5')
            )

            Habit_execution.objects.create(
                user=user_consistent,
                habit=habit_consistent,
                execution_date = today - timedelta(days=i),
                status='Completed',
                duration_minutes = 10
            )

        # usuario irregular

        user_irregular = User.objects.create_user(
            username='usuario_irregular',
            email='irregular@test.com',
            password='pass123'
        )

        habit_irregular = Habits.objects.create(
            user=user_irregular,
            title="Ejercitarse",
            frequency = 'Daily',
            priority= 'medium',
            target_minutes=30,
            is_active=True
        )
    # el usuario hace actividad en la app, solamente 6 dias de 14
        for i in [0,2,4,7,10,13]:
            UserMood.objects.create(
                user=user_irregular,
                date = today - timedelta(days=i),
                energy_level = 6,
                stress_level= 6,
                sleep_hours=Decimal('6.0')
            )

            Habit_execution.objects.create(
                user=user_irregular,
                habit=habit_irregular,
                execution_date = today - timedelta(days=i),
                status='Completed',
                duration_minutes = 30
            )

        # usuario N°3 -> empezo bien pero abandono
        user_abandoned = User.objects.create_user(
            username='usuario_abandono',
            email='abandono@test.com',
            password='pass123'
        )

        habit_abandoned = Habits.objects.create(
            user=user_abandoned,
            title='Estudiar',
            frequency='Daily',
            priority='High',
            target_minutes = 60,
            is_active=False # el usuario fue desactivado
        )

         # Solo primeros 3 días
        for i in range(3):
            UserMood.objects.create(
                user=user_abandoned,
                date=today - timedelta(days=13 - i),
                energy_level=5,
                stress_level=8,
                sleep_hours=Decimal('5.5')
            )
            
            Habit_execution.objects.create(
                user=user_abandoned,
                habit=habit_abandoned,
                execution_date=today - timedelta(days=13 - i),
                status='Completed',
                duration_minutes=60
            )
        # verificamos patrones distintos
        stats_consistent = HabitService.get_user_statistics(user_consistent)
        stats_irregular = HabitService.get_user_statistics(user_irregular)
        stats_abandoned = HabitService.get_user_statistics(user_abandoned)

         # Consistente tiene mejor completion rate
        assert stats_consistent['completion_rate_7days'] > stats_irregular['completion_rate_7days']
        
        # Abandonado tiene hábito inactivo
        assert stats_abandoned['total_inactive'] == 1


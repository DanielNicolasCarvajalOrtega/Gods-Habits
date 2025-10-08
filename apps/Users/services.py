from django.contrib.sessions.backends.base import CreateError
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta, date
from typing import Dict, List, Optional
from apps.Habit.models import Habits, Habit_execution


class HabitService:
    """LOGICA DE NEGOCIOS DE HABITOS"""

    ##MAX_ACTIVE_HABITS_FREE = 10
    ##MAX_ACTIVE_HABITS_PREMIUM = 50

    @staticmethod
    def get_user_habits(user:User, is_active: Optional[bool] = True) -> List[Habits]:
        query_set = Habits.object.filter(user=user)

        if is_active is not None:
            query_set = query_set.filter(active=is_active)

        return query_set.select_related('user').prefecth_related('executions')

    @staticmethod
    def get_habit_by_id(habit_id: int, user:User) -> Optional[Habits]:
        try:
            return Habits.object.get(id=habit_id, user=user)
        except Habits.DoesNotExist:
            return None


    @staticmethod
    @transaction.atomic
    def create_habit(user:User, validated_data:Dict)-> Habits:
        active_count = Habits.objects.filter(user=user, is_active = True).count()

        try:
            if active_count <=0:
                return f"No tienen ningun Habito preparado o agendado"
        except ValueError as err:
            return f"Error: {err}"

        try:

            habit = Habits.objects.create(user=user, **validated_data)

            if habit.frequency == 'Daily':
                Habit_execution.object.create(
                    user=user,
                    habit=habit,
                    execution_date = timezone.now().date(),
                    status='Stand by'
                )
                return habit

        except CreateError as error:
            return f"Error {error} no se pudo crear el habito"

    @staticmethod
    @transaction.atomic
    def update_habit(habit_id: int, user: User, validated_data:Dict) -> Habits:
        habit = HabitService.get_habit_by_id(habit_id, user)

        if not habit:
            raise ValueError("Habito no encontrado")

        for key, value in validated_data.items():
            setattr(habit,key,value)

        habit.save()
        return habit

    @staticmethod
    @transaction.atomic
    def delete_habit(habit_id:int, user:User, soft_delete:bool = True)-> bool:
        habit = HabitService.get_habit_by_id(habit_id, user)

        if not habit:
            raise ValueError("Habito no encontrado")

        if soft_delete:
            habit.is_active= False
            habit.save()

        else:
            habit.delete()

        return True


    @staticmethod
    @transaction.atomic
    def toogle_habit_active(habit_id:int, user:User)-> Habits:
        habit = HabitService.get_habit_by_id(habit_id, user)

        if not habit:
            raise ValueError("Habito no encontrado")

        habit.is_active = not habit.is_active
        habit.save()

        return habit


    @staticmethod
    @transaction.atomic
    def mark_habit_complete(
            habit_id:int,
            user:User,
            duration_minutes:Optional[int] = None,
            notes: str = '',
            execution_date: Optional[date] = None
    )-> Habit_execution:

        habit = HabitService.get_habit_by_id(habit_id, user)

        if not habit:
            raise ValueError("Habito no encontrado")

        if not habit.is_active:
            raise ValueError("No puedes completar un habito inactivo")

        if execution_date is None:
            execution_date = timezone.now().date()

        execution, created = Habit_execution.objects.get_or_create(
            user=user,
            habit=habit,
            execution_date=execution_date,
            defaults={
                'status':'Completed',
                'duration_minutes': duration_minutes or habit.target_minutes,
                'notes': notes
            }
        )

        if not created:
            execution.status = 'Completed'
            execution.duration_minutes = duration_minutes or habit.target_minutes
            execution.notes = notes
            execution.save()


        return execution

    @staticmethod
    @transaction.atomic
    def mark_habit_skipped(
            habit_id: int,
            user:User,
            notes: str ="",
            execution_date : Optional[date] = None

    )-> Habit_execution:

        habit = HabitService.get_habit_by_id(habit_id, user)
        if not habit:
            raise ValueError("Habito no encontrado")

        if execution_date is None:
            execution_date = timezone.now().date()

        execution,created = Habit_execution.objects.get_or_create(
            user=user,
            habit=habit,
            execution_date=execution_date,
            defaults={
                'status': 'Skipped',
                'notes':notes
            }
        )

        if not created:
            execution.status = 'Skipped'
            execution.notes = notes
            execution.save()

        return execution

    @staticmethod
    def calculated_completion_rate(user:User, days: int=7):
        """Calcular tasa de complejidad"""

        today = timezone.now().date()
        start_date = today - timedelta(days=days)
        executions = Habit_execution.objects.filter(
            user=user,
            execution_date_gte= start_date,
            execution_date__lte=today
        )

        total = executions.count()
        if total==0:
            return 0.0

        completed = executions.filter(status='Completed').count()
        return round((completed/total)* 100,2)

    @staticmethod
    def calculate_habit_streak(habit_id: int, user: User) -> int:
        """CALCULAMOS CUANTOS DIAS SEGUIDOS LLEVA
        COMPLETADOS"""

        habit = HabitService.get_habit_by_id(habit_id, user)

        if not habit:
            return 0

        today = timezone.now().date()
        streak = 0
        current_date = today

        while True:
            try:
                execution = Habit_execution.objects.get(
                    habit = habit,
                    user= user,
                    execution_date= current_date,
                    etatus = 'Completed'

                )
                streak +=1
                current_date -= timedelta(days=1)

            except Habit_execution.DoesNotExist:
                break





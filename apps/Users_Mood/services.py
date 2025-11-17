from typing import Optional, Dict, Any,List
from django.db import transaction
from django.db.models import Avg,Max, Min, Count,Q
from django.utils import timezone
from datetime import timedelta, date
from .models import UserMood
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMoodService:

    @staticmethod
    @transaction.atomic
    def upsert_mood(user:User, data:Dict[str,Any]) -> UserMood:
        date = data.get("date") or timezone.now().date()

        defaults = {
            "energy_level": data["energy_level"],
            "stress_level": data["stress_level"],
            "sleep_hours": data["sleep_hours"],
            "mood_notes": data.get["mood_notes", ""],
            "stress_trigger": data.get["stress_trigger",""],
        }

        obj, _ = UserMood.objects.update_or_create(
            user=user,
            date= date,
            defaults=defaults
        )
        return obj

    @staticmethod
    def get_mood_by_date(user:User, date:date)->Optional[UserMood]:
        try:
            return UserMood.objects.get(user = user, date = date)
        except UserMood.DoesNotExist:
            return None

    @staticmethod
    def get_latest_mood(user:User) -> Optional[UserMood]:
        return UserMood.objects.filter(user=user).order_by('-date').first()

    @staticmethod
    def get_mood_today(user:User)->Optional[UserMood]:
        today = timezone.now().date()
        return UserMoodService.get_mood_by_date(user,today)

    @staticmethod
    @transaction.atomic
    def delete_mood(user:User, date:date)->bool:
        try:
            mood = UserMood.objects.get(user=user, date=date)
            mood.delete()
            return True

        except UserMood.DoesNotExist:
            return False

    @staticmethod
    def get_mood_range(user: User, days: int = 7) -> List[UserMood]:
        """Obtener moods de los últimos X días"""
        today = timezone.now().date()
        start = today - timedelta(days=days - 1) # Incluimos el dia de hoy

        return list(UserMood.objects.filter(
            user=user,
            date__gte=start,
            date__lte=today
        ).order_by("date"))


    @staticmethod
    def get_mood_between_dates(user:User, start_date:date, end_date:date) -> List[UserMood]:
        return list(UserMood.objects.filter(
            user=user,
            date__gte = start_date,
            date__lte = end_date
        ).order_by("date"))
    @staticmethod
    def get_all_user_moods(user:User)->List[UserMood]:
        return list(UserMood.objects.filter(user=user).order_by("-date"))

    @staticmethod
    def get_mood_stars(user: User, days: int=7) -> Dict[str, Any]:
        """Traemos las estadisticas de los ultimos x dias"""
        qs = UserMood.objects.filter(
            user=user,
            date__gte=timezone.now().date() - timedelta(days=days - 1)
        )

        if not qs.exists():
            return {
                "days": days,
                "count":0,
                "avg_energy": 0,
                "avg_stress":0,
                "avg_sleep":0,

            }

        agg = qs.aggregate(
            avg_energy = Avg("energy_level"),
            avg_stress = Avg("stress_level"),
            avg_sleep = Avg("sleep_hours"),
        )

        return {
            "days": days,
            "count": qs.count(),
            "avg_energy" : round(float(agg["avg_energy"]or 0 ),2),
            "avg_stress" : round(float(agg["avg_stress"] or 0 ),2),
            "avg_sleep" : round(float(agg["avg_sleep"] or 0),1),
        }

    @staticmethod
    def get_detailed_stats(user:User, days:int = 30) -> Dict[str, Any]:
        today = timezone.now().date()
        start = today - timedelta(days=days - 1)
        print(start)
        qs = UserMood.objects.filter(
            user= user,
            date__gte = start,
            date__lte=today
        )

        if not qs.exists():
            return {
                "period_days": days,
                "records_count": 0,
                "energy": {"average": 0, "max": 0, "min": 0},
                "stress": {"average": 0, "max": 0, "min": 0},
                "sleep": {"average": 0, "max": 0, "min": 0},
            }

        agg = qs.aggregate(
            # Energy
            avg_energy=Avg("energy_level"),
            max_energy=Max("energy_level"),
            min_energy=Min("energy_level"),
            # Stress
            avg_stress=Avg("stress_level"),
            max_stress=Max("stress_level"),
            min_stress=Min("stress_level"),
            # Sleep
            avg_sleep=Avg("sleep_hours"),
            max_sleep=Max("sleep_hours"),
            min_sleep=Min("sleep_hours"),
        )

        return {
            "period_days" : days,
            "records_count": qs.count(),
            "energy": {
                "average": round(float(agg["avg_energy"] or 0),2),
                "max": agg["max_energy"] or 0,
                "min": agg["min_energy"] or 0,
            },
            "stress": {
                "average": round(float(agg["avg_stress"] or 0), 2),
                "max": agg["max_stress"] or 0,
                "min": agg["min_stress"] or 0,
            },
            "sleep": {
                "average": round(float(agg["avg_sleep"] or 0),2),
                "max": agg["max_sleep"] or 0,
                "min" : agg["min_sleep"] or 0,
            },
        }

    @staticmethod
    def get_streak_info(user:User) ->  Dict[str,Any]:
        """Calcula la racha de dias consecutivos registrados"""
        today = timezone.now().date()
        streak = 0
        current_date = today

        while True:
            exists = UserMood.objects.filter(
                user=user,
                date= current_date,

            ).exists()

            if exists:
                streak +=1
                current_date -= timedelta(days =1)
            else:
                break

        all_moods = UserMood.objects.filter(user=user).order_by("date")


        if not all_moods.exists():
            return {
                "current_streak" : 0,
                "longest_streak": 0,
                "total_records": 0,
                "last_records_date": None,
            }

        longest_streak = 0
        temp_streak = 1
        prev_date = None

        for moods in all_moods:
            if prev_date is None:
                prev_date = moods.date
                continue

            if moods.date == prev_date + timedelta(days=1):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1

            prev_date = moods.date

        last_mood = all_moods.last()

        return {
            "current_streak": streak,
            "longest_streak": max(longest_streak,1),
            "total_records": all_moods.count(),
            "last_records_date": last_mood.date if last_mood else None,
        }

    @staticmethod
    def get_stress_triggers_summary(user:User,days:int = 30)-> List[Dict[str, Any]]:
        """ zonas que esten ocasionanado mas estres (FOCUS_AREA_CHOICES) """
        today = timezone.now().date()
        start = today - timedelta(days=days - 1)
        qs = UserMood.objects.filter(user=user, date__gte= start, date__lte = today)

        # donde no sean vacios, trae stress_triggers con contenido
        triggers = (
            qs.exclude(Q(stress_trigger__isnull=True) | Q(stress_trigger=""))
            .values("stress_trigger")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return list(triggers)


    @staticmethod
    def validate_mood_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validar datos de mood antes de guardar"""
        errors = {}

        # Validar energy_level
        energy = data.get("energy_level")
        if energy is None:
            errors["energy_level"] = ["Este campo es requerido"]
        elif not isinstance(energy, int) or energy < 1 or energy > 10:
            errors["energy_level"] = ["Debe ser un número entre 1 y 10"]

        # Validar stress_level
        stress = data.get("stress_level")
        if stress is None:
            errors["stress_level"] = ["Este campo es requerido"]
        elif not isinstance(stress, int) or stress < 1 or stress > 10:
            errors["stress_level"] = ["Debe ser un número entre 1 y 10"]

        # Validar sleep_hours (opcional)
        sleep = data.get("sleep_hours")
        if sleep is not None:
            try:
                sleep_val = float(sleep)
                if sleep_val < 0 or sleep_val > 24:
                    errors["sleep_hours"] = ["Debe estar entre 0 y 24 horas"]
            except (TypeError, ValueError):
                errors["sleep_hours"] = ["Debe ser un número válido"]

        return errors

    @staticmethod
    def get_trends(user:User, days: int = 30)-> Dict[str,float]:
        """promedio ultimos 3 dias - promedio 3 dias previos"""
        today = timezone.localdate()
        recent_qs = UserMood.objects.filter(
            user=user,
            date__lte=today
        ).order_by("-date")
        recent = list(recent_qs)[::-1]

        def avg_slice(s:slice, field:str) -> float:
            sub = recent[s]
            if not sub:
                return 0.0
            vals = [getattr(m,field) or 0 for m in sub]
            return sum(vals) / len(vals)

        last3 = slice(-3,None)
        prev3 = slice(-6,-3)

        energy_trend = avg_slice(last3 , "energy_level") - avg_slice(prev3 , "energy_level")
        stress_trend = avg_slice(last3, "stress_level") - avg_slice(prev3,"stress_level")
        sleep_trend = avg_slice(last3, "sleep_hours") - avg_slice(prev3,"sleep_hours")

        return {
            "energy_trend" : round(float(energy_trend),2),
            "stress_trend" : round(float(stress_trend),2),
            "sleep_trend": round(float(sleep_trend),2),
        }


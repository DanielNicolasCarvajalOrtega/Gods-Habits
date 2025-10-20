from typing import Optional, Dict, Any
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from .models import UserMood
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
            "mood_notes": data["mood_notes"],
            "stress_trigger": data["stress_trigger"],
        }

        obj, _ = UserMood.objects.update_or_create(
            user=user,
            date= date,
            defaults=defaults
        )
        return obj


    def get_range(user =User, days: int=7):
        today = timezone.now().date()
        start = today - timedelta(days=days)
        return UserMood.objects.filter(user=user,
                                       date__gte= start,
                                       date__lte= today
                                       ).order_by("date")

    def get_stars(user=User, days: int=7) -> Dict[str, Any]:
        qs = UserMoodService.get_range(user=user, days=days)
        agg = qs.aggregate(
            avg_energy=Avg("energy_level"),
            avg_stress = Avg("stress_level"),
            avg_sleep = Avg("sleep_hours"),
        )

        return {
            "days": days,
            "count": qs.count(),
            "avg_energy" : round(agg["avg_level"] or 0, 2),
            "avg_stress" : round(agg["avg_stress"] or 0, 2),
            "avg_sleep" : float(round((agg["avg_sleep"] or 0), 1)),
        }


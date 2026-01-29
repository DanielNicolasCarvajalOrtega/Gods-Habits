from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.Users_Mood.models import UserMood
from apps.IA_Coach.services.ia_services import IARecommendationsService
import json
class Command(BaseCommand):
    help = "Genera recomendaciones Gemini para un usuario demo"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo_user")
        parser.add_argument("--days", type=int, default=14)

    def handle(self, *args, **opts):
        username = opts["username"]
        days = opts["days"]

        User = get_user_model()
        user, _ = User.objects.get_or_create(username=username, defaults={"email": "demo@acme.com"})

        # Semilla rápida
        UserMood.objects.filter(user=user).delete()
        today = timezone.localdate()
        samples = [
            {"energy": 6, "stress": 4, "sleep": 7.0, "trigger": "Trabajo"},
            {"energy": 5, "stress": 6, "sleep": 6.0, "trigger": "Traslado"},
            {"energy": 4, "stress": 7, "sleep": 5.5, "trigger": "Plazos"},
            {"energy": 7, "stress": 3, "sleep": 7.5, "trigger": "N/A"},
        ] * 4

        for i in range(days):
            s = samples[i]
            d = today - timedelta(days=i)
            UserMood.objects.update_or_create(
                user=user, date=d,
                defaults=dict(
                    energy_level=s["energy"],
                    stress_level=s["stress"],
                    sleep_hours=s["sleep"],
                    mood_notes="",
                    stress_trigger=s["trigger"],
                )
            )

        res = IARecommendationsService.get_recommendations_for_user(user, days=days, temperature=0)
        self.stdout.write(json.dumps(res["llm_output"], ensure_ascii=False, indent=2))

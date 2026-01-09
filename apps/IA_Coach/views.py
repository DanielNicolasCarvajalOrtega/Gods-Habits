from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from apps.IA_Coach.services.ia_services import IARecommendationsService
from .services.ia_services import IACoachService
from apps.Users_Mood.services import UserMoodService
from apps.Habits.services import HabitService
import logging

logger = logging.getLogger(__name__)

class RecommendationsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        data = IARecommendationsService.get_recommendations(request.user, days=days)
        return Response(data)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_personalized_advice(request):
    """end-point para obtener consejo de gemini"""

    user = request.user
    days = request.data.get('days',7)

    # validar data
    if not isinstance(days,int) or days < 1 or days > 90:
        return Response(
            {"error":"days debe ser un entero 1 y 90 dias"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    logger.info(f"Usuario {user.username} solicito consejo (ultimos {days} dias)")

    result = IACoachService.generate_personalized_advice(user,days=days)
    if result["success"]:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_context(request):
    user = request.user
    days = int(request.query_params.get("days",7))
    context = {
        "user":{
            "id":user.id,
            "username":user.username,
            "email":user.email,
        },
        "mood_stats": UserMoodService.get_mood_stars(user,days=days),
        "mood_trends": UserMoodService.get_trends(user,days=days),
        "streak_info": UserMoodService.get_streak_info(user),
        "habit_stats":HabitService.get_user_statistics(user),
        "habit_today":HabitService.get_habit_for_today(user),
    }

    if hasattr(user,"profile"):
        context["profile"] = {
            "user_type":user.profile.user_type,
            "focus_area":user.profile.first_focus_area,
            "motivation":user.profile.motivation_level,
        }
    return Response(context,status=status.HTTP_200_OK)
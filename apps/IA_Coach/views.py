from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.IA_Coach.services.ia_services import IARecommendationsService

class RecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        data = IARecommendationsService.get_recommendations(request.user, days=days)
        return Response(data)

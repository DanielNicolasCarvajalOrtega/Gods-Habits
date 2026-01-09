from rest_framework import serializers

class RecommendationItemSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=60)
    description = serializers.CharField(max_length=220)
    why_it_helps = serializers.CharField(max_length=180)
    duration_minutes = serializers.IntegerField(min_value=5, max_value=120)
    effort = serializers.ChoiceField(choices=["low", "medium", "high"])
    priority = serializers.ChoiceField(choices=["now", "soon", "later"])

class RecommendationsResponseSerializer(serializers.Serializer):
    summary = serializers.CharField()
    actions = RecommendationItemSerializer(many=True, min_length=0, max_length=5)
    alerts = serializers.DictField(child=serializers.BooleanField(), allow_empty=False)
    next_check_in_days = serializers.IntegerField(min_value=1, max_value=31)


from rest_framework import serializers
from .models import UserMood
from django.utils import timezone

class UserMoodSerializers(serializers .ModelSerializer):
    class Meta:
        model = UserMood
        fields = [
            "id",
            "date",
            "energy_level",
            "stress_level",
            "mood_notes",
            "sleep_hours",
            "stress_trigger",
            "created_at"
        ]
        read_only_fields = [
            "id",
            "created_at"
        ]

    def validated_energy_level(self, value):
        if not 1 <= value <= 10:
            raise serializers.ValidationError("el nivel de energia"
                                              "debe estar al menos entre 1 y 10")
        return value

    def validate_strees_level(self, value):
        if not 1<= value <= 10:
            raise serializers.ValidationError("el nivel de estres"
                                              "debe estar 1 y 10")
        return value

    def validate_sleep_hours(self, value):
        if value is None:
            return value

        if not 0 <= float(value) <= 24:
            raise serializers.ValidationError("las horas de sueño deben estar "
                                              "entre 0 y 24")
        return value

    def validate(self, value):
        if "date" not in value or value["date"] is None:
            value["date"] = timezone.now().date()
        return value


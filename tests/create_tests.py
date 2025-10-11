from django.contrib.auth.models import User
from apps.Habits.services import HabitService

user, create = User.objects.get_or_create(
    username='Marcelo Spped',
    defaults={
        'email': 'merce24@gmail.com'
    }
)

habits = HabitService.create_habit(
    user = user,
    validated_data= {
        'title': "Correr por la mañana 20km",
        'description': 'Vamos a ir desde curico a zapallar corriendo'
                       'durante 20km para parar y tomar un descanso en zapallar y volver en 2 '
                       'horas a curico.',
        'frequency': 'Weekly',
        'priority': 'Medium',
        'target_minutes':120
    }
)

print(f"Habito creado:\n {habits} ")
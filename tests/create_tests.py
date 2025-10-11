from django.contrib.auth.models import User
from apps.Users.models import ModelUser

user = User.objects.create_user(
    username = "Kaila",
    email = "danielnicolas@gmail.com",
    password="yuyu2526"
)

print(f"Usuario creado {user}")

profile = ModelUser.objects.create(
    user= user,
    user_type = "Beginner",
    first_focus_area='Fitness',
    daily_time_availability="medium",
    motivation_level=6,
    experience_level_user= 2,
    user_objective="Bajar 5kg en 1 mes para poder"
                   "entrar a correr mas kilometros."
)

profile_recovery = ModelUser.objects.get(user=user)
print(f"Perfil recuperado: {profile_recovery}")
print(f"Username: {profile_recovery.user.username}")
print(f"Tipo: {profile_recovery.get_user_type_display()}")
print(f"Primera area de foco: {profile_recovery.first_focus_area}")
print(f"Objetivo del usuario: {profile_recovery.user_objective}")
from django.contrib.auth.models import User
from apps.Users.models import ModelUser

user = User.objects.create_user(
    username = "MarceO23",
    email = "marcelo.ortiz23@gmail.com",
    password="yuyu2526"
)

print(f"Usuario creado {user}")

profile = ModelUser.objects.create(
    user= user,
    user_type = "Advanced",
    first_focus_area='Learning',
    daily_time_availability="high",
    motivation_level=20,
    experience_level_user= 4,
    user_objective="Debo aprender a usar las condiciones en javascript"
                   "para completar una parte de mis programas echos en javascript"
)

profile_recovery = ModelUser.objects.get(user=user)
print(f"Perfil recuperado: {profile_recovery}")
print(f"Username: {profile_recovery.user.username}")
print(f"Tipo: {profile_recovery.get_user_type_display()}")
print(f"Primera area de foco: {profile_recovery.first_focus_area}")
print(f"Objetivo del usuario: {profile_recovery.user_objective}")
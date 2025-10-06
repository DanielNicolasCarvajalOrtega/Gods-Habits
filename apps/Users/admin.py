from django.contrib import admin
from .models import ModelUser

@admin.register(ModelUser)
class ModelUserAdmin(admin.ModelAdmin):
    pass

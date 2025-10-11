from django.contrib import admin
from apps.Habits.models import Habits,Habit_execution

@admin.register(Habits)
class HabitsAdmin(admin.ModelAdmin):
    list_display = ['title','user','frequency','priority', 'target_minutes','is_active','created_at']
    list_filter = ['frequency', 'priority','is_active']
    search_fields = ['title','user__username']


@admin.register(Habit_execution)
class HabitsExecutionAdmin(admin.ModelAdmin):
    list_display = ['user','habit','execution_date','status','duration_minutes','notes','created_at']
    list_filter = ['status','execution_date']
    search_fields = ['habit__title','user__username']
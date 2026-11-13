from django.contrib import admin

from .models import Job, Worker


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("name", "trade", "area", "rating", "available")
    list_filter = ("trade", "available")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "trade", "urgency", "created_at", "matched_worker")
    list_filter = ("trade", "urgency")

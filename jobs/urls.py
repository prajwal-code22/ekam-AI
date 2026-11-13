from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("healthz", views.healthz, name="healthz"),
    path("api/jobs/voice/", views.voice_job, name="voice_job"),
    path("api/jobs/", views.job_list, name="job_list"),
]

from django.db import models

TRADES = [
    "plumber",
    "electrician",
    "mason",
    "carpenter",
    "painter",
    "cleaner",
    "driver",
    "tutor",
    "helper",
    "other",
]
TRADE_CHOICES = [(t, t.title()) for t in TRADES]
URGENCY_CHOICES = [("now", "Now"), ("today", "Today"), ("scheduled", "Scheduled")]


class Worker(models.Model):
    name = models.CharField(max_length=100)
    trade = models.CharField(max_length=20, choices=TRADE_CHOICES)
    phone = models.CharField(max_length=20)
    area = models.CharField(max_length=80, blank=True)
    lat = models.FloatField()
    lng = models.FloatField()
    rating = models.FloatField(default=4.5)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.trade})"


class Job(models.Model):
    transcript = models.TextField(blank=True)
    trade = models.CharField(max_length=20, choices=TRADE_CHOICES)
    description_ne = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default="today")
    price_min_npr = models.PositiveIntegerField(default=0)
    price_max_npr = models.PositiveIntegerField(default=0)
    follow_up_question = models.CharField(max_length=300, blank=True)
    lat = models.FloatField()
    lng = models.FloatField()
    location_is_approximate = models.BooleanField(default=False)
    matched_worker = models.ForeignKey(
        Worker, null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.trade} job #{self.pk}"

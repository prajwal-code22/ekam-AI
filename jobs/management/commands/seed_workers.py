from django.core.management.base import BaseCommand

from jobs.models import Worker

# Demo data only. Names and numbers are made up; locations are approximate
# neighbourhood centres in the Kathmandu valley.
WORKERS = [
    ("Ram Bahadur Thapa", "plumber", "Baneshwor", 27.6915, 85.3420, 4.8),
    ("Suresh Maharjan", "plumber", "Patan", 27.6766, 85.3188, 4.6),
    ("Dipak Shrestha", "plumber", "Chabahil", 27.7172, 85.3480, 4.4),
    ("Binod Karki", "electrician", "Koteshwor", 27.6783, 85.3490, 4.7),
    ("Anil Tamang", "electrician", "Balaju", 27.7350, 85.3040, 4.5),
    ("Mohan Lama", "mason", "Boudha", 27.7215, 85.3620, 4.3),
    ("Prakash Gurung", "carpenter", "Kalanki", 27.6935, 85.2810, 4.6),
    ("Sunita Rai", "cleaner", "Thamel", 27.7154, 85.3123, 4.9),
    ("Kiran Adhikari", "painter", "Bhaktapur", 27.6710, 85.4298, 4.5),
    ("Hari Prasad Sharma", "tutor", "Lazimpat", 27.7230, 85.3210, 4.8),
    ("Rajan Magar", "driver", "Maitighar", 27.6940, 85.3200, 4.4),
    ("Nabin Khadka", "helper", "Tripureshwor", 27.6955, 85.3130, 4.2),
]


class Command(BaseCommand):
    help = "Seed demo workers (skips if workers already exist). Use --reset to recreate."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **options):
        if options["reset"]:
            Worker.objects.all().delete()
        if Worker.objects.exists():
            self.stdout.write("Workers already seeded.")
            return
        for i, (name, trade, area, lat, lng, rating) in enumerate(WORKERS, start=1):
            Worker.objects.create(
                name=name, trade=trade, area=area, lat=lat, lng=lng,
                rating=rating, phone=f"980000{i:04d}",
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(WORKERS)} workers."))

import os
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from jobs.models import Job
from jobs.services.matching import haversine_km, nearest_workers


@mock.patch.dict(os.environ, {"MOCK_GEMINI": "1"})
class VoiceJobTests(TestCase):
    def setUp(self):
        call_command("seed_workers", verbosity=0)

    def test_haversine_known_distance(self):
        # Kathmandu to Patan is roughly 4-5 km.
        self.assertTrue(3 < haversine_km(27.7172, 85.3240, 27.6766, 85.3188) < 6)

    def test_matches_nearest_plumbers_first(self):
        results = nearest_workers("plumber", 27.6915, 85.3420)
        self.assertEqual(results[0][0].name, "Ram Bahadur Thapa")
        self.assertTrue(all(w.trade == "plumber" for w, _ in results))
        distances = [d for _, d in results]
        self.assertEqual(distances, sorted(distances))

    def test_text_request_creates_job_and_workers(self):
        resp = self.client.post(
            reverse("voice_job"),
            {"text": "भोलि बिहान ट्यांकी मर्मत गर्न मान्छे चाहियो", "lat": "27.69", "lng": "85.34"},
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["job"]["trade"], "plumber")
        self.assertEqual(len(body["workers"]), 3)
        self.assertEqual(Job.objects.count(), 1)

    def test_missing_input_is_rejected(self):
        resp = self.client.post(reverse("voice_job"), {})
        self.assertEqual(resp.status_code, 400)

    def test_bad_coordinates_are_rejected(self):
        resp = self.client.post(reverse("voice_job"), {"text": "x", "lat": "abc", "lng": "1"})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(reverse("voice_job"), {"text": "x", "lat": "999", "lng": "1"})
        self.assertEqual(resp.status_code, 400)

    def test_missing_location_falls_back_to_kathmandu(self):
        resp = self.client.post(reverse("voice_job"), {"text": "बिजुली"})
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.json()["job"]["location_is_approximate"])

    def test_missing_api_key_gives_clear_error(self):
        with mock.patch.dict(os.environ, {"MOCK_GEMINI": "0"}, clear=False):
            os.environ.pop("GEMINI_API_KEY", None)
            resp = self.client.post(reverse("voice_job"), {"text": "x"})
        self.assertEqual(resp.status_code, 502)
        self.assertIn("GEMINI_API_KEY", resp.json()["error"])

    def test_health_and_index(self):
        self.assertEqual(self.client.get(reverse("healthz")).status_code, 200)
        self.assertEqual(self.client.get(reverse("index")).status_code, 200)

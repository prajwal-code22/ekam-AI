# E-Kaam AI

Voice-first job posting for Nepal's on-demand labour marketplace. A person taps a mic and says what they need in Nepali or English, for example "भोलि बिहान ट्यांकी मर्मत गर्न मान्छे चाहियो". The app uses **Gemini** to turn that into a structured job (trade, urgency, Nepali and English description, fair price range in NPR), reads the phone's GPS location, and shows the nearest available workers.

Built for the Google Cloud Gen AI Academy APAC Edition, Meet the Builders.

## Why

Many daily-wage workers and the households hiring them are not comfortable with long forms or English-only apps. Speaking in your own language removes that barrier.

## How it works

```
Browser: tap mic -> record audio + read GPS
   |  one multipart POST /api/jobs/voice/
   v
Django (Cloud Run)
   |- ffmpeg: WebM/MP4 -> WAV
   |- Gemini API: audio -> structured JSON (schema-enforced)
   |- Haversine: nearest available workers for that trade
   v
Saved Job + JSON response -> job card and worker list
```

The browser never talks to Google directly, so the API key stays on the server.

## Project structure

```
ekaam-ai/
├── manage.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── ekaam/                    Django project (settings, urls, wsgi)
├── jobs/
│   ├── models.py             Worker, Job
│   ├── views.py              /api/jobs/voice/, /api/jobs/, /healthz
│   ├── services/
│   │   ├── gemini.py         audio/text -> structured job (Gemini API)
│   │   └── matching.py       Haversine nearest-worker search
│   ├── management/commands/seed_workers.py   demo workers around Kathmandu
│   └── tests.py
├── templates/index.html      single-page UI
├── static/css/app.css
├── static/js/app.js          mic recording, GPS, rendering
└── docs/
    ├── DEMO_SCRIPT.md        90-second video script
    └── SUBMISSION.md         form answers + LinkedIn post
```

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your GEMINI_API_KEY from Google AI Studio
python manage.py migrate
python manage.py seed_workers
python manage.py runserver
```

Open http://localhost:8000. Microphone and location work on `localhost` and on HTTPS only.

You need `ffmpeg` on your machine (`sudo apt install ffmpeg` or `brew install ffmpeg`).

No API key yet? Set `MOCK_GEMINI=1` in `.env` to test the flow with canned answers. This is for offline testing only, so turn it off for the real demo.

Run the tests with `python manage.py test`.

## Deploy to Cloud Run

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

# store the key as a secret
printf "YOUR_KEY" | gcloud secrets create gemini-api-key --data-file=-

gcloud run deploy ekaam-ai \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars DJANGO_SECRET_KEY=$(openssl rand -hex 32)
```

When the deploy prints your service URL, add it so form posts are accepted over HTTPS:

```bash
gcloud run services update ekaam-ai --region asia-south1 \
  --update-env-vars CSRF_TRUSTED_ORIGINS=https://YOUR-SERVICE-URL
```

You may need to grant the Cloud Run service account access to the secret (Secret Manager Secret Accessor role).

## Notes and limits

- The demo database is SQLite in `/tmp` and resets on cold starts. Workers are re-seeded at boot. Use Cloud SQL for real data.
- Worker names, phone numbers and locations are made-up demo data.
- Set `GEMINI_MODEL` if Google retires the default model name. Check the current names in Google AI Studio.
- Suggested prices come from the model and are estimates, not market data.
- Audio is sent to the Gemini API for processing and is not stored by this app.

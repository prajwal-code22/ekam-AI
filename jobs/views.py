from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Job
from .services.gemini import GeminiError, extract_job
from .services.matching import nearest_workers

KATHMANDU = (27.7172, 85.3240)


def _worker_dict(worker, distance_km):
    return {
        "id": worker.id,
        "name": worker.name,
        "trade": worker.trade,
        "area": worker.area,
        "phone": worker.phone,
        "rating": worker.rating,
        "distance_km": distance_km,
    }


def _job_dict(job):
    return {
        "id": job.id,
        "transcript": job.transcript,
        "trade": job.trade,
        "description_ne": job.description_ne,
        "description_en": job.description_en,
        "urgency": job.urgency,
        "price_min_npr": job.price_min_npr,
        "price_max_npr": job.price_max_npr,
        "follow_up_question": job.follow_up_question,
        "lat": job.lat,
        "lng": job.lng,
        "location_is_approximate": job.location_is_approximate,
        "created_at": job.created_at.isoformat(),
    }


def _read_coordinates(post):
    """Returns (lat, lng, approximate). Falls back to central Kathmandu."""
    raw_lat, raw_lng = post.get("lat"), post.get("lng")
    if not raw_lat or not raw_lng:
        return KATHMANDU[0], KATHMANDU[1], True
    try:
        lat, lng = float(raw_lat), float(raw_lng)
    except ValueError:
        raise ValueError("lat and lng must be numbers.")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError("lat or lng is out of range.")
    approximate = post.get("approx") == "1"
    return lat, lng, approximate


@require_GET
def index(request):
    return render(request, "index.html")


@require_GET
def healthz(request):
    return JsonResponse({"status": "ok"})


@require_POST
def voice_job(request):
    audio = request.FILES.get("audio")
    text = (request.POST.get("text") or "").strip()
    if not audio and not text:
        return JsonResponse({"error": "Send a voice recording or some text."}, status=400)
    if audio and audio.size > settings.MAX_AUDIO_BYTES:
        return JsonResponse({"error": "Recording is too large. Keep it under 30 seconds."}, status=413)

    try:
        lat, lng, approximate = _read_coordinates(request.POST)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    try:
        data = extract_job(audio_bytes=audio.read() if audio else None, text=text)
    except GeminiError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    low, high = sorted((data["price_min_npr"], data["price_max_npr"]))
    matches = nearest_workers(data["trade"], lat, lng)
    job = Job.objects.create(
        transcript=data["transcript"],
        trade=data["trade"],
        description_ne=data["description_ne"],
        description_en=data["description_en"],
        urgency=data["urgency"],
        price_min_npr=max(low, 0),
        price_max_npr=max(high, 0),
        follow_up_question=data["follow_up_question"][:300],
        lat=lat,
        lng=lng,
        location_is_approximate=approximate,
        matched_worker=matches[0][0] if matches else None,
    )
    return JsonResponse(
        {"job": _job_dict(job), "workers": [_worker_dict(w, d) for w, d in matches]},
        status=201,
    )


@require_GET
def job_list(request):
    jobs = Job.objects.all()[:20]
    return JsonResponse({"jobs": [_job_dict(j) for j in jobs]})

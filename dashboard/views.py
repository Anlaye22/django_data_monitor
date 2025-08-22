import logging
from datetime import datetime
from collections import Counter
from typing import Dict, Any, List

import requests
from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required


def _parse_iso(ts: str) -> datetime:
    if not ts:
        return datetime.min
    ts = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        try:
            main, frac = ts.split(".")
            frac = (frac + "000000")[:6]
            return datetime.fromisoformat(f"{main}.{frac}")
        except Exception:
            return datetime.min


@login_required
@permission_required('dashboard.index_viewer', raise_exception=True)
def index_view(request):
    logger = logging.getLogger(__name__)

    api_url = getattr(settings, "API_URL", "").strip()
    if not api_url:
        context = {
            "page_title": "Landing Page' Dashboard",
            "error_message": "API_URL no está configurado en settings.",
            "posts_count": 0,
            "users_count": 0,
            "average_title_length": 0,
            "post_items": [],
            "graph_labels": [],
            "graph_values": [],
        }
        return render(request, 'dashboard/index.html', context)

    try:
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()  # {'status': 'success', 'data': {...}, 'message': '...'}
    except requests.exceptions.RequestException as e:
        logger.exception("Error al llamar a la API")
        context = {
            "page_title": "Landing Page' Dashboard",
            "error_message": f"Error al llamar a la API: {e}",
            "posts_count": 0,
            "users_count": 0,
            "average_title_length": 0,
            "post_items": [],
            "graph_labels": [],
            "graph_values": [],
        }
        return render(request, 'dashboard/index.html', context)
    except ValueError:
        context = {
            "page_title": "Landing Page' Dashboard",
            "error_message": "La API devolvió un JSON inválido.",
            "posts_count": 0,
            "users_count": 0,
            "average_title_length": 0,
            "post_items": [],
            "graph_labels": [],
            "graph_values": [],
        }
        return render(request, 'dashboard/index.html', context)

    raw: Dict[str, Dict[str, Any]] = (payload or {}).get("data", {}) or {}

    # Normaliza a lista
    entries: List[Dict[str, Any]] = [
        {"id": k, **(v or {})} for k, v in raw.items()
    ]

    # Orden por timestamp desc
    for it in entries:
        it["_dt"] = _parse_iso(it.get("timestamp"))
    entries.sort(key=lambda x: x["_dt"], reverse=True)
    for it in entries:
        it.pop("_dt", None)

    # Mapea a lo que tu HTML espera:
    # userId ← id | title ← timestamp
    post_items = [
        {"userId": item.get("id", ""), "title": item.get("timestamp", "")}
        for item in entries
    ]

    posts_count = len(post_items)
    users_count = len({item.get("userId") for item in post_items})
    # “Promedio de longitud de título” usando la longitud del timestamp
    average_title_length = 0
    if posts_count:
        average_title_length = round(
            sum(len(item.get("title", "")) for item in post_items) / posts_count, 2
        )

    # Serie temporal por fecha (YYYY-MM-DD)
    by_date = Counter()
    for item in entries:
        ts = item.get("timestamp")
        d = _parse_iso(ts).date().isoformat() if ts else "sin_fecha"
        by_date[d] += 1

    # Ordena por fecha asc
    graph_labels = sorted(by_date.keys())
    graph_values = [by_date[d] for d in graph_labels]

    context = {
        "page_title": "Landing Page' Dashboard",
        "error_message": None,  # Si quieres que muestre “OK”
        "posts_count": posts_count,
        "users_count": users_count,
        "average_title_length": average_title_length,
        "post_items": post_items,
        "graph_labels": graph_labels,
        "graph_values": graph_values,
    }
    return render(request, 'dashboard/index.html', context)

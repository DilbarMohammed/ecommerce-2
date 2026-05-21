import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .chatbot_engine import get_chatbot_response


@ensure_csrf_cookie
def chat_page(request):
    return render(request, "chatbot/chat.html")


@require_POST
def chatbot_message(request):
    message = _extract_message(request)

    if not message:
        return JsonResponse(
            {"response": "Please type a question so I can help."},
            status=400,
        )

    response = get_chatbot_response(message)
    return JsonResponse({"response": response})


def _extract_message(request):
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return ""

        return str(payload.get("message", "")).strip()

    return request.POST.get("message", "").strip()

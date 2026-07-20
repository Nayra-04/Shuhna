from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, Throttled):
        wait_seconds = int(exc.wait) if exc.wait else None
        if wait_seconds:
            minutes = wait_seconds // 60
            message = f"لقد تجاوزت الحد المسموح به من المحاولات، حاول مرة أخرى بعد {minutes} دقيقة تقريبًا"
        else:
            message = "لقد تجاوزت الحد المسموح به من المحاولات، حاول مرة أخرى لاحقًا"
        response.data = {"detail": message}

    return response
import traceback
from rest_framework.exceptions import APIException
from .models import ErrorLog   
from drf_standardized_errors.handler import exception_handler as drf_se_handler

def custom_exception_handler(exc, context):
    request = context.get("request")

    # Determine status code:
    # If it is a DRF APIException, get the real code (e.g., 400, 404)
    # If not, it's a generic Python error which results in a 500
    status_code = getattr(exc, 'status_code', 500)

    # Only proceed if it is a 500 error (or remove this 'if' to log everything)
    if status_code == 500:
        try:
            try:
                body = request.body.decode("utf-8") if request.body else "<Empty Body>"
            except Exception:
                body = "<Could not decode request body>"

            ErrorLog.objects.create(
                data=(
                    f"Error Code: {status_code}\n"  # <--- Status code added here
                    f"Path: {request.path}\n"
                    f"Method: {request.method}\n"
                    f"Query: {dict(request.GET)}\n"
                    f"Body: {body}\n"
                    f"User: {request.user if request.user.is_authenticated else 'Anonymous'}"
                ),
                error=str(exc),
                notes=traceback.format_exc()
            )
        except Exception as e:
            print("🚨 Failed to log exception:", e)

    # Continue using drf-standardized-errors formatting
    return drf_se_handler(exc, context)

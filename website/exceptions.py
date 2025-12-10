import traceback
from .models import ErrorLog   # change "logs" to your actual app name
from drf_standardized_errors.handler import exception_handler as drf_se_handler

def custom_exception_handler(exc, context):
    request = context.get("request")

    # --- LOGGING SECTION ---
    try:
        try:
            body = request.body.decode("utf-8")
        except:
            body = "<Could not decode request body>"

        ErrorLog.objects.create(
            data=(
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
    # --- END LOGGING ---

    # Continue using drf-standardized-errors formatting
    return drf_se_handler(exc, context)

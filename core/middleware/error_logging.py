import traceback
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from website.models import ErrorLog  # adjust import if ErrorLog is in another app

class GlobalExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        try:
            # Read request body safely
            try:
                body = request.body.decode("utf-8")
            except:
                body = "<Could not decode request body>"

            # Create traceback string
            tb = traceback.format_exc()

            # Save error
            ErrorLog.objects.create(
                data=f"Path: {request.path}\n"
                     f"Method: {request.method}\n"
                     f"GET Params: {request.GET}\n"
                     f"POST Body: {body}\n"
                     f"User: {request.user if request.user.is_authenticated else 'Anonymous'}",
                error=str(exception),
                notes=tb
            )

        except Exception as e:
            # If error while logging, do not break system
            ErrorLog.objects.create(
                data="failed to log errors",
                error=str(exception),
                notes=traceback.format_exc()
            )

        # Continue letting DRF return the default 500 error
        return None



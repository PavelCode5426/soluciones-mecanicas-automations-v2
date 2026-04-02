from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        exc.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        fields = exc.get_full_details()

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    if response is not None and "detail" in response.data:
        response.data.pop("detail")

    # Now add the HTTP status code to the response.
    if response is not None and hasattr(exc, "default_code"):
        response.data["name"] = exc.default_code
        response.data["message"] = exc.default_detail

    if (
        response is not None
        and hasattr(exc, "status_code")
        and exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ):
        response.data["fields"] = fields

    return response
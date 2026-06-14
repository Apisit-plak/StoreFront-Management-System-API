from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "success": False,
            "errors": response.data,
        }
        response.data = error_payload

    return response


class InsufficientStockError(Exception):
    def __init__(self, product_title, requested, available):
        self.product_title = product_title
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for '{product_title}': "
            f"requested {requested}, available {available}"
        )

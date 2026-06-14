from django.db import transaction

from products.models import Product
from storefront.exceptions import InsufficientStockError


@transaction.atomic
def purchase_product(product: Product, quantity: int) -> Product:
    product = Product.objects.select_for_update().get(pk=product.pk)

    if product.quantity < quantity:
        raise InsufficientStockError(product.title, quantity, product.quantity)

    product.quantity -= quantity
    product.save(update_fields=["quantity", "updated_at"])
    return product

from decimal import Decimal

from django.db import transaction

from orders.models import Cart, Order, OrderItem, OrderStatus
from products.models import Product
from storefront.exceptions import InsufficientStockError


@transaction.atomic
def checkout_cart(cart: Cart) -> Order:
    cart_items = list(cart.items.select_related("product").select_for_update())

    if not cart_items:
        raise ValueError("Cart is empty.")

    product_ids = [item.product_id for item in cart_items]
    products = {
        p.pk: p
        for p in Product.objects.select_for_update().filter(pk__in=product_ids)
    }

    total_amount = Decimal("0.00")
    order = Order.objects.create(buyer=cart.user, status=OrderStatus.COMPLETED)

    for item in cart_items:
        product = products[item.product_id]

        if product.quantity < item.quantity:
            raise InsufficientStockError(product.title, item.quantity, product.quantity)

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            unit_price=product.unit_price,
        )

        product.quantity -= item.quantity
        product.save(update_fields=["quantity", "updated_at"])
        total_amount += product.unit_price * item.quantity

    order.total_amount = total_amount
    order.save(update_fields=["total_amount", "updated_at"])

    cart.items.all().delete()

    return order

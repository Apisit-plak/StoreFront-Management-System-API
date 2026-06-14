from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["unit_price"]),
            models.Index(fields=["quantity"]),
        ]

    @property
    def in_stock(self):
        return self.quantity > 0

    @property
    def stock_status(self):
        if self.quantity == 0:
            return "out_of_stock"
        if self.quantity <= 5:
            return "low_stock"
        return "in_stock"

    def __str__(self):
        return self.title

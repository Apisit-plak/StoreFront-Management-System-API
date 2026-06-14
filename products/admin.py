from django.contrib import admin

from products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "unit_price", "quantity", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description", "seller__username")

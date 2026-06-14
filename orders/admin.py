from django.contrib import admin

from orders.models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "item_count_display", "updated_at")
    inlines = [CartItemInline]

    def item_count_display(self, obj):
        return obj.item_count

    item_count_display.short_description = "Items"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    inlines = [OrderItemInline]

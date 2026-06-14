import django_filters

from products.models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")
    seller = django_filters.NumberFilter(field_name="seller_id")

    class Meta:
        model = Product
        fields = ["seller", "min_price", "max_price", "in_stock"]

    def filter_in_stock(self, queryset, name, value):
        if value is True:
            return queryset.filter(quantity__gt=0)
        if value is False:
            return queryset.filter(quantity=0)
        return queryset

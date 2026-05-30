from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "product_name", "unit_price", "quantity", "line_total")
    readonly_fields = ("product_name", "unit_price", "line_total", "created_at")
    autocomplete_fields = ("product",)
    can_delete = False

    @admin.display(description="Line total")
    def line_total(self, obj):
        return obj.line_total if obj.pk else "-"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "total_amount",
        "discount_amount",
        "created_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("order_number", "user__username", "user__email", "email", "full_name")
    readonly_fields = ("order_number", "created_at", "updated_at")
    autocomplete_fields = ("user",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "unit_price", "quantity", "created_at")
    list_filter = ("created_at",)
    search_fields = ("order__order_number", "product_name", "product__name")
    autocomplete_fields = ("order", "product")

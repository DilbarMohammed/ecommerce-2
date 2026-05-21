from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_primary")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "discount_price",
        "stock",
        "stock_warning",
        "is_available",
        "created_at",
    )
    list_filter = ("category", "is_available", "created_at", "updated_at")
    list_editable = ("price", "discount_price", "stock", "is_available")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description", "category__name")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProductImageInline]

    @admin.display(description="Stock status", ordering="stock")
    def stock_warning(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color:#dc3545;font-weight:600;">Out of stock</span>')
        if obj.stock <= 5:
            return format_html('<span style="color:#b45309;font-weight:600;">Low stock ({})</span>', obj.stock)
        return format_html('<span style="color:#198754;">Healthy</span>')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "created_at")
    list_filter = ("is_primary", "created_at")
    search_fields = ("product__name", "alt_text")

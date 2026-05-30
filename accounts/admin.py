from django.contrib import admin

from .models import Address, WishlistItem


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "country", "is_default", "updated_at")
    list_filter = ("country", "is_default", "created_at", "updated_at")
    search_fields = (
        "full_name",
        "user__username",
        "user__email",
        "phone_number",
        "city",
        "postal_code",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email", "product__name")
    autocomplete_fields = ("user", "product")

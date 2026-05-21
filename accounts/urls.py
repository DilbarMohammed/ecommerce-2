from django.urls import path

from .views import (
    AccountLoginView,
    AccountLogoutView,
    AddressCreateView,
    AddressDeleteView,
    AddressUpdateView,
    ProfileView,
    RegisterView,
    WishlistRemoveView,
    WishlistToggleView,
    WishlistView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", AccountLoginView.as_view(), name="login"),
    path("logout/", AccountLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("addresses/add/", AddressCreateView.as_view(), name="address_add"),
    path("addresses/<int:pk>/edit/", AddressUpdateView.as_view(), name="address_edit"),
    path("addresses/<int:pk>/delete/", AddressDeleteView.as_view(), name="address_delete"),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", WishlistToggleView.as_view(), name="wishlist_toggle"),
    path("wishlist/remove/<int:product_id>/", WishlistRemoveView.as_view(), name="wishlist_remove"),
]

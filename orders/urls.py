from django.urls import path

from .views import CheckoutView, OrderDetailView, OrderHistoryView, PaymentSuccessView

app_name = "orders"

urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("payment-success/<str:order_number>/", PaymentSuccessView.as_view(), name="payment_success"),
    path("history/", OrderHistoryView.as_view(), name="order_history"),
    path("<str:order_number>/", OrderDetailView.as_view(), name="order_detail"),
]

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, TemplateView

from cart.cart import Cart
from products.models import Product

from .models import Order, OrderItem


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    address_line_1 = forms.CharField(max_length=255)
    address_line_2 = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20)
    country = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class CheckoutView(LoginRequiredMixin, FormView):
    template_name = "orders/checkout.html"
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        self.cart = Cart(request)

        if len(self.cart) == 0:
            messages.info(request, "Your cart is empty.")
            return redirect("cart:cart_detail")

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = {
            "full_name": self.request.user.get_full_name() or self.request.user.username,
            "email": self.request.user.email,
        }
        default_address = self.request.user.addresses.filter(is_default=True).first()

        if default_address:
            initial.update(
                {
                    "full_name": default_address.full_name,
                    "phone_number": default_address.phone_number,
                    "address_line_1": default_address.address_line_1,
                    "address_line_2": default_address.address_line_2,
                    "city": default_address.city,
                    "state": default_address.state,
                    "postal_code": default_address.postal_code,
                    "country": default_address.country,
                }
            )

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart_items"] = list(self.cart)
        context["cart_total"] = self.cart.get_total_price()
        context["discount"] = self.cart.get_discount()
        context["coupon"] = self.cart.get_coupon()
        context["cart_total_after_discount"] = self.cart.get_total_after_discount()
        return context

    def form_valid(self, form):
        cart_items = list(self.cart)

        try:
            order = self._create_order(form.cleaned_data, cart_items)
        except ValueError as error:
            messages.error(self.request, str(error))
            return redirect("cart:cart_detail")

        self.cart.clear()
        return redirect("orders:payment_success", order_number=order.order_number)

    @transaction.atomic
    def _create_order(self, shipping_data, cart_items):
        subtotal_amount = Decimal("0.00")
        product_ids = [item["product"].id for item in cart_items]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        products_by_id = {product.id: product for product in products}

        for item in cart_items:
            product = products_by_id.get(item["product"].id)

            if not product or not product.is_available:
                raise ValueError(f"{item['product'].name} is no longer available.")

            if item["quantity"] > product.stock:
                raise ValueError(f"Only {product.stock} item(s) of {product.name} are available.")

            subtotal_amount += product.final_price * item["quantity"]

        coupon = self.cart.get_coupon()
        discount_amount = coupon.calculate_discount(subtotal_amount) if coupon else Decimal("0.00")
        total_amount = subtotal_amount - discount_amount

        order = Order.objects.create(
            user=self.request.user,
            coupon_code=coupon.code if coupon and discount_amount > 0 else "",
            subtotal_amount=subtotal_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            **shipping_data,
        )

        order_items = []
        for item in cart_items:
            product = products_by_id[item["product"].id]
            quantity = item["quantity"]

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    product_name=product.name,
                    unit_price=product.final_price,
                    quantity=quantity,
                )
            )
            product.stock -= quantity
            product.save(update_fields=["stock", "updated_at"])

        OrderItem.objects.bulk_create(order_items)

        if coupon and discount_amount > 0:
            coupon.used_count += 1
            coupon.save(update_fields=["used_count", "updated_at"])

        return order


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "orders/payment_success.html"

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(
            Order,
            order_number=kwargs["order_number"],
            user=request.user,
        )

        if self.order.status == Order.Status.PENDING:
            self.order.status = Order.Status.PAID
            self.order.save(update_fields=["status", "updated_at"])

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_history.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse("orders:order_history")
        return context

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import Product

from .cart import Cart
from .models import Coupon


def cart_detail(request):
    cart = Cart(request)
    cart_total = cart.get_total_price()
    discount = cart.get_discount()
    coupon = cart.get_coupon()

    return render(
        request,
        "cart/cart_detail.html",
        {
            "cart": cart,
            "cart_items": list(cart),
            "cart_total": cart_total,
            "coupon": coupon,
            "discount": discount,
            "cart_total_after_discount": cart_total - discount,
        },
    )


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    quantity = request.POST.get("quantity", 1)
    cart = Cart(request)

    if product.stock <= 0:
        messages.error(request, "This product is currently out of stock.")
        return redirect("products:product_detail", slug=product.slug)

    requested_quantity = cart._clean_quantity(quantity)
    cart.add(product=product, quantity=requested_quantity)

    if requested_quantity > product.stock:
        messages.warning(request, f"Only {product.stock} item(s) of {product.name} are available.")

    messages.success(request, f"{product.name} was added to your cart.")

    return redirect(request.POST.get("next") or "cart:cart_detail")


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    quantity = request.POST.get("quantity", 1)
    cart = Cart(request)

    requested_quantity = cart._clean_quantity(quantity)
    cart.add(product=product, quantity=requested_quantity, override_quantity=True)

    if requested_quantity > product.stock:
        messages.warning(request, f"Quantity was limited to available stock: {product.stock}.")

    messages.success(request, "Cart updated.")

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.success(request, f"{product.name} was removed from your cart.")

    return redirect("cart:cart_detail")


@require_POST
def coupon_apply(request):
    code = request.POST.get("code", "").strip()
    cart = Cart(request)

    if not code:
        messages.error(request, "Enter a coupon code.")
        return redirect("cart:cart_detail")

    coupon = Coupon.objects.filter(code__iexact=code).first()

    if not coupon or not coupon.is_valid_for_amount(cart.get_total_price()):
        messages.error(request, "This coupon is not valid for your cart.")
        return redirect("cart:cart_detail")

    cart.apply_coupon(coupon)
    messages.success(request, f"Coupon {coupon.code} applied.")
    return redirect("cart:cart_detail")


@require_POST
def coupon_remove(request):
    Cart(request).remove_coupon()
    messages.success(request, "Coupon removed.")
    return redirect("cart:cart_detail")

from decimal import Decimal

from products.models import Product

from .models import Coupon


CART_SESSION_KEY = "cart"
COUPON_SESSION_KEY = "coupon_id"


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get(CART_SESSION_KEY, {})

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids, is_available=True)
        products_by_id = {str(product.id): product for product in products}

        for product_id, item in self.cart.items():
            product = products_by_id.get(product_id)

            if not product:
                continue

            quantity = item["quantity"]
            unit_price = product.final_price

            yield {
                "product": product,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": unit_price * quantity,
            }

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        quantity = self._clean_quantity(quantity)

        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0}

        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity

        self.cart[product_id]["quantity"] = min(self.cart[product_id]["quantity"], product.stock)

        if self.cart[product_id]["quantity"] <= 0:
            self.remove(product)
        else:
            self.save()

    def remove(self, product):
        product_id = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        if CART_SESSION_KEY in self.session:
            del self.session[CART_SESSION_KEY]
        if COUPON_SESSION_KEY in self.session:
            del self.session[COUPON_SESSION_KEY]
        self.session.modified = True

    def get_total_price(self):
        return sum((item["total_price"] for item in self), Decimal("0.00"))

    def apply_coupon(self, coupon):
        self.session[COUPON_SESSION_KEY] = coupon.id
        self.session.modified = True

    def remove_coupon(self):
        if COUPON_SESSION_KEY in self.session:
            del self.session[COUPON_SESSION_KEY]
            self.session.modified = True

    def get_coupon(self):
        coupon_id = self.session.get(COUPON_SESSION_KEY)

        if not coupon_id:
            return None

        try:
            return Coupon.objects.get(id=coupon_id)
        except Coupon.DoesNotExist:
            self.remove_coupon()
            return None

    def get_discount(self):
        coupon = self.get_coupon()

        if not coupon:
            return Decimal("0.00")

        subtotal = self.get_total_price()
        discount = coupon.calculate_discount(subtotal)

        if discount <= 0:
            self.remove_coupon()

        return discount

    def get_total_after_discount(self):
        return self.get_total_price() - self.get_discount()

    def save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    @staticmethod
    def _clean_quantity(quantity):
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        return max(quantity, 1)

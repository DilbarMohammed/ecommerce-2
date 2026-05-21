from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percentage"
        FIXED = "fixed", "Fixed amount"

    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
        default=DiscountType.PERCENT,
    )
    value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(blank=True, null=True)
    used_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active", "valid_from", "valid_until"]),
        ]

    def __str__(self):
        return self.code

    def is_valid_for_amount(self, amount):
        now = timezone.now()

        if not self.is_active:
            return False

        if self.valid_from > now or self.valid_until < now:
            return False

        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False

        return amount >= self.minimum_order_amount

    def calculate_discount(self, amount):
        if not self.is_valid_for_amount(amount):
            return Decimal("0.00")

        if self.discount_type == self.DiscountType.PERCENT:
            discount = amount * (self.value / Decimal("100"))
        else:
            discount = self.value

        return min(discount.quantize(Decimal("0.01")), amount)

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count

from products.models import Product


class ReviewQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(is_approved=True)

    def summary_for_product(self, product):
        return self.approved().filter(product=product).aggregate(
            average_rating=Avg("rating"),
            review_count=Count("id"),
        )


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )
    title = models.CharField(max_length=120)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_review_per_user_product",
            )
        ]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.user}"

    @property
    def star_range(self):
        return range(self.rating)

    @property
    def empty_star_range(self):
        return range(5 - self.rating)

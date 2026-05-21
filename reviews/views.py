from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from products.models import Product

from .forms import ReviewForm
from .models import Review


class ReviewCreateUpdateView(LoginRequiredMixin, View):
    def post(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug, is_available=True)
        review = Review.objects.filter(product=product, user=request.user).first()
        form = ReviewForm(request.POST, instance=review)

        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Your review has been saved.")
        else:
            messages.error(request, "Please fix the review form and try again.")

        return redirect("products:product_detail", slug=product.slug)


class ReviewDeleteView(LoginRequiredMixin, View):
    def post(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        review = get_object_or_404(Review, product=product, user=request.user)
        review.delete()
        messages.success(request, "Your review has been removed.")
        return redirect("products:product_detail", slug=product.slug)

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Category, Product, ProductImage


RECENTLY_VIEWED_SESSION_KEY = "recently_viewed_products"
RECENTLY_VIEWED_LIMIT = 8


def product_card_queryset():
    return Product.objects.filter(is_available=True).select_related("category").prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary", "created_at"),
        )
    )


class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        self.category = None
        category_slug = self.kwargs.get("category_slug")

        if category_slug:
            self.category = get_object_or_404(
                Category,
                slug=category_slug,
                is_active=True,
            )

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (
            product_card_queryset()
        )

        if self.category:
            queryset = queryset.filter(category=self.category)

        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(category__name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True).order_by("name")
        context["selected_category"] = self.category
        context["search_query"] = self.request.GET.get("q", "").strip()
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return product_card_queryset()

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self._store_recently_viewed_product()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        images = list(self.object.images.all())
        recently_viewed_ids = self.request.session.get(RECENTLY_VIEWED_SESSION_KEY, [])
        recently_viewed_products = product_card_queryset().filter(id__in=recently_viewed_ids).exclude(
            id=self.object.id
        )
        recently_viewed_products = sorted(
            recently_viewed_products,
            key=lambda product: recently_viewed_ids.index(product.id),
        )

        context["primary_image"] = next(
            (image for image in images if image.is_primary),
            images[0] if images else None,
        )
        context["gallery_images"] = images
        context["related_products"] = (
            product_card_queryset()
            .filter(category=self.object.category)
            .exclude(id=self.object.id)[:4]
        )
        context["recently_viewed_products"] = recently_viewed_products[:4]
        context["recommended_products"] = self._get_recommended_products(recently_viewed_ids)
        context["is_in_wishlist"] = self._is_in_wishlist()
        return context

    def _store_recently_viewed_product(self):
        product_ids = self.request.session.get(RECENTLY_VIEWED_SESSION_KEY, [])
        product_id = self.object.id

        if product_id in product_ids:
            product_ids.remove(product_id)

        product_ids.insert(0, product_id)
        self.request.session[RECENTLY_VIEWED_SESSION_KEY] = product_ids[:RECENTLY_VIEWED_LIMIT]
        self.request.session.modified = True

    def _get_recommended_products(self, recently_viewed_ids):
        category_ids = Product.objects.filter(id__in=recently_viewed_ids).values_list(
            "category_id",
            flat=True,
        )
        category_ids = list(dict.fromkeys(category_ids))

        if not category_ids:
            category_ids = [self.object.category_id]

        return (
            product_card_queryset()
            .filter(category_id__in=category_ids)
            .exclude(id__in=[self.object.id, *recently_viewed_ids])[:4]
        )

    def _is_in_wishlist(self):
        if not self.request.user.is_authenticated:
            return False

        from accounts.models import WishlistItem

        return WishlistItem.objects.filter(
            user=self.request.user,
            product=self.object,
        ).exists()

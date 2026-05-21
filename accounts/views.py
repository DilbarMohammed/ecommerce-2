from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from products.models import Product

from .forms import AddressForm, UserLoginForm, UserProfileForm, UserRegistrationForm
from .models import Address, WishlistItem


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Your account has been created.")
        return response


class AccountLoginView(LoginView):
    authentication_form = UserLoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return reverse_lazy("accounts:profile")


class AccountLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_form"] = UserProfileForm(instance=self.request.user)
        context["addresses"] = self.request.user.addresses.all()
        return context

    def post(self, request, *args, **kwargs):
        form = UserProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")

        context = self.get_context_data()
        context["profile_form"] = form
        return self.render_to_response(context)


class AddressCreateView(LoginRequiredMixin, CreateView):
    model = Address
    form_class = AddressForm
    template_name = "accounts/address_form.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Address added.")
        return super().form_valid(form)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    model = Address
    form_class = AddressForm
    template_name = "accounts/address_form.html"
    success_url = reverse_lazy("accounts:profile")

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Address updated.")
        return super().form_valid(form)


class AddressDeleteView(LoginRequiredMixin, DeleteView):
    model = Address
    template_name = "accounts/address_confirm_delete.html"
    success_url = reverse_lazy("accounts:profile")

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Address deleted.")
        return super().form_valid(form)


class WishlistView(LoginRequiredMixin, ListView):
    model = WishlistItem
    template_name = "accounts/wishlist.html"
    context_object_name = "wishlist_items"
    paginate_by = 12

    def get_queryset(self):
        return (
            WishlistItem.objects.filter(user=self.request.user)
            .select_related("product", "product__category")
            .prefetch_related("product__images")
        )


class WishlistToggleView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_available=True)
        item, created = WishlistItem.objects.get_or_create(
            user=request.user,
            product=product,
        )

        if created:
            messages.success(request, f"{product.name} was added to your wishlist.")
        else:
            item.delete()
            messages.success(request, f"{product.name} was removed from your wishlist.")

        return redirect(request.POST.get("next") or "accounts:wishlist")


class WishlistRemoveView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        WishlistItem.objects.filter(user=request.user, product=product).delete()
        messages.success(request, f"{product.name} was removed from your wishlist.")
        return redirect("accounts:wishlist")

from decimal import Decimal
from html import escape

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from products.models import Category, Product, ProductImage


DEMO_CATEGORIES = [
    {
        "name": "Electronics",
        "description": "Everyday tech accessories and smart devices for home and travel.",
    },
    {
        "name": "Home & Kitchen",
        "description": "Useful home essentials, kitchen tools, and small appliances.",
    },
    {
        "name": "Fashion",
        "description": "Comfortable wardrobe basics and accessories for daily wear.",
    },
    {
        "name": "Sports & Outdoors",
        "description": "Fitness, wellness, and outdoor gear for active routines.",
    },
]


DEMO_PRODUCTS = [
    {
        "category": "Electronics",
        "name": "Aurora Wireless Headphones",
        "description": "Comfortable over-ear Bluetooth headphones with soft ear cushions, clear audio, and long battery life for commuting, study, and work calls.",
        "price": "89.99",
        "discount_price": "74.99",
        "stock": 24,
        "color": "#2563eb",
    },
    {
        "category": "Electronics",
        "name": "VoltEdge 20W USB-C Charger",
        "description": "Compact fast charger for phones, earbuds, and small tablets. The travel-friendly build fits neatly into a backpack or desk drawer.",
        "price": "18.99",
        "discount_price": None,
        "stock": 60,
        "color": "#0f766e",
    },
    {
        "category": "Electronics",
        "name": "LumaView Desk Lamp",
        "description": "LED desk lamp with adjustable brightness, warm and cool light modes, and a flexible arm for reading or focused laptop work.",
        "price": "42.50",
        "discount_price": "34.50",
        "stock": 18,
        "color": "#ca8a04",
    },
    {
        "category": "Electronics",
        "name": "Pocket Bluetooth Speaker",
        "description": "Small wireless speaker with punchy sound, simple controls, and a durable outer shell for picnics, rooms, and weekend trips.",
        "price": "36.00",
        "discount_price": None,
        "stock": 35,
        "color": "#7c3aed",
    },
    {
        "category": "Home & Kitchen",
        "name": "BrewMate Stainless Coffee Press",
        "description": "A sturdy French press with a heat-resistant handle and fine mesh filter for rich coffee at home or in the office.",
        "price": "29.99",
        "discount_price": None,
        "stock": 22,
        "color": "#92400e",
    },
    {
        "category": "Home & Kitchen",
        "name": "FreshStack Glass Storage Set",
        "description": "Stackable glass food containers with snap lids for meal prep, leftovers, pantry organization, and lunch packing.",
        "price": "54.99",
        "discount_price": "44.99",
        "stock": 16,
        "color": "#16a34a",
    },
    {
        "category": "Home & Kitchen",
        "name": "CloudSoft Cotton Towel Pack",
        "description": "Soft absorbent cotton towels for bathroom, gym, or guest use. Includes multiple sizes for everyday routines.",
        "price": "39.99",
        "discount_price": None,
        "stock": 28,
        "color": "#0891b2",
    },
    {
        "category": "Home & Kitchen",
        "name": "QuickChop Bamboo Cutting Board",
        "description": "Smooth bamboo cutting board with juice grooves and a reversible surface for vegetables, bread, and serving snacks.",
        "price": "24.75",
        "discount_price": "19.99",
        "stock": 31,
        "color": "#65a30d",
    },
    {
        "category": "Fashion",
        "name": "UrbanTrail Canvas Backpack",
        "description": "A lightweight everyday backpack with padded straps, laptop sleeve, and roomy front pocket for school, work, or travel.",
        "price": "64.00",
        "discount_price": "52.00",
        "stock": 14,
        "color": "#475569",
    },
    {
        "category": "Fashion",
        "name": "BreezeFit Running Tee",
        "description": "Breathable quick-dry T-shirt with a relaxed athletic fit, made for workouts, walks, and casual weekend wear.",
        "price": "22.99",
        "discount_price": None,
        "stock": 45,
        "color": "#dc2626",
    },
    {
        "category": "Fashion",
        "name": "Classic Leather Wallet",
        "description": "Slim leather wallet with card slots, bill compartment, and clean stitching for a polished everyday carry option.",
        "price": "31.50",
        "discount_price": "27.00",
        "stock": 26,
        "color": "#78350f",
    },
    {
        "category": "Fashion",
        "name": "Everyday Knit Beanie",
        "description": "Soft ribbed beanie with a simple fold-over cuff, comfortable enough for chilly mornings and casual outfits.",
        "price": "16.99",
        "discount_price": None,
        "stock": 38,
        "color": "#be123c",
    },
    {
        "category": "Sports & Outdoors",
        "name": "FlexCore Yoga Mat",
        "description": "Non-slip exercise mat with balanced cushioning for yoga, stretching, floor workouts, and cooldown routines.",
        "price": "33.99",
        "discount_price": "28.99",
        "stock": 21,
        "color": "#9333ea",
    },
    {
        "category": "Sports & Outdoors",
        "name": "TrailSip Insulated Bottle",
        "description": "Double-wall stainless bottle that keeps drinks cold or warm, with a leak-resistant lid for gym bags and day hikes.",
        "price": "27.99",
        "discount_price": None,
        "stock": 40,
        "color": "#0284c7",
    },
    {
        "category": "Sports & Outdoors",
        "name": "PulseGrip Resistance Band Kit",
        "description": "Portable resistance band set with multiple tension levels for strength training, mobility work, and travel workouts.",
        "price": "25.50",
        "discount_price": "21.25",
        "stock": 33,
        "color": "#ea580c",
    },
    {
        "category": "Sports & Outdoors",
        "name": "SummitLite Daypack",
        "description": "Compact outdoor daypack with breathable shoulder straps and enough room for snacks, water, layers, and small essentials.",
        "price": "48.00",
        "discount_price": None,
        "stock": 12,
        "color": "#15803d",
    },
]


class Command(BaseCommand):
    help = "Create realistic demo categories, products, and placeholder product images."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-demo",
            action="store_true",
            help="Delete and recreate products managed by this demo seed command.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset_demo"]:
            demo_names = [product["name"] for product in DEMO_PRODUCTS]
            deleted_count, _ = Product.objects.filter(name__in=demo_names).delete()
            self.stdout.write(f"Deleted {deleted_count} existing demo records.")

        categories = self._create_categories()
        created_count = 0
        updated_count = 0

        for product_data in DEMO_PRODUCTS:
            product, created = self._create_product(product_data, categories)
            self._replace_demo_image(product, product_data)

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready: {len(categories)} categories, "
                f"{created_count} products created, {updated_count} products updated."
            )
        )

    def _create_categories(self):
        categories = {}

        for category_data in DEMO_CATEGORIES:
            category, _ = Category.objects.update_or_create(
                name=category_data["name"],
                defaults={
                    "description": category_data["description"],
                    "is_active": True,
                },
            )
            categories[category.name] = category

        return categories

    def _create_product(self, product_data, categories):
        product, created = Product.objects.update_or_create(
            name=product_data["name"],
            defaults={
                "category": categories[product_data["category"]],
                "description": product_data["description"],
                "price": Decimal(product_data["price"]),
                "discount_price": (
                    Decimal(product_data["discount_price"])
                    if product_data["discount_price"]
                    else None
                ),
                "stock": product_data["stock"],
                "is_available": True,
            },
        )
        return product, created

    def _replace_demo_image(self, product, product_data):
        for image in product.images.all():
            if image.image:
                image.image.delete(save=False)
            image.delete()

        image = ProductImage(
            product=product,
            alt_text=f"{product.name} demo image",
            is_primary=True,
        )
        image.image.save(
            f"{slugify(product.name)}.svg",
            ContentFile(self._build_svg(product_data).encode("utf-8")),
            save=True,
        )

    @staticmethod
    def _build_svg(product_data):
        name = escape(product_data["name"])
        category = escape(product_data["category"])
        color = product_data["color"]

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="700" viewBox="0 0 900 700">
  <rect width="900" height="700" fill="#f8fafc"/>
  <rect x="70" y="70" width="760" height="560" rx="34" fill="{color}"/>
  <circle cx="710" cy="170" r="72" fill="#ffffff" opacity="0.2"/>
  <circle cx="205" cy="510" r="116" fill="#111827" opacity="0.14"/>
  <rect x="150" y="210" width="600" height="250" rx="28" fill="#ffffff" opacity="0.92"/>
  <text x="450" y="315" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="44" font-weight="700" fill="#111827">{name}</text>
  <text x="450" y="380" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="28" fill="#475569">{category}</text>
  <text x="450" y="540" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="24" font-weight="700" fill="#ffffff">DEMO PRODUCT</text>
</svg>
"""

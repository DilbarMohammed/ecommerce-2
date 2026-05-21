import re

from django.db.models import Q
from django.urls import reverse

from products.models import Product


FAQS = {
    "return policy": "You can request a return within 7 days of delivery if the item is unused and in its original packaging.",
    "refund policy": "Refunds are processed after the returned item is inspected. The amount is usually credited within 5 to 7 business days.",
    "shipping time": "Standard shipping usually takes 3 to 7 business days depending on your location.",
    "payment methods": "We currently support card payments, cash on delivery, and demo checkout for local testing.",
    "order tracking": "You can track your order from your account order history page after signing in.",
    "product availability": "Product availability is shown on each product page and is based on current stock.",
}

RULE_RESPONSES = {
    "greeting": "Hi! I can help with products, orders, shipping, refunds, payments, and availability.",
    "order": "You can view order status from your order history page. If you have an order number, open your account orders to check the latest status.",
    "refund": FAQS["refund policy"],
    "return": FAQS["return policy"],
    "shipping": FAQS["shipping time"],
    "payment": FAQS["payment methods"],
}

STOP_WORDS = {
    "a",
    "about",
    "and",
    "are",
    "available",
    "availability",
    "can",
    "do",
    "find",
    "for",
    "have",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "please",
    "product",
    "products",
    "show",
    "stock",
    "the",
    "you",
}


def get_chatbot_response(message):
    message = (message or "").strip()[:500]

    if not message:
        return "Please type a question so I can help."

    tokens = _tokenize(message)
    raw_tokens = _raw_tokens(message)

    rule_response = _match_rule(tokens, raw_tokens)
    if rule_response:
        return rule_response

    faq_response = _match_faq(tokens)
    if faq_response:
        return faq_response

    product_response = _match_products(message, tokens, raw_tokens)
    if product_response:
        return product_response

    return (
        "I can help with product search, availability, order tracking, refunds, returns, "
        "shipping, and payment questions. Try asking about a product name or category."
    )


def _tokenize(message):
    words = re.findall(r"[a-z0-9]+", message.lower())
    return {word for word in words if word not in STOP_WORDS}


def _raw_tokens(message):
    return set(re.findall(r"[a-z0-9]+", message.lower()))


def _match_rule(tokens, raw_tokens):
    if tokens & {"hello", "hey", "hi", "namaste"}:
        return RULE_RESPONSES["greeting"]

    if tokens & {"order", "orders", "track", "tracking", "status"}:
        return RULE_RESPONSES["order"]

    if tokens & {"refund", "refunded", "money"}:
        return RULE_RESPONSES["refund"]

    if tokens & {"return", "replace", "exchange"}:
        return RULE_RESPONSES["return"]

    if tokens & {"shipping", "ship", "delivery", "deliver"}:
        return RULE_RESPONSES["shipping"]

    if tokens & {"payment", "pay", "card", "cod", "cash"}:
        return RULE_RESPONSES["payment"]

    if raw_tokens & {"available", "availability", "stock"}:
        return FAQS["product availability"]

    return None


def _match_faq(tokens):
    best_answer = None
    best_score = 0

    for question, answer in FAQS.items():
        question_tokens = _tokenize(question)
        score = len(tokens & question_tokens)

        if score > best_score:
            best_score = score
            best_answer = answer

    return best_answer if best_score >= 2 else None


def _match_products(message, tokens, raw_tokens):
    product_keywords = {"buy", "category", "price", "product", "products", "search", "stock"}
    should_search = bool(tokens) or bool(raw_tokens & product_keywords)

    if not should_search:
        return None

    queryset = Product.objects.filter(is_available=True).select_related("category")
    search_query = Q()

    for token in tokens:
        search_query |= (
            Q(name__icontains=token)
            | Q(description__icontains=token)
            | Q(category__name__icontains=token)
        )

    if not search_query:
        return None

    products = list(queryset.filter(search_query).distinct()[:5])

    if not products:
        return None

    lines = ["I found these matching products:"]

    for product in products:
        stock_status = "in stock" if product.in_stock else "out of stock"
        product_url = reverse("products:product_detail", kwargs={"slug": product.slug})
        lines.append(
            f"- {product.name} ({product.category.name}) - ${product.final_price} - {stock_status} - {product_url}"
        )

    return "\n".join(lines)

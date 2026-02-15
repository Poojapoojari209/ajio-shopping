from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from cart.models import Cart, CartItem
from users.models import Address
from orders.models import Order, OrderItem
from datetime import datetime
from django.http import JsonResponse

# import this from your orders app
from orders.jwt_utils import get_jwt_user_from_cookie


def index(request):
    return render(request, 'index.html')



def cart_page(request):
    return render(request, "cart.html")

def wishlist_page(request):
    return render(request, "wishlist.html")




@login_required
def orders(request):
    return render(request, "account/orders.html", {"active": "orders"})

@login_required
def wallet(request):
    return render(request, "account/wallet.html", {"active": "wallet"})

@login_required
def invites(request):
    return render(request, "account/invites.html", {"active": "invites"})

@login_required
def profile(request):
    return render(request, "account/profile.html", {"active": "profile"})

@login_required
def address_book(request):
    return render(request, "account/address_book.html", {"active": "address_book"})

@login_required
def payments(request):
    return render(request, "account/payments.html", {"active": "payments"})


# order details page
def order_detail_page(request, order_id):
    return render(request, "account/order_detail.html", {"order_id": order_id})


def customer_care_page(request):
    """
    Public page:
    - Guest: show login CTA (AJIO-like)
    - Logged in: show order carousel + FAQs
    """
    user = get_jwt_user_from_cookie(request)

    return render(request, "customer_care/customer_care.html", {
        "is_logged_in": bool(user)
    })


def customer_care_orders_api(request):
    """
    URL: /api/customer-care/orders/
    - Guest: []
    - Logged in: returns recent orders
    """
    user = get_jwt_user_from_cookie(request)
    if not user:
        return JsonResponse([], safe=False)

    orders = (
        Order.objects
        .filter(user=user)
        .prefetch_related("items__product__images")
        .order_by("-created_at")[:10]
    )

    data = []
    for o in orders:
        items = list(o.items.all())[:2]
        products = []

        for it in items:
            p = it.product
            img = p.images.first().image.url if hasattr(p, "images") and p.images.first() else None
            products.append({"name": p.name, "image": img})

        data.append({
            "id": o.id,
            "order_id": f"FN{o.id:010d}",
            "status": o.status,
            "products": products
        })

    return JsonResponse(data, safe=False)

# def order_success(request):
#     return render(request, "orders/success.html")

def order_confirm_page(request, order_id):
    user = get_jwt_user_from_cookie(request)
    if not user:
        return redirect("/login/")

    order = get_object_or_404(Order, id=order_id, user=user)
    items = OrderItem.objects.select_related("product").filter(order=order)

    return render(request, "orders/confirm.html", {
        "order": order,
        "items": items
    })

def order_success_page(request, order_id):
    user = get_jwt_user_from_cookie(request)
    if not user:
        return redirect("/login/")

    order = get_object_or_404(Order, id=order_id, user=user)
    return render(request, "orders/success.html", {"order": order})
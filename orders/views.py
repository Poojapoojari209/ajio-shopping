# orders/views.py

from decimal import Decimal
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

import razorpay
from django.conf import settings

from .models import Payment, Order, OrderItem, ProductRating, OrderStatusHistory
from .serializers import OrderSerializer
from users.models import Address
from cart.models import Cart, CartItem
from .jwt_utils import get_jwt_user_from_cookie
from products.models import ProductPincodeAvailability


# -------------------------
# Helpers
# -------------------------

def get_cart_items(user):
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        return CartItem.objects.none()
    return CartItem.objects.filter(cart=cart).select_related("product")


def push_order_status(order, status_value, note=""):
    """
    Update Order.status + create timeline entry.
    Prevent duplicates.
    """
    status_value = (status_value or "").upper().strip()
    if not status_value:
        return

    if order.status != status_value:
        order.status = status_value
        order.save(update_fields=["status"])

    last = OrderStatusHistory.objects.filter(order=order).order_by("-created_at").first()
    if not last or last.status != status_value:
        OrderStatusHistory.objects.create(order=order, status=status_value, note=note)


def auto_update_order_status(order):
    """
    Auto update ONLY:
    CONFIRMED or PENDING -> DELIVERED
    when estimated_delivery date is reached.
    No SHIPPED logic.
    """
    if not order:
        return

    current = (order.status or "").upper()

    if current in ["DELIVERED", "CANCELLED", "FAILED"]:
        return

    if not order.estimated_delivery:
        return

    today = timezone.localdate()
    if today >= order.estimated_delivery:
        push_order_status(order, "DELIVERED", "Auto delivered (ETA reached)")


def D(x):
    """Safe Decimal converter"""
    if x is None:
        return Decimal("0.00")
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal("0.00")


def clean_size(val, max_len=10):
    """
    Stores ONLY safe size values like XS, S, M, L, XL, 32 etc.
    """
    if val is None:
        return ""
    s = str(val).strip()

    if s.lower() in ("none", "null", "undefined", "[object object]"):
        return ""

    return s[:max_len]


# ✅ VALID SIZE CODES (must match your ProductSize.SIZE_CHOICES keys)
VALID_SIZES = {
    "XS", "S", "M", "L", "XL", "XXL",
    "28", "30", "32", "34", "36",
    "5", "6", "7", "8", "9", "10", "11", "12",
    "0-2", "3-5", "6-7", "8-10", "11-14",
    "FZ",
}


def normalize_order_size(cart_item) -> str:
    """
    Fixes your bug:
    Sometimes cart_item.size becomes product name.
    This function guarantees only valid size codes are stored in OrderItem.size.
    """
    raw = getattr(cart_item, "size", "")

    if raw is None:
        return ""

    # If size accidentally is an object (FK), take its .size
    if hasattr(raw, "size"):
        raw = raw.size

    s = str(raw).strip()

    # reject wrong values (like product name)
    if s not in VALID_SIZES:
        return ""

    return s


def compute_eta_days(cart_items, pincode):
    """
    Get ETA from ProductPincodeAvailability
    Take max eta_days among items
    """
    product_ids = list(cart_items.values_list("product_id", flat=True))

    qs = ProductPincodeAvailability.objects.filter(
        product_id__in=product_ids,
        pincode__pincode=str(pincode),
        is_available=True
    )

    availability_map = {x.product_id: x for x in qs}

    for pid in product_ids:
        if pid not in availability_map:
            raise ValueError("Product not deliverable to this pincode")

    return max(int(availability_map[pid].eta_days or 3) for pid in product_ids)


def calculate_order_breakup(cart_items):
    bag_total = Decimal("0.00")
    bag_discount = Decimal("0.00")
    payable_items_total = Decimal("0.00")

    for item in cart_items:
        qty = int(item.quantity or 0)
        price = D(item.product.price)
        discount_price = D(getattr(item.product, "discount_price", 0))

        unit_payable = discount_price if discount_price > 0 else price

        bag_total += price * qty
        payable_items_total += unit_payable * qty

        if unit_payable < price:
            bag_discount += (price - unit_payable) * qty

    convenience_fee = Decimal("0.00")
    delivery_fee = Decimal("99.00") if payable_items_total > 0 else Decimal("0.00")
    platform_fee = Decimal("29.00") if payable_items_total > 0 else Decimal("0.00")

    order_total = payable_items_total + convenience_fee + delivery_fee + platform_fee

    return {
        "bag_total": bag_total,
        "bag_discount": bag_discount,
        "convenience_fee": convenience_fee,
        "delivery_fee": delivery_fee,
        "platform_fee": platform_fee,
        "order_total": order_total,
    }


# -------------------------
# HTML PAGES
# -------------------------

def checkout_page(request):
    # ✅ DO NOT redirect to /login/
    # Page will load, JS will open OTP modal if not logged in
    addresses = []
    user = get_jwt_user_from_cookie(request)

    if user:
        addresses = Address.objects.filter(user=user).order_by("-is_default", "-id")

    cart_items = get_cart_items(user) if user else CartItem.objects.none()
    breakup = calculate_order_breakup(cart_items) if user else {
        "bag_total": Decimal("0.00"),
        "bag_discount": Decimal("0.00"),
        "convenience_fee": Decimal("0.00"),
        "delivery_fee": Decimal("0.00"),
        "platform_fee": Decimal("0.00"),
        "order_total": Decimal("0.00"),
    }

    return render(request, "orders/shipping.html", {
        "addresses": addresses,
        "bag_total": breakup["bag_total"],
        "bag_discount": breakup["bag_discount"],
        "convenience_fee": breakup["convenience_fee"],
        "delivery_fee": breakup["delivery_fee"],
        "platform_fee": breakup["platform_fee"],
        "order_total": breakup["order_total"],
    })


def payment_page(request):
    # ✅ DO NOT redirect to /login/
    user = get_jwt_user_from_cookie(request)

    months = [f"{i:02d}" for i in range(1, 13)]
    years = list(range(datetime.now().year, datetime.now().year + 15))

    cart_items = get_cart_items(user) if user else CartItem.objects.none()
    breakup = calculate_order_breakup(cart_items) if user else {
        "delivery_fee": Decimal("0.00"),
        "platform_fee": Decimal("0.00"),
        "order_total": Decimal("0.00"),
    }

    return render(request, "orders/payment.html", {
        "months": months,
        "years": years,
        "delivery_fee": breakup["delivery_fee"],
        "platform_fee": breakup["platform_fee"],
        "order_total": breakup["order_total"],
        "amount": breakup["order_total"],
        "phone": "",
        "customer_name": user.username if user else "",
    })

# -------------------------
# APIs
# -------------------------

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_order(request):
    address_id = request.data.get("address_id")

    address = Address.objects.filter(id=address_id, user=request.user).first()
    if not address:
        return Response({"error": "Invalid address"}, status=400)

    cart_items = get_cart_items(request.user)
    if not cart_items.exists():
        return Response({"error": "Cart empty"}, status=400)

    # Calculate total
    total = Decimal("0.00")
    for item in cart_items:
        price = D(item.product.discount_price or item.product.price)
        total += price * int(item.quantity or 0)

    # ETA from DB
    try:
        eta_days = compute_eta_days(cart_items, address.pincode)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    estimated_delivery = timezone.localdate() + timedelta(days=eta_days)

    order = Order.objects.create(
        user=request.user,
        address=address,
        total_amount=total,
        status="PENDING",
        estimated_delivery=estimated_delivery
    )

    push_order_status(order, "PENDING", "Order created")

    # ✅ Create Order Items (FIXED SIZE)
    for item in cart_items:
        price = D(item.product.discount_price or item.product.price)
        picked_size = normalize_order_size(item)   # ✅ always safe

        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=int(item.quantity or 0),
            price=price,
            size=picked_size
        )

    return Response({
        "order_id": order.id,
        "estimated_delivery": str(order.estimated_delivery) if order.estimated_delivery else None
    }, status=201)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    # auto update each order
    for o in orders:
        auto_update_order_status(o)

    data = OrderSerializer(orders, many=True, context={"request": request}).data

    for i, o in enumerate(orders):
        data[i]["estimated_delivery"] = str(o.estimated_delivery) if o.estimated_delivery else None
        data[i]["can_cancel"] = (o.status or "").upper() not in ["DELIVERED", "CANCELLED", "FAILED"]
        data[i]["status_label"] = (o.status or "").capitalize()

    return Response(data)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def order_detail_api(request, order_id):
    order = Order.objects.filter(id=order_id, user=request.user).first()
    if not order:
        return Response({"error": "Order not found"}, status=404)

    auto_update_order_status(order)

    data = OrderSerializer(order, context={"request": request}).data
    data["estimated_delivery"] = str(order.estimated_delivery) if order.estimated_delivery else None
    data["can_cancel"] = (order.status or "").upper() not in ["DELIVERED", "CANCELLED", "FAILED"]
    data["status_label"] = (order.status or "").capitalize()

    return Response(data)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_payment(request):
    order_id = request.data.get("order_id")
    payment_method = request.data.get("payment_method", "COD")

    order = Order.objects.filter(id=order_id, user=request.user).first()
    if not order:
        return Response({"error": "Invalid order"}, status=400)

    if payment_method != "COD":
        return Response({"error": "Use Razorpay APIs for online payment"}, status=400)

    Payment.objects.create(
        order=order,
        payment_method="COD",
        payment_status="PENDING",
        transaction_id=""
    )

    push_order_status(order, "CONFIRMED", "COD confirmed")

    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        CartItem.objects.filter(cart=cart).delete()

    return Response({"message": "COD order confirmed"})


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def razorpay_create_order(request):
    order_id = request.data.get("order_id")

    if not order_id:
        return Response({"error": "order_id is required"}, status=400)

    order = Order.objects.filter(id=order_id, user=request.user).first()
    if not order:
        return Response({"error": "Invalid order"}, status=400)

    if not getattr(settings, "RAZORPAY_KEY_ID", None) or not getattr(settings, "RAZORPAY_KEY_SECRET", None):
        return Response({"error": "Razorpay keys missing in settings.py"}, status=500)

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        amount_paise = int(D(order.total_amount) * 100)
        if amount_paise <= 0:
            return Response({"error": "Order amount is invalid"}, status=400)

        rp_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"order_{order.id}",
            "payment_capture": 1
        })

        order.razorpay_order_id = rp_order["id"]
        order.save(update_fields=["razorpay_order_id"])

        return Response({
            "key": settings.RAZORPAY_KEY_ID,
            "amount": amount_paise,
            "razorpay_order_id": rp_order["id"]
        })

    except Exception as e:
        print("RAZORPAY ERROR:", str(e))
        return Response({"error": f"Razorpay error: {str(e)}"}, status=500)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def razorpay_verify(request):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": request.data["razorpay_order_id"],
            "razorpay_payment_id": request.data["razorpay_payment_id"],
            "razorpay_signature": request.data["razorpay_signature"],
        })
    except Exception:
        order = Order.objects.filter(id=request.data.get("order_id"), user=request.user).first()
        if order:
            push_order_status(order, "FAILED", "Razorpay signature failed")
        return Response({"error": "Signature verification failed"}, status=400)

    order = Order.objects.filter(id=request.data.get("order_id"), user=request.user).first()
    if not order:
        return Response({"error": "Order not found"}, status=404)

    if order.razorpay_order_id != request.data.get("razorpay_order_id"):
        return Response({"error": "Order mismatch"}, status=400)

    Payment.objects.create(
        order=order,
        payment_method="RAZORPAY",
        payment_status="SUCCESS",
        transaction_id=request.data["razorpay_payment_id"]
    )

    push_order_status(order, "CONFIRMED", "Online payment success")

    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        CartItem.objects.filter(cart=cart).delete()

    return Response({"message": "Payment successful"})


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def submit_rating(request):
    order_item_id = request.data.get("order_item_id")
    rating = request.data.get("rating")
    comment = request.data.get("comment", "")

    try:
        order_item_id = int(order_item_id)
        rating = int(rating)
    except Exception:
        return Response({"error": "Invalid data"}, status=400)

    if rating < 1 or rating > 5:
        return Response({"error": "Rating must be between 1 and 5"}, status=400)

    item = OrderItem.objects.select_related("order", "product").filter(
        id=order_item_id,
        order__user=request.user
    ).first()

    if not item:
        return Response({"error": "Order item not found"}, status=404)

    if (item.order.status or "").upper() != "DELIVERED":
        return Response({"error": "Rating allowed only after delivery"}, status=403)

    if ProductRating.objects.filter(order_item=item, user=request.user).exists():
        return Response({"error": "Already rated"}, status=409)

    ProductRating.objects.create(
        user=request.user,
        product=item.product,
        order_item=item,
        rating=rating,
        comment=comment
    )

    return Response({"message": "Rating submitted successfully"}, status=200)


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_update_order_status(request, order_id):
    if not request.user.is_staff:
        return Response({"error": "Only admin can update order status"}, status=403)

    new_status = (request.data.get("status") or "").upper().strip()
    valid = {k for (k, _) in Order.STATUS_CHOICES}

    if new_status not in valid:
        return Response({"error": f"Invalid status. Allowed: {sorted(valid)}"}, status=400)

    order = Order.objects.filter(id=order_id).first()
    if not order:
        return Response({"error": "Order not found"}, status=404)

    push_order_status(order, new_status, "Admin updated status")

    return Response({
        "message": "Status updated",
        "order_id": order.id,
        "status": order.status
    }, status=200)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def cancel_order_api(request, order_id):
    order = Order.objects.filter(id=order_id, user=request.user).first()

    if not order:
        return Response({"error": "Order not found"}, status=404)

    if (order.status or "").upper() in ["SHIPPED", "DELIVERED", "CANCELLED"]:
        return Response({"error": "Cannot cancel this order"}, status=400)

    push_order_status(order, "CANCELLED", "Cancelled by user")
    return Response({"message": "Order cancelled successfully"})

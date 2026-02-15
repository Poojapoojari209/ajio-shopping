from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import *
from products.models import Product, ProductSize


# ---------------- CART ----------------

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)  # always exists
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    product_id = request.data.get("product_id")
    size_value = request.data.get("size")         #  coming from frontend
    quantity = request.data.get("quantity", 1)

    # DEBUG (keep for now)
    print("ADD TO CART DATA:", request.data)

    if not product_id or not size_value:
        return Response({"error": "product_id and size are required"}, status=400)

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return Response({"error": "Invalid quantity"}, status=400)

    if quantity < 1:
        quantity = 1

    product = get_object_or_404(Product, id=product_id)
    product_size = get_object_or_404(ProductSize, product=product, size=size_value)

    if product_size.stock < quantity:
        return Response({"error": "Not enough stock for selected size"}, status=400)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=product_size,
        defaults={"quantity": quantity}
    )

    if not created:
        if product_size.stock < quantity:
            return Response({"error": "Not enough stock for selected size"}, status=400)

        item.quantity += quantity
        item.save()

        product_size.stock -= quantity
        product_size.save()
    else:
        product_size.stock -= quantity
        product_size.save()

    return Response({"message": "Item added", "cart_item_id": item.id})


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    qty = request.data.get("quantity")
    try:
        qty = int(qty)
    except (ValueError, TypeError):
        return Response({"error": "Invalid quantity"}, status=400)

    if qty < 1:
        qty = 1

    diff = qty - item.quantity  # + => user increases qty

    if diff > 0:
        # need more stock
        if item.size.stock < diff:
            return Response({"error": "Not enough stock"}, status=400)
        item.size.stock -= diff
        item.size.save()

    elif diff < 0:
        # return stock
        item.size.stock += abs(diff)
        item.size.save()

    item.quantity = qty
    item.save()

    return Response({"message": "Quantity updated", "quantity": item.quantity})


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):
    CartItem.objects.filter(
        cart__user=request.user,
        id=item_id
    ).delete()

    return Response({"message": "Removed from cart"})


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    qty = request.data.get("quantity")
    try:
        qty = int(qty)
    except:
        return Response({"error": "Invalid quantity"}, status=400)

    if qty < 1:
        qty = 1

    # stock handling (increase/decrease)
    # if you reduce stock on add-to-cart, you must adjust here too
    diff = qty - item.quantity  # + means user increased qty

    if diff > 0:
        # need more stock
        if item.size.stock < diff:
            return Response({"error": "Not enough stock"}, status=400)
        item.size.stock -= diff
        item.size.save()
    elif diff < 0:
        # return stock
        item.size.stock += abs(diff)
        item.size.save()

    item.quantity = qty
    item.save()

    return Response({"message": "Quantity updated", "quantity": item.quantity})

from django.shortcuts import get_object_or_404
from products.models import ProductSize

@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_cart_item_size(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    new_size_value = request.data.get("size")
    if not new_size_value:
        return Response({"error": "size is required"}, status=400)

    # find new ProductSize for same product
    new_ps = get_object_or_404(ProductSize, product=item.product, size=new_size_value)

    # If size is same, nothing to do
    if item.size_id == new_ps.id:
        return Response({"message": "Size unchanged"})

    # stock handling:
    # return old size stock
    if item.size:
        item.size.stock += item.quantity
        item.size.save()

    # check new size stock
    if new_ps.stock < item.quantity:
        # rollback old stock return is already done, so put back? better: do check first
        # Instead do check first before returning old stock:
        # (Simpler approach below)
        return Response({"error": "Not enough stock for selected size"}, status=400)

    # reduce new size stock
    new_ps.stock -= item.quantity
    new_ps.save()

    # update item size
    item.size = new_ps
    item.save()

    return Response({"message": "Size updated", "size": item.size.size})

# account/api_views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from users.models import Address
from .serializers import AddressSerializer


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def address_list_api(request):
    qs = Address.objects.filter(user=request.user).order_by("-is_default", "-id")
    return Response(AddressSerializer(qs, many=True).data)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def address_create_api(request):
    serializer = AddressSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    is_default = serializer.validated_data.get("is_default", False)
    if is_default:
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

    obj = serializer.save(user=request.user)
    return Response(AddressSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(["PUT", "PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def address_update_api(request, pk):
    obj = Address.objects.filter(pk=pk, user=request.user).first()
    if not obj:
        return Response({"error": "Address not found"}, status=404)

    serializer = AddressSerializer(obj, data=request.data, partial=(request.method == "PATCH"))
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    is_default = serializer.validated_data.get("is_default", obj.is_default)
    if is_default:
        Address.objects.filter(user=request.user, is_default=True).exclude(pk=obj.pk).update(is_default=False)

    obj = serializer.save()
    return Response(AddressSerializer(obj).data)


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def address_delete_api(request, pk):
    obj = Address.objects.filter(pk=pk, user=request.user).first()
    if not obj:
        return Response({"error": "Address not found"}, status=404)
    obj.delete()
    return Response({"message": "Deleted"})


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def address_set_default_api(request, pk):
    obj = Address.objects.filter(pk=pk, user=request.user).first()
    if not obj:
        return Response({"error": "Address not found"}, status=404)

    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    obj.is_default = True
    obj.save(update_fields=["is_default"])

    return Response({"message": "Default updated"})

import random
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate  # MISSING IMPORT FIXED

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Address, OTP, UserProfile
from .serializers import AddressSerializer, MeProfileSerializer

import os
from twilio.rest import Client

def twilio_client():
    return Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))


# ----------------------------
# Address APIs (JWT)
# ----------------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_addresses(request):
    qs = Address.objects.filter(user=request.user).order_by("-is_default", "-id")
    return Response(AddressSerializer(qs, many=True).data)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_address(request):
    serializer = AddressSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    is_default = serializer.validated_data.get("is_default", False)
    if is_default:
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

    obj = serializer.save(user=request.user)
    return Response(AddressSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(["PUT"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_address(request, address_id):
    address = Address.objects.filter(id=address_id, user=request.user).first()
    if not address:
        return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = AddressSerializer(address, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    is_default = serializer.validated_data.get("is_default", address.is_default)
    if is_default:
        Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)

    obj = serializer.save()
    return Response(AddressSerializer(obj).data)


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_address(request, address_id):
    deleted, _ = Address.objects.filter(id=address_id, user=request.user).delete()
    if deleted == 0:
        return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "Address deleted"}, status=status.HTTP_200_OK)


# ----------------------------
# Auth APIs
# ----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username & password required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

    User.objects.create_user(username=username, password=password)
    return Response({"message": "Registered successfully"}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if not user:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    res = Response({
        "access": access,
        "refresh": str(refresh),
        "message": "Login success"
    }, status=status.HTTP_200_OK)

    #  cookie so checkout_page can read JWT
    res.set_cookie(
        key="access",
        value=access,
        httponly=True,
        samesite="Lax",
        secure=False  # True when HTTPS
    )
    return res


# ----------------------------
# OTP APIs
# ----------------------------


def send_sms(to_number: str, body: str) -> str:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not account_sid or not auth_token or not from_number:
        raise RuntimeError("Twilio credentials missing in .env")

    client = Client(account_sid, auth_token)
    msg = client.messages.create(
        body=body,
        from_=from_number,
        to=to_number
    )
    return msg.sid



@api_view(["GET"])
@permission_classes([AllowAny])
def send_otp(request):
    mobile = request.GET.get("mobile")
    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return Response({"error": "Invalid mobile"}, status=400)

    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")
    if not service_sid:
        return Response({"error": "TWILIO_VERIFY_SERVICE_SID missing"}, status=500)

    to_number = f"+91{mobile}"

    client = twilio_client()
    client.verify.v2.services(service_sid).verifications.create(
        to=to_number,
        channel="sms"
    )
    return Response({"message": "OTP sent"})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    mobile = (request.data.get("mobile") or "").strip()
    otp = (request.data.get("otp") or "").strip()

    # ✅ optional fields (from signup step)
    name = (request.data.get("name") or "").strip()
    email = (request.data.get("email") or "").strip()
    gender = (request.data.get("gender") or "").strip()   # "Female" / "Male"
    invite_code = (request.data.get("invite_code") or "").strip()  # optional

    if not mobile or not otp:
        return Response(
            {"success": False, "message": "Mobile and OTP required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(mobile) != 10 or not mobile.isdigit():
        return Response(
            {"success": False, "message": "Invalid mobile"},
            status=status.HTTP_400_BAD_REQUEST
        )

    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")
    if not service_sid:
        return Response({"error": "TWILIO_VERIFY_SERVICE_SID missing"}, status=500)

    to_number = f"+91{mobile}"

    # ✅ verify with Twilio Verify
    client = twilio_client()
    check = client.verify.v2.services(service_sid).verification_checks.create(
        to=to_number,
        code=otp
    )

    if check.status != "approved":
        return Response({"success": False, "message": "Invalid OTP"}, status=400)

    # ✅ create user (username = mobile)
    user, created = User.objects.get_or_create(username=mobile)

    # ✅ save name/email only if provided (AJIO setup step)
    if name:
        user.first_name = name
    if email:
        user.email = email
    user.save()

    # ✅ create/update profile once
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.phone = mobile

    # if screen_name empty, set it
    if not profile.screen_name:
        profile.screen_name = user.first_name or user.username

    # save gender if provided
    if gender in ["Female", "Male"]:
        profile.gender = gender

    # NOTE: invite_code not stored in your model (you can add field if needed)
    profile.save()

    # ✅ generate JWT
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    res = Response({
        "success": True,
        "access": access,
        "refresh": str(refresh),
        "username": user.username,
        "user_id": user.id,

        #  send name for topbar
        "first_name": user.first_name,
        "email": user.email,
        "screen_name": profile.screen_name,
        "phone": profile.phone,
        "gender": profile.gender,
    }, status=status.HTTP_200_OK)

    #  cookie (optional)
    res.set_cookie("access", access, httponly=True, samesite="Lax", secure=False)
    return res

#  check if mobile user already exists
@api_view(["GET"])
@permission_classes([AllowAny])
def check_mobile(request):
    mobile = request.GET.get("mobile", "").strip()
    if len(mobile) != 10 or not mobile.isdigit():
        return Response({"error": "Invalid mobile"}, status=400)

    exists = User.objects.filter(username=mobile).exists()
    return Response({"exists": exists})



@api_view(["GET", "PUT"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def me_profile(request):
    # ensure profile exists
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "GET":
        data = {
            "first_name": request.user.first_name or "",
            "last_name": request.user.last_name or "",
            "email": request.user.email or "",
            "screen_name": profile.screen_name or "",
            "phone": profile.phone or request.user.username,  # username = mobile in your OTP system
            "gender": profile.gender or "",
            "dob": profile.dob,
        }
        return Response(data)

    # PUT
    serializer = MeProfileSerializer(data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    v = serializer.validated_data

    # Update User fields
    if "first_name" in v:
        request.user.first_name = v["first_name"]
    if "last_name" in v:
        request.user.last_name = v["last_name"]
    if "email" in v:
        request.user.email = v["email"]
    request.user.save()

    # Update Profile fields
    if "screen_name" in v:
        profile.screen_name = v["screen_name"]
    if "phone" in v:
        profile.phone = v["phone"]
    if "gender" in v:
        profile.gender = v["gender"]
    if "dob" in v:
        profile.dob = v["dob"]
    profile.save()

    # return fresh data
    out = {
        "first_name": request.user.first_name or "",
        "last_name": request.user.last_name or "",
        "email": request.user.email or "",
        "screen_name": profile.screen_name or "",
        "phone": profile.phone or request.user.username,
        "gender": profile.gender or "",
        "dob": profile.dob,
    }
    return Response(out)
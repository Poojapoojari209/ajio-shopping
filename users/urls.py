from django.urls import path
from . import views

urlpatterns = [

    # ---------- AUTH ----------
    path("register/", views.register, name="register"),
    path("login/", views.login_api, name="login_api"),          # username + password
    path("send-otp/", views.send_otp, name="send_otp"),         # OTP send
    path("verify-otp/", views.verify_otp, name="verify_otp"),   # OTP verify + JWT cookie

     # check mobile exists
    path("check-mobile/", views.check_mobile, name="check_mobile"),

    # ---------- ADDRESS (JWT PROTECTED) ----------
    path("addresses/", views.my_addresses, name="my_addresses"),
    path("addresses/add/", views.add_address, name="add_address"),
    path("addresses/update/<int:address_id>/", views.update_address, name="update_address"),
    path("addresses/delete/<int:address_id>/", views.delete_address, name="delete_address"),

    # Personal Information API (ADD THIS)
    path("me/", views.me_profile, name="me_profile"),
]
from django.urls import path
from . import views

urlpatterns = [
    # -------- PAGES (HTML) --------
    path("checkout/", views.checkout_page, name="checkout_page"),
    path("payment-page/", views.payment_page, name="payment_page"),  # <-- HTML page

    # -------- APIs --------
    path("create/", views.create_order, name="create_order"),
    path("my/", views.my_orders, name="my_orders"),
    path("payment/", views.create_payment, name="create_payment"),
    path("detail/<int:order_id>/", views.order_detail_api, name="order_detail_api"),

    path("review/submit/", views.submit_rating, name="submit_rating"),

    path("admin/status/<int:order_id>/", views.admin_update_order_status),

    path("cancel/<int:order_id>/", views.cancel_order_api, name="cancel_order_api"),

    # -------- Razorpay APIs --------
    path("razorpay/create-order/", views.razorpay_create_order, name="razorpay_create_order"),
    path("razorpay/verify/", views.razorpay_verify, name="razorpay_verify"),


]

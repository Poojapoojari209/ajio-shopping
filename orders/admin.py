from django.contrib import admin
from .models import *

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price", "size")

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "note", "created_at")
    ordering = ("-created_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email")
    list_editable = ("status",)

    inlines = [OrderItemInline, OrderStatusHistoryInline]

    actions = ["mark_confirmed", "mark_shipped", "mark_delivered", "mark_cancelled"]

    def _push_history(self, queryset, status, note=""):
        for order in queryset:
            if order.status != status:
                order.status = status
                order.save(update_fields=["status"])
                OrderStatusHistory.objects.create(order=order, status=status, note=note)

    def mark_confirmed(self, request, queryset):
        self._push_history(queryset, "CONFIRMED", "Marked confirmed by admin")
    mark_confirmed.short_description = "Mark selected orders as CONFIRMED"

    def mark_shipped(self, request, queryset):
        self._push_history(queryset, "SHIPPED", "Marked shipped by admin")
    mark_shipped.short_description = "Mark selected orders as SHIPPED"

    def mark_delivered(self, request, queryset):
        self._push_history(queryset, "DELIVERED", "Marked delivered by admin")
    mark_delivered.short_description = "Mark selected orders as DELIVERED"

    def mark_cancelled(self, request, queryset):
        self._push_history(queryset, "CANCELLED", "Marked cancelled by admin")
    mark_cancelled.short_description = "Mark selected orders as CANCELLED"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "payment_method", "payment_status", "transaction_id")
    list_filter = ("payment_method", "payment_status")


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "note", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order__id",)


# Register your models here.
# admin.site.register(Order)     # orders
admin.site.register(OrderItem)
# admin.site.register(Payment)
from django.db import models
from django.contrib.auth.models import User
from products.models import Product, ProductSize

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, null=True, blank=True)  # size
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product", "size") 


    def __str__(self):
        return f"{self.product.name} - {self.size.size} x {self.quantity}"



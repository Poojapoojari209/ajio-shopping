from django.db import models
from django.contrib.auth.models import User

class Address(models.Model):
    ADDRESS_TYPES = (
        ("HOME", "Home"),
        ("WORK", "Work"),
        ("OTHER", "Other"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=10)
    pincode = models.CharField(max_length=10)
    area = models.CharField(max_length=255)
    address_line = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default="HOME")
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # if this address is default, make others false
        if self.is_default:
            Address.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.city}"

class OTP(models.Model):
    mobile = models.CharField(max_length=10)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mobile} - {self.otp}"
    

# profile(personal information)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    screen_name = models.CharField(max_length=80, blank=True, null=True)
    phone = models.CharField(max_length=10, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)  # Female / Male
    dob = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} profile"
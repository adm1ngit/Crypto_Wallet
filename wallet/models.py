from django.contrib.auth.models import User
from django.db import models

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, unique=True)
    private_key = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} - {self.address}"

class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    to_address = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    tx_hash = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
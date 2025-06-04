from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Wallet
from .utils import create_eth_wallet

@receiver(post_save, sender=User)
def create_wallet_for_user(sender, instance, created, **kwargs):
    if created:
        address, private_key = create_eth_wallet()
        Wallet.objects.create(user=instance, address=address, private_key=private_key)

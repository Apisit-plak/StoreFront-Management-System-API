from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User, UserRole
from orders.models import Cart


@receiver(post_save, sender=User)
def create_cart_for_buyer(sender, instance, created, **kwargs):
    if created and instance.role == UserRole.BUYER:
        Cart.objects.get_or_create(user=instance)

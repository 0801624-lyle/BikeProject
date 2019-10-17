from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import UserProfile

# @receiver(post_save, sender=User, dispatch_uid='save_new_user_profile')
# def create_or_save_user_profile(sender, instance, created, **kwargs):
#     """ Creates a UserProfile instance whenever a new User is created """
#     if created:
#         # The instance arg is the User instance that triggered the signal
#         UserProfile.objects.create(user=instance)
#     else:
#         instance.userprofile.save()
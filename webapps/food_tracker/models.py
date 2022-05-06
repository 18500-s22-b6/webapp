import datetime
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import AbstractUser
import time

import os
from django.conf import settings

from .constants import *

class User(AbstractUser):
    phone_number = PhoneNumberField(null = False, blank = False)
    image_url = models.CharField(max_length=200)
    id = models.AutoField(primary_key=True)


# Cabinet and Device are synonymous, in case of documentation discrepancy
class Device(models.Model):
    serial_number = models.CharField(max_length=32)
    status = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(blank=True, max_length = 50)
    most_recent_image = models.ImageField(blank=True, null=True, upload_to='images/user_bg_images/')
    key = models.CharField(max_length = 100)
    last_ping = models.DateTimeField(editable=True, auto_now_add=True)
    last_val = models.IntegerField(default=0)

    def update_online_status(self):
        if self.status != NOT_REGISTERED:
            if datetime.datetime.now().astimezone(datetime.timezone.utc) - self.last_ping  > datetime.timedelta(minutes=5):
                self.status = OFFLINE
            else:
                self.status = ONLINE
            self.save()

    def __str__(self):
        return "Device(id=" + str(self.serial_number) \
                      + ", " + "status=" + str(self.status) \
                      + ", " + "owner=" + str(self.owner) \
                      + ", " + "name=" + str(self.name) \
                      + ", " + "key=" + str(self.key) \
                      + ")"


# General item classes, in case of documentation discrepancy
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    user_gen = models.BooleanField()
    creator = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    desc_folder = models.CharField(max_length = 200) # extended max len

    def __str__(self):
        return "" + str(self.name)


# Instances of grocery items
class ItemEntry(models.Model):
    id = models.AutoField(primary_key=True)
    location = models.ForeignKey(Device, on_delete=models.PROTECT)
    type = models.ForeignKey(Category, on_delete=models.PROTECT)
    # image = models.ImageField(upload_to= f'images/ItemEntries/', null=True, blank=True)
    thumbnail = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return "ItemEntry(id=" + str(self.id) \
                      + ", " + "location=" + str(self.location) \
                      + ", " + "type=" + str(self.type) \
                      + ", " + "thumbnail=" + str(self.thumbnail) \
                      + ")"



# User recipes
class Recipe(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    ingredients = models.ManyToManyField(Category, blank=True)

class PublicRecipe(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=50)
    ingredients = models.ManyToManyField(Category, blank=True)

# User registered Iconic images
# May have an associated ItemEntry, which will have it's category updated
# When the image is identified by the
class IconicImage(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to= f'images/user_registered_iconic_images/')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    associated_item_entry = models.ForeignKey(ItemEntry, on_delete=models.SET_NULL, blank=True, null=True)


# def register_defaults():
#     for default_item in ["Applesauce", "BakingPowder", "Beans", "Ceereal", "Crackers", "CrushedTomatoes", "Milk", "Shredded cheese", "Spaghetti", "Yogurt"]:
#         try:
#             cat = Category.objects.get(name=default_item)
#         except:
#             cat = Category(name=default_item,
#                                 user_gen=False,
#                                 creator= None,
#                                 desc_folder='n/a')
#             cat.save()

# register_defaults()

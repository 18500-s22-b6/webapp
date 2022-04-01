from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class User(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_number = PhoneNumberField(unique = True, null = False, blank = False)
    email = models.EmailField(max_length=200)
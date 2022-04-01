from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class User(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_number = PhoneNumberField(unique = True, null = False, blank = False)
    email = models.EmailField(max_length=200)

# Cabinet and Device are synonymous, in case of documentation discrepancy
class Device(models.Model):
    serial_number = models.IntegerField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length = 50)
    most_recent_image = models.ImageField()
    key = models.CharField(max_length = 50)

    def __str__(self):
        return "Device(id=" + str(self.serial_number) \
                      + ", " + "status=" + str(self.status) \
                      + ", " + "owner=" + str(self.owner) \
                      + ", " + "name=" + str(self.name) \
                      + ", " + "key=" + str(self.key) \
                      + ")"

# Instances of grocery items
class ItemEntry(models.Model):
    id = models.IntegerField(blank=True, null=True)
    location = models.ForeignKey(Device, on_delete=models.PROTECT)
    type = models.ForeignKey(Category, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)

    def __str__(self):
        return "ItemEntry(id=" + str(self.id) + ", " \
                      + "name=" + str(self.name) + ")"



# General item classes, in case of documentation discrepancy
class Category(models.Model):
    id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=50)
    user_gen = models.BooleanField()
    creator = models.ForeignKey(User, on_delete=models.PROTECT)
    desc_folder = models.CharField(max_length = 200) # extended max len

from django.db import models

# Create your models here.

class ItemEntry(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
    return "ItemEntry(id=" + str(self.id) + ", " \
                      + "name=" + str(self.name) + ")"
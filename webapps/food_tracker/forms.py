from django import forms
from food_tracker import models

class UserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ['first_name', 'last_name', 'phone_number']
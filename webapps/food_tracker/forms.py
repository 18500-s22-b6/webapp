# forms.py
# See ourlife > forms.py for similar model

from django import forms
from food_tracker.models import *

# ALL_USERS = [(user.username, str(user.first_name + " " + user.last_name))
#              for user in User.objects.all()]

class DeviceRegistrationForm(forms.Form):
    serial_number = forms.IntegerField() # TODO: CharField
    # TODO: some unique constraint
    status = forms.IntegerField()
    # owner = forms.Model(User, on_delete=models.PROTECT) 
    ##### We don't need to ask the user who the owner is
    name = forms.CharField(max_length = 50)
    key = forms.CharField(required=True, max_length = 50)

    ### TODO: form validation doesn't work
    ### Temporarily allow duplicate registrations, preferable over NULL regis
    
    # # Customizes form validation for the username field.
    # def clean_serial_number(self):
    #     # Confirms that the SN is not already present in the 
    #     # Device model database.
    #     serial_number = self.cleaned_data.get('username')
    #     if Device.objects.filter(serial_number__exact=serial_number):
    #         raise forms.ValidationError("Device is already registered.")

    #     # We must return the cleaned data we got from the cleaned_data dict
    #     return serial_number

  
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']

class RecipeForm(forms.Form):
    name = forms.CharField(max_length=50)
    ingredients = forms.ModelMultipleChoiceField( \
                                    queryset=Category.objects.all(), \
                                    widget=forms.CheckboxSelectMultiple, \
                                    required=False, \
                                    label="Ingredients") \

# forms.py
# See ourlife > forms.py for similar model

from django import forms
from food_tracker.models import User


# ALL_USERS = [(user.username, str(user.first_name + " " + user.last_name))
#              for user in User.objects.all()]

class DeviceRegistrationForm(forms.Form):
    serial_number = forms.IntegerField() # TODO: CharField
    status = forms.IntegerField()
    # owner = forms.Model(User, on_delete=models.PROTECT) #####
    name = forms.CharField(max_length = 50)
    key = forms.CharField(required=True, max_length = 50)

  # text = forms.CharField(required=False, max_length=10000, widget=forms.Textarea)
  # raw_location = forms.CharField(required=False, max_length=200, label="Location:")
  # shared_with = forms.ModelMultipleChoiceField(queryset=User.objects.all(),
  #                                              widget=forms.CheckboxSelectMultiple,
  #                                              required=False,
  #                                              label="Share with:")
  # image_data = forms.CharField(widget=forms.HiddenInput(), required=False)

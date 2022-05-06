# forms.py
# See ourlife > forms.py for similar model

from unicodedata import category
from django import forms
from django.db.models import Q
from food_tracker.models import *

#####
# https://stackoverflow.com/questions/3695754/django-customizing-display-of-modelmultiplechoicefield
from django.forms.models import ModelMultipleChoiceField, ModelChoiceField
from django.forms import ValidationError

class MyModelMultipleChoiceField(ModelMultipleChoiceField):

    def label_from_instance(self, obj):
        return "%s" % (obj.name)
#####


class DeviceRegistrationForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['serial_number', 'name']
    name = forms.CharField(required=True)

    # # Customizes form validation for the username field.
    # def clean_serial_number(self):
    #     # Confirms that the SN is not already present in the
    #     # Device model database.
    #     serial_number = self.cleaned_data.get('username')
    #     if Device.objects.filter(serial_number__exact=serial_number):
    #         raise forms.ValidationError("Device is already registered.")

    #     # We must return the cleaned data we got from the cleaned_data dict
    #     return serial_number

class UpdateDeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['name']
    name = forms.CharField(required=True)

class DeleteDeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['name']
    name = forms.CharField(required=True)

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['name', 'ingredients']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(RecipeForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['ingredients'].queryset = Category.objects\
                            .filter(Q(creator=user) | Q(creator=None))\
                            .exclude(name="UNKNOWN ITEM")

    name = forms.CharField(max_length=50)
    ingredients = MyModelMultipleChoiceField(
                        queryset=Category.objects.all(),\
                        widget=forms.CheckboxSelectMultiple, \
                        required=True, \
                        label="Ingredients")

class ImageIdForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ImageIdForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects\
                            .filter(Q(creator=user) | Q(creator=None))\
                            .exclude(name="UNKNOWN ITEM")

    category = ModelChoiceField( \
                                    queryset=Category.objects.all(), \
                                    widget=forms.Select, \
                                    required=False, \
                                    label="Please identify the above item as an existing category")

    new_category_name = forms.CharField(max_length=50, required=False, label="Alternatley, create a custom catagory for the above item")

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('new_category_name') and not cleaned_data.get('category'):  # This will check for None or Empty
            raise ValidationError({'new_category_name': 'Even one of new_category_name or category should have a value.'})
        if cleaned_data.get('new_category_name') and cleaned_data.get('category'):
            raise ValidationError({'new_category_name': 'new_category_name and category should not both have a value at the same time.'})

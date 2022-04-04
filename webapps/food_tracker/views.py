from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse

from food_tracker.models import *
from food_tracker.forms import *

import requests

from .models import *
from .forms import DeviceRegistrationForm

def home(request):
  if request.user.is_authenticated:
    return redirect('profile')
  return render(request, 'home.html', {})

def login(request):
  if request.user.is_authenticated:
    return redirect('profile')

  return render(request, 'login.html')

@login_required
def profile(request):
  if not request.user.phone_number:
    return redirect('register_user')
  
  return render(request, 'profile.html')

@login_required
def register_user(request):
  context = {}
  user = request.user

  if request.method == 'POST':
    form = UserForm(request.POST)
    if form.is_valid():
      for (key, value) in form.cleaned_data.items():
        setattr(user, key, value)
      user.save()
      return redirect('profile')
    else:
      context['form'] = form
      return render(request, 'register_user.html', context)

  context['form'] = UserForm(instance=user)

  return render(request, 'register_user.html', context)

@login_required
def logout_user(request):
  if request.user.social_auth.filter(provider='facebook'):
    # Revoke access token
    data = request.user.social_auth.get(provider='facebook').extra_data
    # https://developers.facebook.com/docs/facebook-login/permissions/requesting-and-revoking#revokelogin
    response = requests.delete(
      'https://graph.facebook.com/v13.0/me/permissions',
      params={'access_token': data['access_token']})
    print(response.json())

  logout(request)
  return redirect('home')

@login_required # TODO: remove later
def dashboard(request):
  return render(request, 'dashboard.html', {})

@login_required
def cabinet(request):
  return render(request, 'inv.html', {})

@login_required
def register_device(request):
  if request.method == 'GET':
    context = {'form': DeviceRegistrationForm()}
    # Logged in users shouldn't share posts with themselves
    # context['form'].fields['shared_with'].queryset = \
    #   context['form'].fields['shared_with'].queryset.exclude(id=request.user.id)
    return render(request, 'add_device.html', context)

  form = DeviceRegistrationForm(request.POST)
  # form.fields['shared_with'].queryset = form.fields['shared_with'].queryset.exclude(id=request.user.id)
  if not form.is_valid():
    context = {'form': form}
    return render(request, 'add_device.html', context)

  new_user = User(first_name = "fn_TEST",
                  last_name = "ln_TEST",
                  phone_number = "pn_TEST", 
                  email = "email@email.com")
  new_user.save()

  new_device = Device(serial_number=form.cleaned_data["serial_number"],
                      status=form.cleaned_data["status"],
                      owner=new_user, 
                      name=form.cleaned_data["name"],
                      most_recent_image=None, 
                      key=form.cleaned_data["key"])
  new_device.save()

  print("asdfasdfasdfasdf")
  return render(request, 'add_device.html', context)

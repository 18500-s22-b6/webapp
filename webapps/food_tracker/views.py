from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

import requests

from .userinfo import get_userinfo
from .models import *
from .forms import DeviceRegistrationForm

def home(request):
  return render(request, 'home.html', {})

@login_required
def profile(request):
  data = get_userinfo(request)
  print(data)

  context = {
    'user': {
      **data,
      'is_superuser': request.user.is_superuser,
    }
  }

  return render(request, 'profile.html', context)

@login_required
def register_user(request):
  return render(request, 'registration.html')

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


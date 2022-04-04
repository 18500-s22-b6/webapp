from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from django.contrib import messages

import requests

from .models import *
from .forms import *

# Device status
NOT_REGISTERED = 0
ONLINE = 1

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

  context = {'devices': Device.objects.filter(owner=request.user)}
  
  if User.objects.filter(email=request.user.email):
    return render(request, 'profile.html', context)
  
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
  context = {}
  context['devices'] = Device.objects.filter(owner=request.user)

  if 'message' in request.session:
    context['message'] = request.session['message']
    del request.session['message']

  return render(request, 'dashboard.html', context)

@login_required
def cabinet(request, id):
  # Request for a specific cabinet
  context = {}

  if not Device.objects.filter(id=id).exists():
    request.session['message'] = 'Invalid device ID'
    return redirect('dashboard')

  device = Device.objects.get(id=id)
  context = { 
    'devices': Device.objects.filter(owner=request.user), 
    'device': device,
    'items': ItemEntry.objects.filter(location=device)
  }
  return render(request, 'inv.html', context)

@login_required
def register_device(request):
  context = {}

  if request.method == 'GET':
    num = len(Device.objects.filter(owner=request.user))
    form = DeviceRegistrationForm(initial={'name': f'device-{num}'})
    context['form'] = form
    return render(request, 'add_device.html', context)

  form = DeviceRegistrationForm(request.POST)
  if not form.is_valid():
    context['form'] = form
    return render(request, 'add_device.html', context)

  try:
    device = Device.objects.get(serial_number=form.cleaned_data["serial_number"])
  except Exception as e:
    request.session['message'] = 'Invalid serial number'
    return redirect('dashboard')
  
  if device.status != NOT_REGISTERED:
    if device.owner == request.user:
      request.session['message'] = 'You have already registered this device'
    else:
      request.session['message'] = 'Invalid serial number'
    return redirect('dashboard')
  
  device.status = ONLINE
  device.owner = request.user
  for key, value in form.cleaned_data.items():
    setattr(device, key, value)
  device.save()

  # v1: Redirect to add_device
  # Problem: refresh adds duplicate devices
  # context['message'] = "Registration successful!" 
  # return render(request, 'add_device.html', context)

  # v2: Django messages
  # TODO: update to use
  # messages.success(request, "parameter")

  # v3: functional 'session' workaround
  # stackoverflow.com/questions/51155947/django-redirect-to-another-view-with-context
  request.session['message'] = "Registration successful!"
  return redirect('dashboard')

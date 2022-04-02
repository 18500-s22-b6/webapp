from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages

import requests

from .userinfo import get_userinfo
from .models import *
from .forms import *

def home(request):
  return render(request, 'home.html', {})

@login_required
def profile(request):
  data = get_userinfo(request)
  print(data)

  context = get_context_by_user_data(request, data)
  context['devices'] = Device.objects.all()
  
  if User.objects.filter(email=data['email']):
    return render(request, 'profile.html', context)
  
  return redirect('register_user')

@login_required
def register_user(request):
  data = get_userinfo(request)
  context = get_context_by_user_data(request, data)
  
  try:
    user = User.objects.get(email=data['email'])
    form = UserForm(instance=user)
  except Exception:
    user = User(
      first_name=data['first_name'],
      last_name=data['last_name'],
      email=data['email'],
    )
    form = UserForm()

  context['form'] = form

  if request.method == 'POST':
    form = UserForm(request.POST)
    if form.is_valid():
      user.first_name = form.cleaned_data['first_name']
      user.last_name = form.cleaned_data['last_name']
      user.phone_number = form.cleaned_data['phone_number']
      user.save()
      return redirect('profile')
    else:
      context['form'] = form
      return render(request, 'register_user.html', context)

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
  context = { 'devices': Device.objects.all() }

  if 'message' in request.session:
    context = { 'devices': Device.objects.all(), 
              'message': request.session['message'] }
    del request.session['message']

  return render(request, 'dashboard.html', context)

@login_required
def cabinet(request, id):
  # Request for a specific cabinet

  dev = Device.objects.get(id=id)

  print("request:")
  print(request)
  print("id: " + str(id))
  context = { 'devices': Device.objects.all(), 
              'device': Device.objects.get(id=id),
              'items': ItemEntry.objects.filter(location=dev)}
  return render(request, 'inv.html', context)

@login_required
def register_device(request):

  ##### If GET, the user just clicked on the link
  ##### i.e. just render the website, plain and simple
  if request.method == 'GET':
    context = { 'form': DeviceRegistrationForm(), 
                'devices': Device.objects.all() }
    return render(request, 'add_device.html', context)


  ##### If POST, "submit" button was pressed
  form = DeviceRegistrationForm(request.POST)
  if not form.is_valid():
    context = {'form': form, 'devices': Device.objects.all()}
    return render(request, 'add_device.html', context)

  # temp_user = User(first_name = "fn_TEST",
  #                 last_name = "ln_TEST",
  #                 phone_number = "pn_TEST", 
  #                 email = "email@email.com")
  data = get_userinfo(request)
  context = get_context_by_user_data(request, data)
  context['devices'] = Device.objects.all()
  
  temp_user = User.objects.get(email=data['email']) 
  # TODO: change when done debugging to email=data['email']

  new_device = Device(serial_number=form.cleaned_data["serial_number"],
                      status=form.cleaned_data["status"],
                      owner=temp_user, 
                      name=form.cleaned_data["name"],
                      most_recent_image=None, 
                      key=form.cleaned_data["key"])
  new_device.save()

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

def get_context_by_user_data(request, data):
  context = {
    'user': {
      **data,
      'is_superuser': request.user.is_superuser,
    }
  }
  return context

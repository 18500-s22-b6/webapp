from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from django.contrib import messages

import requests

from .models import *
from .forms import *

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

  context = {'devices': Device.objects.all()}
  
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

@login_required
def dashboard(request):
  context = { 'devices': Device.objects.all() }

  if 'message' in request.session:
    context = { 'devices': Device.objects.all(), 
              'message': request.session['message'] }
    del request.session['message']

  return render(request, 'dashboard.html', context)

@login_required
def recipes(request):
  context = { 'devices': Device.objects.all() }

  if 'message' in request.session:
    context = { 'devices': Device.objects.all(), 
              'message': request.session['message'] }
    del request.session['message']

  return render(request, 'recipes.html', context)

@login_required
def add_recipe(request):
  
  ##### If GET, the user just clicked on the link
  ##### i.e. just render the website, plain and simple
  if request.method == 'GET':
    context = { 'form': RecipeForm(), 
                'devices': Device.objects.all() }
    return render(request, 'add_recipe.html', context)
  
  ##### If POST, "submit" button was pressed
  form = RecipeForm(request.POST)
  if not form.is_valid():
    context = {'form': form, 'devices': Device.objects.all()}
    return render(request, 'add_recipe.html', context)

  context = {'devices': Device.objects.all()}
  
  temp_user = User.objects.get(email=request.user.email) 
  # TODO: change when done debugging to email=data['email']

  new_recipe = Recipe(author = temp_user, 
                      name = form.cleaned_data["name"], 
                      ingredients = form.cleaned_data["ingredients"])
  new_recipe.save()

  request.session['message'] = "Registration successful!"
  return redirect('recipes')
  # return render(request, 'recipes.html', context)

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

  context = {'devices': Device.objects.all()}
  
  temp_user = User.objects.get(email=request.user.email) 
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

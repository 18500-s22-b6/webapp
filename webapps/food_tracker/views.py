from django.shortcuts import redirect, render, get_object_or_404
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
  context = { 'devices': Device.objects.all(), 
              'recipes': Recipe.objects.filter(), 
              'items':ItemEntry.objects.all() }

  if 'message' in request.session:
    context = { 'devices': Device.objects.all(),
                'recipes': Recipe.objects.all(),
                'items':ItemEntry.objects.all(),
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
  
  user = request.user
  # TODO: change when done debugging to email=data['email']

  new_recipe = Recipe(author = user, 
                      name = form.cleaned_data["name"])
                      # ingredients = form.cleaned_data["ingredients"]
  new_recipe.save()
  new_recipe.ingredients.set(form.cleaned_data["ingredients"])

  request.session['message'] = "Registration successful!"
  return redirect('recipes')
  # return render(request, 'recipes.html', context)

@login_required
def cabinet(request, id):
  # Request for a specific cabinet

  dev = Device.objects.get(id=id)

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

  context = {'devices': Device.objects.all()}
  
  user = request.user

  new_device = Device(serial_number=form.cleaned_data["serial_number"],
                      status=form.cleaned_data["status"],
                      owner=user, 
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

@login_required
def delete_device(request, id):
# See addrbook2 for example

  context = { 'devices': Device.objects.all() }

  if request.method != 'POST':
    message = 'Invalid request.  POST method must be used.'
    context['message'] = message
    return render(request, 'dashboard.html', context)

  entry = get_object_or_404(Device, id=id)
  message = 'Cabinet {0} has been deleted.'.format(entry.name)
  entry.delete()

  # OJO: recreate device list after deleting the device (duh)
  context = { 'devices': Device.objects.all(), 
              'message': message }

  return render(request, 'dashboard.html', context)

def get_context_by_user_data(request, data):
  context = {
    'user': {
      **data,
      'is_superuser': request.user.is_superuser,
    }
  }
  return context

@login_required
def add_item(request, id):
#KNOWN BUGS: empty field error redirect not working

    # Set context with current list of items so we can easily return if we discover errors.
    context = { 'items': ItemEntry.objects.all() }

    # Adds the new item to the database if the request parameter is present
    if 'item' not in request.POST or not request.POST['item']:
        context['message'] = 'You must enter an item to add.'
        return render(request, 'inv.html', context)

    # data = get_userinfo(request)
    # print(data)
    # user = User.objects.get(email=data['email']) 
    user = request.user
    loc = Device.objects.get(id=id)
    new_cat = Category(name=request.POST['item'],
                       user_gen=True, 
                       creator=user, 
                       desc_folder='n/a')
    new_cat.save()

    # cat = Category.objects.get(name="Custom")

    new_item = ItemEntry(location=loc, 
                         type=new_cat, # cat
                         thumbnail="")
    new_item.save()
    
    return redirect('cabinet', id)

@login_required
def delete_item(request, id):

  context = { 'devices': Device.objects.all() }

  if request.method != 'POST':
    message = 'Invalid request.  POST method must be used.'
    context['message'] = message
    return render(request, 'inv.html', context)

  entry = get_object_or_404(ItemEntry, id=id)
  cab_id = entry.location.id
  # TODO: determine how necessary the message actually is
  message = 'Item {0} has been deleted.'.format(entry.type.name)
  entry.delete()

  context = { 'devices': Device.objects.all(), 
              'items': ItemEntry.objects.all(),
              'message': message }
  print(context)

  # return render(request, 'inv.html', context)
  return redirect('cabinet', cab_id)

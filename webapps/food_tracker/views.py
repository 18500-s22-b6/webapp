import imp
from http.client import METHOD_NOT_ALLOWED
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from django.contrib import messages


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import jsonschema
import hashlib
import io
from PIL import Image
import base64
from django.core.files.base import ContentFile

#import cv module
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv_code"))
import cv_code_main as cv_code

from .models import *
from .forms import *
import numpy as np

# Device status
NOT_REGISTERED = 0
ONLINE = 1
OFFLINE = 2

# HTTP Status Codes
SUCCESS = 200
BAD_REQUEST = 400
FORBIDDEN = 403
METHOD_NOT_ALLOWED = 405

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

  context = {
    'devices': Device.objects.filter(owner=request.user),
    "unkown_items": IconicImage.objects.filter(user=request.user, category__name="UNKNOWN ITEM"), #TODO: filter by category
    }

  if 'message' in request.session:
    context['message'] = request.session['message']
    del request.session['message']

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
  context = {}
  context['devices'] = Device.objects.filter(owner=request.user)

  for device in context['devices']:
    device.update_online_status()

  if 'message' in request.session:
    context['message'] = request.session['message']
    del request.session['message']

  return render(request, 'dashboard.html', context)






@login_required
def recipes(request):
  context = { 'devices': Device.objects.filter(owner=request.user),
              # 'recipes': Recipe.objects.filter(author=request.user),
              'items':ItemEntry.objects.all() }

  if 'message' in request.session:
    context['message'] = request.session['message']
    del request.session['message']


  d = {}
  for recipe in Recipe.objects.all():
    # d[0] represents ingr that exist
    # d[1] represents ingr that are missing
    d[recipe.name] = [[] , []]
    for ingr in recipe.ingredients.all():
      if(ItemEntry.objects.filter(type=ingr)):
        d[recipe.name][0].append(ingr)
      else:
        d[recipe.name][1].append(ingr)

  context['recipes'] = d

  # User hit the button to generate a shopping list
  if request.method == 'POST':
    name = request.POST.get('recipe')
    l = d.get(name, None)
    if l:
      # TODO: print is a proxy for emailing the user
      print(l[1])
    else:
      print(name + " doesn't exist")
    return render(request, 'recipes.html', context)

  # Otherwise, regular recipes viewer
  return render(request, 'recipes.html', context)






@login_required
def add_recipe(request):

  ##### If GET, the user just clicked on the link
  ##### i.e. just render the website, plain and simple
  if request.method == 'GET':
    context = { 'form': RecipeForm(),
                'devices': Device.objects.filter(owner=request.user) }
    return render(request, 'add_recipe.html', context)

  ##### If POST, "submit" button was pressed
  form = RecipeForm(request.POST)
  if not form.is_valid():
    context = { 'form': form,
                'devices': Device.objects.filter(owner=request.user) }
    return render(request, 'add_recipe.html', context)

  context = {'devices': Device.objects.filter(owner=request.user) }

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
  context = { 'devices': Device.objects.filter(owner=request.user) }

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
# Assumption that all "approved" devices will already be added in the database
# New registrations simply assign owner to existing devices

  context = {}

  # First load (GET request), return empty form
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
    request.session['message'] = 'Invalid serial number (Error NF)'
    return redirect('dashboard')

  if device.status != NOT_REGISTERED:
    if device.owner == request.user:
      request.session['message'] = 'You have already registered this device'
    else:
      request.session['message'] = 'Device has already been registered (Error SE)'
    return redirect('dashboard')

  device.status = ONLINE
  device.owner = request.user
  for key, value in form.cleaned_data.items():
    setattr(device, key, value)
  device.save()

  # MESSAGE: Inform the user of successful registration
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

  context = { 'devices': Device.objects.filter(owner=request.user) }

  if request.method != 'POST':
    message = 'Invalid request.  POST method must be used.'
    context['message'] = message
    return render(request, 'dashboard.html', context)

  entry = get_object_or_404(Device, id=id)
  message = 'Cabinet {0} has been deleted.'.format(entry.name)
  entry.delete()

  # OJO: recreate device list after deleting the device (duh)
  context = { 'devices': Device.objects.filter(owner=request.user),
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

  context = { 'devices': Device.objects.filter(owner=request.user) }

  if request.method != 'POST':
    message = 'Invalid request.  POST method must be used.'
    context['message'] = message
    return render(request, 'inv.html', context)

  entry = get_object_or_404(ItemEntry, id=id)
  cab_id = entry.location.id
  # TODO: determine how necessary the message actually is
  message = 'Item {0} has been deleted.'.format(entry.type.name)
  entry.delete()

  context = { 'devices': Device.objects.filter(owner=request.user),
              'items': ItemEntry.objects.all(),
              'message': message }
  print(context)

  # return render(request, 'inv.html', context)
  return redirect('cabinet', cab_id)

@csrf_exempt
def update_inventory(request):
  if request.method != 'POST':
    return JsonResponse({
        'error': 'Only POST requests are supported'
      }, status=METHOD_NOT_ALLOWED)

  data = json.loads(request.body.decode('utf-8'))

  schema = {
    "type": "object",
    "properties": {
      "serial_number": {"type": "string"},
      "image": {"type": "string"},
      "secret": {"type": "string"},
    },
    "additionalProperties": False,
    "required": ["serial_number", "image", "secret"],
  }
  try:
    jsonschema.validate(instance=data, schema=schema)
  except jsonschema.exceptions.ValidationError as err:
    return JsonResponse({
      'error': 'Invalid request body'
    }, status=BAD_REQUEST)

  try:
    device = Device.objects.get(serial_number=data['serial_number'])
    if device.status == NOT_REGISTERED:
      raise Exception('Device is not registered')

    #TODO: do we need to hash this?
    # hashed_str = hashlib.sha256(data['secret'].encode()).hexdigest()
    if data['secret'] != device.key:
      raise Exception('Invalid secret')
  except Exception as e:
    print(e)
    return JsonResponse({
        'error': f'Invalid request: {e}'
      }, status=FORBIDDEN)

  # convert image back to PIL object
  img_bytes = base64.b64decode(data["image"].encode('utf-8'))
  cur_img_bytes_io = io.BytesIO(img_bytes)
  #update device image field
  image_field = device.most_recent_image
  try:
    old_bg_path = image_field.path
  except:
    old_bg_path = None
  device.most_recent_image.save(f"{device.owner.id}/bg.png", ContentFile(cur_img_bytes_io.getvalue()), save=True)
  device.save()

  #if we have no previous bg image, this is the first bg image
  if old_bg_path is None:
    return JsonResponse({'success': 'bg image updated'}, status=SUCCESS)

  new_image_path = image_field.path

  iconic_images = list(IconicImage.objects.all().filter(user=device.owner))
  iconic_dict = dict()
  for iconic_image in iconic_images:
    iconic_dict[iconic_image.category.name] = iconic_image.image.path

  #TODO: supply the iconic images which this user has registered as third argument
  best_guess = cv_code.get_best_guess_or_none(old_bg_path, new_image_path, iconic_dict)

  if isinstance(best_guess, str):

    try:
      cat = Category.objects.get(name=best_guess)
    except:
      cat = Category(name=best_guess,
                        user_gen=True,
                        creator=device.owner,
                        desc_folder='n/a')
      cat.save()


    new_item = ItemEntry(location=device,
                          type=cat, # cat
                          thumbnail="")
    new_item.save()
    return JsonResponse({'success': 'Inventory updated'}, status=SUCCESS)
  elif best_guess is None:
    return JsonResponse({'success': 'No change detected'}, status=SUCCESS)
  else:
    assert isinstance(best_guess, np.ndarray)
    import cv2
    _ret, buf = cv2.imencode('.jpg', best_guess)
    img_file = ContentFile(buf.tobytes())

    # In this case, we create an Iconic image for this user, with the default category "UNKNOWN ITEM"

    #create unknown Item category if it doesn't exist
    try:
      unknown_cat = Category.objects.get(name="UNKNOWN ITEM")
    except:
      unknown_cat = Category(name="UNKNOWN ITEM",
                       user_gen=True,
                       creator=device.owner,
                       desc_folder='n/a')
      unknown_cat.save()

    new_item = ItemEntry(location=device,
                          type=unknown_cat, # cat
                          thumbnail="")
    new_item.save()

    new_iconic_img = IconicImage(user=device.owner,
                                  category=unknown_cat,
                                  image = img_file,
                                  associated_item_entry = new_item,
                                  )
    #This addition image save is needed. I don't know if there is a better way to do this.
    new_iconic_img.image.save(f"unknown.png", img_file, save=True)
    new_iconic_img.save()

    return JsonResponse({'success': 'Unable to identify item'}, status=SUCCESS)


@login_required
def id_unknown_item(request, id):
  entry = get_object_or_404(IconicImage, id=id, user=request.user)

  if request.method == 'GET':
    context = {"entry": entry, 'form': ImageIdForm(), "id": id}
    return render(request, 'id_unknown_item.html', context)

  ##### If POST, "submit" button was pressed
  form = ImageIdForm(request.POST)
  if not form.is_valid():
    #TODO: raise a proper error
    context = {"entry": entry, 'form': ImageIdForm(), "id": id}
    return render(request, 'id_unknown_item.html', context)

  if form.cleaned_data["category"]:
    cat = form.cleaned_data["category"]
  else:
    assert form.cleaned_data["new_category_name"]
    cat =  Category(name=form.cleaned_data["new_category_name"],
                       user_gen=True,
                       creator=request.user,
                       desc_folder='n/a')
    cat.save()


  entry.category = cat
  entry.associated_item_entry.type = cat

  entry.save()
  entry.associated_item_entry.save()


  request.session['message'] = "Identification successful!"
  return redirect('profile')




def shopping_list(request):
  context = {}

  return




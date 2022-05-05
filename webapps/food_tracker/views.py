from http.client import METHOD_NOT_ALLOWED
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from django.contrib import messages
from django.core.mail import send_mail

from django.conf import settings
from django.http import JsonResponse, HttpResponse

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
from .constants import *
import numpy as np



def home(request):
  return render(request, 'home.html', {})



def login(request):
  if request.user.is_authenticated:
    return redirect('profile')
  return render(request, 'login.html')


def privacy(request):
  return render(request, 'privacy.html')



@login_required
def profile(request):
  # If this is their first time logging in
  if not request.user.phone_number:
    return redirect('register_user')

  context = { 'devices': get_and_update_status(request.user) }

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


  logout(request)

  messages.info(request, 'You have been logged out.')
  return redirect('home')



@login_required
def dashboard(request):
  context = {
    'devices': get_and_update_status(request.user),
    'recipes': Recipe.objects.filter(author=request.user)
  }

  return render(request, 'dashboard.html', context)



@login_required
def recipe(request, id):
  try:
    recipe = Recipe.objects.get(author=request.user, id=id)
  except Exception as e:
    messages.error(request, "Recipe doesn't exist")
    return redirect('dashboard')

  form = RecipeForm(instance=recipe)

  if request.method == 'POST':
    form = RecipeForm(request.POST)
    if form.is_valid():
      recipe.name = form.cleaned_data['name']
      recipe.ingredients.set(form.cleaned_data["ingredients"])
      recipe.save()

  context = {
    'form': form,
    'recipe': recipe,
    'public': False,
    'site_key': settings.GOOGLE_RECAPTCHA_KEY,
  }
  return render(request, 'recipe.html', context)



@login_required
def public_recipe(request, id):
  try:
    recipe = PublicRecipe.objects.get(id=id)
  except Exception as e:
    messages.error(request, "Recipe doesn't exist")
    return redirect('recipes')

  context = {
    'recipe': recipe,
    'public': True,
  }
  return render(request, 'recipe.html', context)



# <i class="fas fa-share-alt"></i>
@login_required
def publish_recipe(request, id):
  try:
    recipe = Recipe.objects.get(author=request.user, id=id)
  except Exception as e:
    messages.error(request, "Recipe doesn't exist")
    return redirect('dashboard')

  new_recipe = PublicRecipe(
    author=request.user,
    name=recipe.name,
  )
  new_recipe.save()
  new_recipe.ingredients.set(recipe.ingredients.all())

  messages.success(request, 'Recipe shared successfully')
  return redirect('public_recipe', new_recipe.id)


@login_required
def save_public_recipe(request, id):
  try:
    recipe = PublicRecipe.objects.get(id=id)
  except Exception as e:
    messages.error(request, "Recipe doesn't exist")
    return redirect('recipes')

  new_recipe = Recipe(
    author=request.user,
    name=recipe.name,
  )
  new_recipe.save()
  new_recipe.ingredients.set(recipe.ingredients.all())

  messages.success(request, 'Recipe created successfully')
  return redirect('recipe', new_recipe.id)



@login_required
def delete_recipe(request, id):
  try:
    recipe = Recipe.objects.get(author=request.user, id=id)
  except Exception as e:
    messages.error(request, "Recipe doesn't exist")
    return redirect('dashboard')

  if request.method == 'POST':
    recipe.delete()

  return redirect('dashboard')



@login_required
def email_grocery_list(request, id):
  try:
    recipe = Recipe.objects.get(author=request.user, id=id)
  except Exception as e:
    messages.error(request, "Recipe doesn't exist")
    return redirect('dashboard')

  if request.method == 'POST':
    recaptcha_response = request.POST.get('g-recaptcha-response')
    response = requests.post(
      url=RECAPTCHA_VERIFICATION_URL,
      data={
        'secret': settings.GOOGLE_RECAPTCHA_SECRET,
        'response': recaptcha_response,
      }).json()

    if not response['success']:
      messages.error(request, 'reCAPTCHA failed')
      return redirect('recipe', id)

    # Send email
    missing = []
    for i in recipe.ingredients.all():
      if not ItemEntry.objects.filter(type=i):
        missing.append(i)
    if not missing:
      message = "Everything is in stock'"
    else:
      message = str(missing)

    print(message)
    recipents = [request.user.email]
    send_mail(subject='FT Shopping List',
              message=message,
              from_email=settings.EMAIL_HOST_USER,
              recipient_list=recipents,
              fail_silently=False)
    print('sending email...')

    messages.success(request, 'Email sent successfully')
    return redirect('recipe', id)

  return redirect('recipe', id)



@login_required
def recipes(request):
  recipes = PublicRecipe.objects.all()
  context = {
    'recipes': recipes,
  }

  return render(request, 'recipes.html', context)



@login_required
def add_recipe(request):
  if request.method == 'GET':
    context = { 'form': RecipeForm(),
                'devices': get_and_update_status(request.user) }
    return render(request, 'add_recipe.html', context)

  ##### If POST, "submit" button was pressed
  form = RecipeForm(request.POST)
  if not form.is_valid():
    context = { 'form': form,
                'devices': get_and_update_status(request.user) }
    return render(request, 'add_recipe.html', context)

  user = request.user
  new_recipe = Recipe(author = user,
                      name = form.cleaned_data["name"])
                      # ingredients = form.cleaned_data["ingredients"]
  new_recipe.save()
  new_recipe.ingredients.set(form.cleaned_data["ingredients"])

  messages.success(request, 'Recipe saved successfully!')
  return redirect('recipe', new_recipe.id)



@login_required
def cabinet(request, id):
  # Request for a specific cabinet
  context = { 'devices': get_and_update_status(request.user) }

  if not Device.objects.filter(owner=request.user, serial_number=id).exists():
    messages.error(request, 'Invalid device ID')
    return redirect('dashboard')

  device = Device.objects.get(owner=request.user, serial_number=id)
  update_form = UpdateDeviceForm(instance=device)

  if request.method == "POST":
    update_form = UpdateDeviceForm(request.POST)
    if update_form.is_valid():
      for (key, value) in update_form.cleaned_data.items():
        setattr(device, key, value)
      device.save()

  delete_form = DeleteDeviceForm()
  context = {
    'update_form': update_form,
    'delete_form': delete_form,
    'devices': get_and_update_status(request.user),
    'device': device,
    'items': ItemEntry.objects.filter(location=device),
    # "unknown_items": IconicImage.objects.filter(user=request.user, category__name="UNKNOWN ITEM"),
    "unknown_items": list(map(
      lambda cat: IconicImage.objects.get(user=request.user, category=cat),
      [item.type for item in ItemEntry.objects.filter(location=device, type__name="UNKNOWN ITEM")]
    ))
  }
  return render(request, 'inventory.html', context)



@login_required
def register_device(request):
# Assumption that all "approved" devices will already be added in the database
# New registrations simply assign owner to existing devices

  context = {'device': get_and_update_status(request.user)}
  context['site_key'] = settings.GOOGLE_RECAPTCHA_KEY

  # First load (GET request), return empty form
  if request.method == 'GET':
    devices = Device.objects.filter(owner=request.user)
    num = len(devices)
    while f'Device {num}' in [d.name for d in devices]:
      num += 1
    form = DeviceRegistrationForm(initial={'name': f'Device {num}'})
    context['form'] = form
    return render(request, 'add_device.html', context)

  form = DeviceRegistrationForm(request.POST)
  context['form'] = form

  if not form.is_valid():
    return render(request, 'add_device.html', context)

  recaptcha_response = request.POST.get('g-recaptcha-response')
  response = requests.post(
    url=RECAPTCHA_VERIFICATION_URL,
    data={
      'secret': settings.GOOGLE_RECAPTCHA_SECRET,
      'response': recaptcha_response,
    }).json()

  if not response['success']:
    messages.error(request, 'reCAPTCHA failed')
    return render(request, 'add_device.html', context)

  try:
    device = Device.objects.get(serial_number=form.cleaned_data["serial_number"])
  except Exception as e:
    messages.error(request, 'Invalid serial number')
    return render(request, 'add_device.html', context)

  if device.status != NOT_REGISTERED:
    if device.owner == request.user:
      messages.warning(request, 'You have already registered this device')
    else:
      messages.error(request, 'Invalid serial number')
    return render(request, 'add_device.html', context)

  device.status = ONLINE
  device.owner = request.user
  for key, value in form.cleaned_data.items():
    setattr(device, key, value)
  device.save()

  messages.success(request, 'Device registration successful!')
  return redirect('dashboard')



@login_required
def delete_device(request, id):
  if not Device.objects.filter(owner=request.user, serial_number=id).exists():
    messages.error(request, 'Invalid device ID')
    return redirect('dashboard')

  device = Device.objects.get(serial_number=id)

  if request.method != 'POST':
    return redirect('dashboard')

  form = DeleteDeviceForm(request.POST)
  if form.is_valid():
    if form.cleaned_data['name'] == device.name:
      items = ItemEntry.objects.filter(location=device)

      device.owner = None
      device.status = NOT_REGISTERED
      device.save()

      items.delete()
      messages.info(request, 'Cabinet {0} has been deleted.'.format(device.name))
    else:
      messages.warning(request, "Input doesn't match device name")

  context = { 'devices': get_and_update_status(request.user) }

  return redirect('dashboard')



@login_required
def get_list_json_dumps_serializer(request, id):
  response_data = []
  items__in = ItemEntry.objects.filter(location__owner=request.user).filter(location__id=id)
  for model_item in items__in:
    my_item = {
      'id': model_item.id,
      'location': model_item.location.name,
      'type': model_item.type.name,
    }
    response_data.append(my_item)

  # dumps: no slashes, []
  # loads: list, gets mad
  # response_json = json.dumps(response_data, default=vars)
  # print(response_json)
  return JsonResponse(data=response_data, safe=False)

@csrf_exempt
def keep_alive(request):
  if request.method != 'POST':
    return JsonResponse({
        'error': 'Only POST requests are supported'
      }, status=METHOD_NOT_ALLOWED)

  data = json.loads(request.body.decode('utf-8'))
  if not validate_json(data):
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
    return JsonResponse({
        'error': f'Invalid request: {e}'
      }, status=FORBIDDEN)

  device.update_online_status()

  return HttpResponse("OK")

@csrf_exempt
def update_inventory(request):
  if request.method != 'POST':
    return JsonResponse({
        'error': 'Only POST requests are supported'
      }, status=METHOD_NOT_ALLOWED)

  data = json.loads(request.body.decode('utf-8'))
  if not validate_json(data):
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
    return JsonResponse({
        'error': f'Invalid request: {e}'
      }, status=FORBIDDEN)

  device.update_online_status()
  if data["timestamp"] <= device.last_val:
    return JsonResponse({
        'error': f'Invalid request: timestamp {data["timestamp"]} is older than last_val {device.last_val}'
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

  #get dict of custom registered iconic dict items
  iconic_images = list(IconicImage.objects.all().filter(user=device.owner))
  iconic_dict = dict()
  for iconic_image in iconic_images:
    iconic_dict[iconic_image.category.name] = iconic_image.image.path


  #get set of all categories currently in the inventory
  existing_categories = set(ItemEntry.objects.all().filter(location=device).values_list('type__name', flat=True))

  best_guess = cv_code.get_best_guess_or_none(old_bg_path, new_image_path, iconic_dict,existing_categories)

  if isinstance(best_guess, tuple):
    (best_guess_category_name, is_post) = best_guess

    if is_post:
      #new item has been added to the inventory
      try:
        cat = Category.objects.get(name=best_guess_category_name)
      except:
        cat = Category(name=best_guess_category_name,
                          user_gen=True,
                          creator=device.owner,
                          desc_folder='n/a')
        cat.save()

      new_item = ItemEntry(location=device,
                            type=cat, # cat
                            thumbnail="")
      new_item.save()
      return JsonResponse({'success': f'Inventory updated to include new item: {best_guess_category_name}'}, status=SUCCESS)
    else:
      #item has been removed from the inventory
      ItemEntry.objects.all().filter(location=device, type__name=best_guess_category_name).first().delete()
      return JsonResponse({'success': f'Removed item {best_guess_category_name}'}, status=SUCCESS)
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
  try:
    item = ItemEntry.objects.get(id=id)
    if item.location.owner != request.user:
      return redirect('dashboard')
  except Exception as e:
    return redirect('dashboard')

  iconic_images = IconicImage.objects.filter(user=request.user)
  entry = None
  for image in iconic_images:
    if image.associated_item_entry == item:
      entry = image
  if not entry:
    return redirect('dashboard')

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
    cat = Category(name=form.cleaned_data["new_category_name"],
                       user_gen=True,
                       creator=request.user,
                       desc_folder='n/a')
    cat.save()


  entry.category = cat
  entry.associated_item_entry.type = cat

  entry.save()
  entry.associated_item_entry.save()


  request.session['message'] = "Identification successful!"
  return redirect('dashboard')



################## Helper Functions ##################
def get_and_update_status(user):
  """helper function that gets all the devices for that user, and updates their online/offline status"""

  devices = Device.objects.filter(owner=user)

  for device in devices:
    device.update_online_status()

  return devices



def validate_json(data):
  schema = {
    "type": "object",
    "properties": {
      "serial_number": {"type": "string"},
      "image": {"type": "string"},
      "secret": {"type": "string"},
      "timestamp": {"type": "integer"},
    },
    "additionalProperties": False,
    "required": ["serial_number", "image", "secret", "timestamp"],
  }
  try:
    jsonschema.validate(instance=data, schema=schema)
  except jsonschema.exceptions.ValidationError as err:
    return False

  return True


################## Unused Functions ##################
def shopping_list(request):
  context = {}

  return



@login_required
def add_item(request, id, ajax):
# Param: id = cabinet number
#KNOWN BUGS: empty field error redirect not working

  # Set context with current list of items so we can easily return if we discover errors.
  context = { 'items': ItemEntry.objects.all() }

  # Adds the new item to the database if the request parameter is present
  if 'item' not in request.POST or not request.POST['item']:
    messages.warning(request, 'You must enter an item to add.')
    return render(request, 'inventory.html', context)

  user = request.user
  loc = Device.objects.get(id=id)

  # If the category doesn't exist, try
  try:
    new_cat = Category(name=request.POST['item'],
                       user_gen=True,
                       creator=user,
                       desc_folder='n/a')
    new_cat.save()
  except:
    new_cat = Category.objects.get(name=request.POST['item'])

  print("new_cat: ")
  print(new_cat)
  new_item = ItemEntry(location=loc,
                       type=new_cat, # cat
                       thumbnail="")
  new_item.save()

  # TODO: check that this works as expected
  if(ajax):
    return get_list_json_dumps_serializer(request, id)
  return redirect('cabinet', id)



@login_required
def delete_item(request, id):

  context = { 'devices': get_and_update_status(request.user) }

  if request.method != 'POST':
    return render(request, 'inventory.html', context)

  entry = get_object_or_404(ItemEntry, id=id)
  cab_id = entry.location.id
  messages.info(request, 'Item {0} has been deleted.'.format(entry.type.name))
  entry.delete()

  context = { 'devices': get_and_update_status(request.user),
              'items': ItemEntry.objects.all() }

  # return render(request, 'inventory.html', context)
  return redirect('cabinet', cab_id)



def ajax_del_item(request, id):
  entry = get_object_or_404(ItemEntry, id=id)
  cab_id = entry.location.id
  return redirect('cabinet', cab_id)

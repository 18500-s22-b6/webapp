from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from food_tracker.models import *
from food_tracker.forms import *

import requests

from .userinfo import get_userinfo

def home(request):
  return render(request, 'home.html', {})

@login_required
def profile(request):
  data = get_userinfo(request)
  print(data)

  context = get_context_by_user_data(request, data)
  
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

# @login_required # TODO: remove later
def dashboard(request):
  return render(request, 'dashboard.html', {})

def cabinet(request):
  return render(request, 'inv.html', {})

def get_context_by_user_data(request, data):
  context = {
    'user': {
      **data,
      'is_superuser': request.user.is_superuser,
    }
  }
  return context
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

import requests

from .userinfo import get_userinfo

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
def register(request):
  return render(request, 'registration.html')

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
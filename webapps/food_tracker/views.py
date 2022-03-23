from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
def home(request):
  return render(request, 'home.html', {})

@login_required
def profile(request):
  return render(request, 'profile.html')

@login_required
def register(request):
  return render(request, 'registration.html')

# @login_required # TODO: remove later
def dashboard(request):
  return render(request, 'dashboard.html', {})
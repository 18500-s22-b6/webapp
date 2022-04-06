"""webapps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.contrib.auth.views import LogoutView

from food_tracker import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('', include('social_django.urls', namespace='social')),
    path('dashboard', views.dashboard, name='dashboard'),
    path('recipes', views.recipes, name='recipes'), 
    path('add_recipe', views.add_recipe, name='add_recipe'),
    path('login', views.login, name='login'),
    path('profile', views.profile, name='profile'),
    path('register_user', views.register_user, name='register_user'),
    # path('logout/', LogoutView.as_view(template_name="index.html"), name='logout'),
    path('logout/', views.logout_user, name='logout'),
    path('cabinet/<int:id>', views.cabinet, name='cabinet'),
    path('add_device', views.register_device, name='add_device'), 
    path('del_cabinet/<int:id>', views.delete_device, name='del_cabinet'),
    path('add_item/<int:id>', views.add_item, name='add_item'),
    path('del_item/<int:id>', views.delete_item, name='del_item'),
]

"""hknWebsiteProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
	https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
	1. Add an import:  from my_app import views
	2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
	1. Add an import:  from other_app.views import Home
	2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
	1. Add an import:  from blog import urls as blog_urls
	2. Import the include() function: from django.conf.urls import url, include
	3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from . import views
from users import views as userviews

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^about', views.about, name='about'),
    url(r'^corporate', views.corporate, name='corporate'),
    url(r'^create_new_members', views.create_new_members, name='create_new_members'),
    url(r'^login_user', views.login_user, name='login_user'),
    url(r'^profile/(?P<uniqname>[a-z]{3,8})/(?P<profile_saved>[0-1])$', userviews.profile,
        name='profile'),
    url(r'^mentoring_competition', views.mentoring_competition, name='mentoring_competition'),
    url(r'^elections', views.elections, name='elections'),
    url(r'^feedback', views.feedback, name='feedback'),
    url(r'^misc_tools/(?P<success>[0-1])$', views.misc_tools, name='misc_tools'),
    url(r'^misc_tools', views.misc_tools, name='misc_tools'),
    url(r'^email_uncompleted_profiles', views.email_uncompleted_profiles, name='email_uncompleted_profiles'),
    url(r'^make_alumni', views.make_alumni, name='make_alumni'),
    url(r'^email_electee_progress', views.email_electee_progress, name='email_electee_progress'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

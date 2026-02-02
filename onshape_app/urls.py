from django.urls import path
from . import views

urlpatterns = [
    path('oauthSignin/', views.oauth_signin, name='oauth_signin'),
    path('oauthRedirect/', views.authorize, name='authorize'),
    path('index/<str:os_user_id>/', views.index, name='index'), 
]
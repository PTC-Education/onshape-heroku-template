from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from .models import OnshapeUser
from django.core.exceptions import ObjectDoesNotExist
import os
from django.http import HttpResponse
from urllib.parse import urlencode
import requests
from .api import *

def oauth_signin(request: HttpRequest):
    """
    Initial OAuth signin view for Onshape app.
    If new user, redirects to OAuth. If existing user, refreshes token and continues.
    """
    user_id = request.GET.get('userId')

    if not user_id:
        return HttpResponse("Missing userId parameter", status=400)
    
    try:
        # Try to get existing user
        user = OnshapeUser.objects.get(os_user_id=user_id)
        # Refresh token
        user.refresh_oauth_token() 
    except ObjectDoesNotExist:
        # Create new user
        user = OnshapeUser(os_user_id=user_id)
    
    # Update user's current Onshape context
    user.os_domain = request.GET.get('server')
    user.did = request.GET.get('did')
    user.wvm = request.GET.get('wvm')
    user.wvmid = request.GET.get('wvmid')
    user.eid = request.GET.get('eid')
    user.etype = request.GET.get('etype')
    user.save()

    # If user has tokens, go to app. Otherwise, do OAuth.
    if user.access_token:
        return HttpResponseRedirect(reverse("index", args=[user.os_user_id]))
    else:

        client_id = os.environ['OAUTH_CLIENT_ID']
        oauth_url = os.environ['OAUTH_URL']

        # Build query parameters properly
        params = {
            'response_type': 'code',
            'client_id': client_id,
        }
        
        redirect_url = f"{oauth_url}/oauth/authorize?{urlencode(params)}"
        return redirect(redirect_url)

def authorize(request: HttpRequest):
    """
    OAuth callback view - Onshape redirects here after authorization.
    Exchange the code for access and refresh tokens.
    """
    code = request.GET.get('code')
    
    if not code:
        return HttpResponse("Error: No authorization code received", status=400)
    
    # Exchange code for tokens
    token_url = f"{os.environ.get('OAUTH_URL')}/oauth/token"
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': os.environ.get('OAUTH_CLIENT_ID'),
        'client_secret': os.environ.get('OAUTH_CLIENT_SECRET')
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        # tokens contains: access_token, refresh_token, expires_in, token_type
        
        # Get the user's Onshape ID using the access token
        sess_response = requests.get(
            "https://cad.onshape.com/api/users/sessioninfo", 
            headers={"Authorization": "Bearer " + tokens['access_token']}
        ).json()
        
        # Find and update the user
        user = OnshapeUser.objects.get(os_user_id=sess_response['id'])
        user.access_token = tokens['access_token']
        user.refresh_token = tokens['refresh_token']
        user.save()

        # After saving tokens:
        return HttpResponseRedirect(reverse("index", args=[user.os_user_id]))
        
    else:
        return HttpResponse(f"Token exchange failed: {response.text}", status=400)

def index(request: HttpRequest, os_user_id: str):
    """
    Main app view - shown after successful OAuth
    """
    curr_user = get_object_or_404(OnshapeUser, os_user_id=os_user_id)
    
    doc_info = get_doc_info(curr_user.os_domain, curr_user.did, auth_token=curr_user.access_token)

    part_info = get_part_info(curr_user.os_domain, curr_user.did, curr_user.wvm, curr_user.wvmid, curr_user.eid, curr_user.etype, auth_token=curr_user.access_token)
    
    context = {
        "user": curr_user,
        "doc_info": doc_info,
        "part_info": part_info
    }
    return render(request, "onshape_app/index.html", context=context)
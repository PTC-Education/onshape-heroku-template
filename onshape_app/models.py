from django.db import models
import os
import requests
from datetime import timedelta
from django.utils import timezone

class OnshapeUser(models.Model):
    # Onshape user identifier
    os_user_id = models.CharField(max_length=200, unique=True)
    
    # OAuth tokens
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(blank=True, null=True)
    
    # Onshape environment info
    os_domain = models.CharField(max_length=200, blank=True, null=True)
    did = models.CharField(max_length=200, blank=True, null=True)  # Document ID
    wv = models.CharField(max_length=10, blank=True, null=True)    # Workspace/Version/Microversion
    wvid = models.CharField(max_length=200, blank=True, null=True) # Workspace/Version ID
    eid = models.CharField(max_length=200, blank=True, null=True)  # Element ID
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def refresh_oauth_token(self) -> None: 
        """
        When a user's ``access_token`` is expired or about to expire, tracked by the user's ``expires_at``, this function can be called to use the ``refresh_token`` to exchange for a new ``access_token``.  
        """
        try:
            token_url = f"{os.environ['OAUTH_URL']}/oauth/token"
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': os.environ['OAUTH_CLIENT_ID'],
                'client_secret': os.environ['OAUTH_CLIENT_SECRET']
            }
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()  # Raises exception for 4xx/5xx
            
            tokens = response.json()
            
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            self.token_expiry = timezone.now() + timedelta(seconds=tokens['expires_in'])
            self.save()
            
        except Exception as e:
            print(f"Token refresh failed for user {self.os_user_id}: {e}")

    def __str__(self):
        return f"OnshapeUser: {self.os_user_id}"
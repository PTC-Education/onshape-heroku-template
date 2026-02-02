import requests
from .models import OnshapeUser
import os

def get_doc_info(domain: str, did: str, auth_token: str): 
    """ Get the document info from the current document """

    url = f"{domain}/api/documents/{did}"

    response = requests.get(
        url, 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    if response.ok: 
        return response.json() 
    else: 
        return None
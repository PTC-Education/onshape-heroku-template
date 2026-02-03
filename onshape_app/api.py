import requests

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
    
def get_part_info(domain: str, did: str, wvm: str, wvmid: str, eid: str, etype: str, auth_token: str): 
    """ Get the document info from the current document """

    url = f"{domain}/api/{etype}/d/{did}/{wvm}/{wvmid}/e/{eid}"

    response = requests.get(
        url, 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    
    if response.ok: 
        if etype == "parts":
            return response.json()
        else:
            return response.json()['rootAssembly']['instances']
    else: 
        return None
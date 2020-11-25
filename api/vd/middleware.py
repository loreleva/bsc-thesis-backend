from flask import Response
from requests import post
import json

#VIRTUAL_DOCTOR_ID = 

auth_url = "https://mclabservices.di.uniroma1.it/auth/introspect"


def get_user_from_request(request):
    token = request.headers.get('token') 
    return get_user_from_token(token)

def get_user_from_token(token):
    headers = {
        'Host': 'auth-server',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = post(auth_url, data=token, headers=headers).json()
    if (not response['active']): #or (response['client_id'] != VIRTUAL_DOCTOR_ID):
        return None
    else:
        return response['sub']
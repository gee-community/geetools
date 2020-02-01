# coding=utf-8
""" Authentication functions """
import ee
from google.oauth2.credentials import Credentials
import json
import os
import shutil

DEFAULT_PATH = os.path.split(ee.oauth.get_credentials_path())[0]


def list_users(credential_path=DEFAULT_PATH):
    """ List local users """
    return os.listdir(credential_path)


def rename_current_user(name, credential_path=DEFAULT_PATH):
    """ Rename the current user. If you run `ee.Initialize()` after this
    you will be ask to initialize.
    """
    origin = ee.oauth.get_credentials_path()
    destination = os.path.join(credential_path, name)
    shutil.move(origin, destination)


def Initialize(filename, credential_path='default'):
    """
    Authenticate to GEE with the specified credentials

    If credential_path is set to 'defualt', it searches for the 'filename' in
    the same folder in which credentials are stored locally
    """
    if credential_path == 'default':
        credential_path = os.path.split(ee.oauth.get_credentials_path())[0]

    path = os.path.join(credential_path, filename)

    def get_credentials():
        try:
            tokens = json.load(open(path))
            refresh_token = tokens['refresh_token']
            return Credentials(
                None,
                refresh_token=refresh_token,
                token_uri=ee.oauth.TOKEN_URI,
                client_id=ee.oauth.CLIENT_ID,
                client_secret=ee.oauth.CLIENT_SECRET,
                scopes=ee.oauth.SCOPES)
        except IOError:
            raise ee.EEException(
                'Please authorize access to your Earth Engine account by '
                'running\n\nearthengine authenticate\n\nin your command line, and then '
                'retry.')

    credentials = get_credentials()
    ee.Initialize(credentials)
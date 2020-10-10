import json 
import requests
import time 
import urllib.parse as urlparse
from typing import List, Union
import itertools
from bs4 import BeautifulSoup
import requests
from models import SteamUrl
from utils import get_value_in_nested_dict, resource_path
import xmltodict
import random

class AutoPoster:
    
    def __init__(self, session):
        self._session = session
        self.config = self.__readConfig(resource_path('config.json'))

    def getGroupIDFromURL(self, url):
        req = requests.get(url+'/memberslistxml?xml=1')
        data = xmltodict.parse(req.content)
        return data['memberList']['groupID64']

    def postComments(self, urls, message):
        for url in urls:
            session_id = self._get_session_id()
            post = 'https://steamcommunity.com/comment/Clan/post/'+self.getGroupIDFromURL(url)+'/-1/'
            params = {
                'comment' : message,
                'sessionid': session_id,
                'count': 6
            }
            headers = {'Referer': url,
                    'Origin': SteamUrl.COMMUNITY_URL}
            response = self._session.post(post, data=params, headers=headers).json()
        return response

    def postDiscussion(self, urls, title, message):
        for url in urls:
            time.sleep(random.randint(60, 300)) #dont get blocked for posting frequently 
            o_id = next(get_value_in_nested_dict(self.config, url))
            session_id = self._get_session_id()
            url = 'https://steamcommunity.com/forum/'+o_id+'/General/createtopic/0/'
            params = {
                'topic' : title,
                'text' : message,
                'sessionid': session_id,
            }
            headers = {'Referer': url,
                    'Origin': SteamUrl.COMMUNITY_URL}
            response = self._session.post(url, data=params, headers=headers).json()
          

    def _get_session_id(self) -> str:
        return self._session.cookies.get_dict()['sessionid']

    def __readConfig(self, path):
        with open(path) as file:
            return json.load(file)

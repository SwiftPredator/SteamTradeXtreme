import json 
import requests
import time 
import urllib.parse as urlparse
from typing import List, Union
import itertools
from bs4 import BeautifulSoup
import requests
from models import SteamUrl
import xmltodict

class AutoPoster:
    
    def __init__(self, session):
        self._session = session

    def getGroupIDFromURL(self, url):
        req = requests.get(url+'/memberslistxml?xml=1')
        data = xmltodict.parse(req.content)
        return data['memberList']['groupID64']

    def postComments(self, urls, message):
        for url, _ in urls.items():
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
        for url, o_id in urls.items():
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
        print(self._session.cookies)
        return self._session.cookies.get_dict()['sessionid']

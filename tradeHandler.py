from steampy.client import SteamClient
import json 
import requests
import time 
import urllib.parse as urlparse
from typing import List, Union
import itertools
import numpy as np
import pyotp
import operator
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from models import Asset, TradeOfferState, SteamUrl, GameOptions, Currency, PriceAPIEndpoint, InventoryType
from utils import text_between, texts_between, merge_items_with_descriptions_from_inventory, \
    steam_id_to_account_id, merge_items_with_descriptions_from_offers, get_description_key, \
    merge_items_with_descriptions_from_offer, account_id_to_steam_id, get_key_value_from_url, parse_price, reverseDict

class TradeHandler:

    def __init__(self, api_endpoint: PriceAPIEndpoint, config_path="./config.json"):
        self.config = self.readConfig(config_path)
        self._session = requests.Session()
        self._price_endpoint = api_endpoint
        self.bitskins_pricelist = self.__getBitskinsPriceList(self.config["bitskins"]["api_key"], self.config["bitskins"]["api_secret"])
        self.steamapis_pricelist = self.__getSteamPriceAPIPrices(self.config["steamapis"]["api_key"])
        self._session_tradelinks = []

    def readConfig(self, path):
        with open(path) as file:
            return json.load(file)

    def loginSteam(self):
        try:
            login_data = self.config["steam_data"]["login"]
            self.steamClient = webdriver.Chrome(ChromeDriverManager().install())
            self.steamClient.get(login_data["url"])
            ele_username = self.steamClient.find_element_by_id(login_data["username_id"])
            ele_password = self.steamClient.find_element_by_id(login_data["password_id"])
            ele_login = self.steamClient.find_element_by_id(login_data["login_button_id"])
            self.driverSetValuesInput((ele_username, login_data["username"]), (ele_password, login_data["password"]))
            ele_login.click()
            wait = WebDriverWait(self.steamClient, 60)
            wait.until(EC.url_contains("/profiles"))
            cookies = self.steamClient.get_cookies()
            for cookie in cookies:
                self._session.cookies.set(cookie['name'], cookie['value'])
        except TimeoutException as t:
             print("Exception has been thrown. " + str(t))
        self.steamClient.close()
        return self._session

    
    def get_my_inventory(self, game: GameOptions, merge: bool = True, count: int = 5000) -> dict:
        steam_id = self.config["steam_data"]["login"]["steam_id"]
        return self.get_partner_inventory(steam_id, game, merge, count)

    
    def get_partner_inventory(self, partner_steam_id: str, game: GameOptions, merge: bool = True, count: int = 5000) -> dict:
        url = '/'.join([SteamUrl.COMMUNITY_URL, 'inventory', partner_steam_id, game.app_id, game.context_id])
        params = {'l': 'english',
                  'count': count}
        try:
            response_dict = self._session.get(url, params=params).json()
            if response_dict['success'] != 1:
                print("Failed")
            if merge:
                return merge_items_with_descriptions_from_inventory(response_dict, game)
            return response_dict
        except Exception as e:
            raise Exception("Problem in fetching Inventory. Continue with next Inventory. url: {}, Error: {}".format(url, str(e)))


    def driverSetValuesInput(self, *args):
        for ele, value in args:
            self.steamClient.execute_script("arguments[1].value=arguments[0];", str(value), ele)
    
    def calculateOptimalTrade(self, inv_raw, partner_inv_raw):
        my_inv = self.__convertRawInventory(inv_raw, InventoryType.MY)
        partner_inv = self.__convertRawInventory(partner_inv_raw, InventoryType.THEIR)
        if partner_inv == None or len(partner_inv) == 0:
            print("Partner Inevtory empty or something like that")
            return None

        overall_value_my = sum(my_inv.values())
        overall_value_partner = sum(partner_inv.values())
        max_item_my = max(my_inv.items(), key=operator.itemgetter(1))
        max_item_partner = max(partner_inv.items(), key=operator.itemgetter(1))
        max_price_my = max_item_my[1]
        max_price_partner = max_item_partner[1]
        
        #print(overall_value_my, overall_value_partner, max_price_my, max_price_partner, self.__get_name_from_itemID(partner_inv_raw, max(partner_inv.items(), key=operator.itemgetter(1))[0]))
        target_price = None 
        #margin_min = self.config["trades"]["min_margin"] @remove
        #margin_max = self.config["trades"]["max_margin"] @remove
        working_dict = None
        #look which item should be traded 
        if max_price_my > max_price_partner and overall_value_partner > max_price_my:
            target_price = max_price_my
            working_dict = partner_inv
            print("Target is in my inventory")
        elif max_price_my < max_price_partner and overall_value_my > max_price_partner:
            target_price = max_price_partner
            working_dict = my_inv
            print("Target is in partner inventory")
        else:
            print("No target found")
            return None

       
        inv_type = InventoryType.MY  if working_dict == my_inv else InventoryType.THEIR
        sorted_pairs = [(k, v) for k, v in sorted(working_dict.items(), key=lambda item: item[1])]
        #print(sorted_pairs)
        tradeComb = self.find_closest_sum(sorted_pairs, target_price, inv_type)
        if tradeComb == None:
            print("No Combo Found")
            return None
        res = {
            "my_items" : [Asset(x[0], GameOptions.CS) for x in tradeComb] if working_dict == my_inv else [Asset(max_item_my[0], GameOptions.CS)],
            "their_items" : [Asset(x[0], GameOptions.CS) for x in tradeComb] if working_dict == partner_inv else [Asset(max_item_partner[0], GameOptions.CS)]

        }
        return res

        
        
        
    def __convertRawInventory(self, inv, inv_type: InventoryType, bitskins=True):
        res = {}
        inv_key = "my_inv" if inv_type == InventoryType.MY else "their_inv"
        for item in iter(inv.values()):
            id = item["id"]
            name = item["market_hash_name"]
            tradeable = item["tradable"]
            if not tradeable:
                continue
            if any(x in name for x in self.config["trades"]["avoid"][inv_key]):
                continue
            prices = self.fetch_price(name, GameOptions.CS)
            if not bitskins: 
                time.sleep(3.1) #Steam only accepts 20 requests all 60 seconds
                if prices == None or "median_price" not in prices:
                    continue
                price = float(text_between(prices["median_price"], "$", " "))
                if price < self.config["trades"]["min_item_price_partner"]:
                    continue
                res[id] = price
            else:
                if float(prices) < self.config["trades"]["min_item_price_partner"]:
                    continue
                res[id] = float(prices)
        return res

    def __get_name_from_itemID(self, inv, id):
         for item in iter(inv.values()):
             if item["id"] == id:
                 return item["market_hash_name"]

    #Check for inventory
    def find_closest_sum(self, numbers, target, inv_type: InventoryType): #numbers must be key-value tuple array 
        #numbers.sort()
        result = [(0, 0),]
        last_sum = 0
        max_target = target+((target/100)*self.config["trades"]["max_margin_downgrade"]) \
            if inv_type == InventoryType.THEIR else \
                target-((target/100)*self.config["trades"]["min_margin_upgrade"])
        min_target = target+((target/100)*self.config["trades"]["min_margin_downgrade"]) \
            if inv_type == InventoryType.THEIR else \
                target-((target/100)*self.config["trades"]["max_margin_upgrade"])
        print("Price Targets: ", target, min_target, max_target)
        while(1):
            for i in range(0, len(numbers)):
                res_sum = sum([pair[1] for pair in result])
                if numbers[i][1] + res_sum > max_target:
                    index = i - 1
                elif i == len(numbers) - 1:
                    index = i
                else:
                    continue
                result.append(numbers[index])
                numbers.pop(index)
                break
            res_sum_new = sum([pair[1] for pair in result])
            if res_sum_new <= max_target and res_sum_new >= min_target:
                return result[1:]
            elif res_sum_new == last_sum:
                return None
            last_sum = res_sum_new
        return None
 
    def fetch_price(self, item_hash_name: str, game: GameOptions, inventory_type=0,  currency: str = Currency.EURO) -> dict:
        if self._price_endpoint == PriceAPIEndpoint.BITSKINS:
            for item in self.bitskins_pricelist["prices"]:
                if item["market_hash_name"] == item_hash_name:
                    return item["price"]
            return None
        elif self._price_endpoint == PriceAPIEndpoint.STEAMAPIS:
            for item in self.steamapis_pricelist["data"]:
                if item["market_hash_name"] == item_hash_name:
                    return item["prices"]["safe"]
        else:
            url = SteamUrl.COMMUNITY_URL + '/market/priceoverview/'
            params = {'country': 'DE',
                    'currency': currency,
                    'appid': game.app_id,
                    'market_hash_name': item_hash_name}
            response = self._session.get(url, params=params)
            if response.status_code == 429:
                time.sleep(60)
            return response.json()



    '''Get the actual Price-List of all items from Bitskins.com'''
    def __getBitskinsPriceList(self, api_key, secret):
        try:
            token = pyotp.TOTP(secret)
            data_bit = {'api_key': api_key, 'app_id': '730', 'code': token.now()}
            headers_bit = {'content-type': 'application/json', 'accept': 'application/json'}
            r = requests.post('https://bitskins.com/api/v1/get_all_item_prices', data=json.dumps(data_bit), headers=headers_bit)
            return r.json()
        except Exception as e:
            print("Exception triggered "+ str(e))
        return []

    """Get better pricelist from steamapis.com, since Bitskins prices are shit but free"""
    def __getSteamPriceAPIPrices(self, api_key):
        data = {'api_key' : api_key}
        header = {'content-type': 'application/json', 'accept': 'application/json'}
        r = requests.get("https://api.steamapis.com/market/items/730", params=data, headers=header)
        return r.json()
        
    def make_offer_with_url(self, items_from_me: List[Asset], items_from_them: List[Asset],
                            trade_offer_url: str, message: str = '', case_sensitive: bool=True) -> dict:
        token = get_key_value_from_url(trade_offer_url, 'token', case_sensitive)
        partner_account_id = get_key_value_from_url(trade_offer_url, 'partner', case_sensitive)
        partner_steam_id = account_id_to_steam_id(partner_account_id)
        offer = self._create_offer_dict(items_from_me, items_from_them)
        session_id = self._get_session_id()
        url = SteamUrl.COMMUNITY_URL + '/tradeoffer/new/send'
        server_id = 1
        trade_offer_create_params = {'trade_offer_access_token': token}
        params = {
            'sessionid': session_id,
            'serverid': server_id,
            'partner': partner_steam_id,
            'tradeoffermessage': message,
            'json_tradeoffer': json.dumps(offer),
            'captcha': '',
            'trade_offer_create_params': json.dumps(trade_offer_create_params)
        }
        headers = {'Referer': SteamUrl.COMMUNITY_URL + urlparse.urlparse(trade_offer_url).path,
                   'Origin': SteamUrl.COMMUNITY_URL}
        response = self._session.post(url, data=params, headers=headers).json()

        return response

    def _create_offer_dict(self, items_from_me: List[Asset], items_from_them: List[Asset]) -> dict:
        return {
            'newversion': True,
            'version': 4,
            'me': {
                'assets': [asset.to_dict() for asset in items_from_me],
                'currency': [],
                'ready': False
            },
            'them': {
                'assets': [asset.to_dict() for asset in items_from_them],
                'currency': [],
                'ready': False
            }
        }

    def _get_session_id(self) -> str:
        return self._session.cookies.get_dict()['sessionid']

    def get_session_trades(self):
        return self._session_tradelinks
    
    def append_session_trade(self, url):
        self._session_tradelinks.append(url)



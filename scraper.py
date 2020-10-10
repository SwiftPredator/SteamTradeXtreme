from bs4 import BeautifulSoup
import requests
import json
from utils import account_id_to_steam_id, text_between, resource_path
from selenium import webdriver
import time

class Scraper:

    def __init__(self, config_path="./config.json"):
        self.comment_urls, self.thread_urls = self.__getGroupURLs(resource_path(config_path))

    @staticmethod
    def __getGroupURLs(config_path):
        with open(config_path) as file:
            data = json.load(file)
            return data['groups']['urls']['autotrader']['comments'], data['groups']['urls']['autotrader']['threads']

    def getTradeURLsComments(self):
        res = {}
        for url in self.comment_urls:
            req = requests.get(url)
            soup = BeautifulSoup(req.content, "html.parser")
            comments = soup.find_all("div", class_="commentthread_comment_content")
            for comment in comments:
                profile_link = comment.find("a", class_="commentthread_author_link")["href"]
                trade_link = comment.find("a", class_="bb_link")
                if trade_link == None or trade_link.find("https://steamcommunity.com") == -1:
                    continue
                split_sub = "profiles/" if profile_link.find("profiles") != -1 else "id/"
                steam_id = None
                if trade_link['href'].find('?partner=') == -1:
                    continue
                elif split_sub == "id/": #Extract id from trade link
                    try:
                        steam_id = account_id_to_steam_id(text_between(trade_link['href'], '?partner=', '&'))
                    except:
                        continue
                else:
                    steam_id = profile_link.split(split_sub)[1]
                #steam_id = steam_id if split_sub == "profiles/" else account_id_to_steam_id(steam_id)
                res[steam_id] = trade_link["href"]
          
        return res


    def getTradeURLsThreads(self):
        res = {}
        for url in self.thread_urls:
            req = requests.get(url)
            soup = BeautifulSoup(req.content, "html.parser")
            discussions_url = soup.find_all("a", class_="forum_topic_overlay")
            for disc in discussions_url:
                req = requests.get(disc["href"])
                soup = BeautifulSoup(req.content, "html.parser")
                if soup != None:
                    trade_info = soup.find("div", class_='forum_op')
                    if trade_info:
                        trade_info = trade_info.find('div', class_="content")
                        if trade_info:
                            trade_link = trade_info.find('a', class_='bb_link')
                            if trade_link and trade_link["href"].find('https://steamcommunity.com/tradeoffer/') != -1:
                                #print(trade_link["href"])
                                steam_id = account_id_to_steam_id(text_between(trade_link["href"], '?partner=', '&'))
                                res[steam_id] = trade_link["href"]
        return res
  
    def __get_trade_urls_CS_main_trade_discussion(self, url, soup):
        driver = webdriver.PhantomJS()
        driver.get(url)
        time.sleep(10)
        p_element = driver.find_element_by_class_name("maincontent")
        print(p_element.get_attribute('innerHTML'))
        
        return None, None
        
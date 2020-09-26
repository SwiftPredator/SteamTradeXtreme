import scraper as scpr
import tradeHandler as th
from utils import GameOptions, text_between, account_id_to_steam_id, steam_id_to_account_id, reverseDict
from steamid import SteamID
from itertools import permutations, combinations, chain
from models import PriceAPIEndpoint
import view as vw
import sched, time
import PySimpleGUI as sg
import autoposter as ap
from valve.steam.id import SteamID



print("""
(                                                             )                                                   
 )\ )    )                     *   )             (          ( /(     )                                  )      )   
(()/( ( /(   (     )     )   ` )  /( (       )   )\ )   (   )\()) ( /( (      (     )      (     )   ( /(   ( /(   
 /(_)))\()) ))\ ( /(    (     ( )(_)))(   ( /(  (()/(  ))\ ((_)\  )\()))(    ))\   (      ))\   /((  )\())  )\())  
(_)) (_))/ /((_))(_))   )\  '(_(_())(()\  )(_))  ((_))/((_)__((_)(_))/(()\  /((_)  )\  ' /((_) (_))\((_)\  ((_)\   
/ __|| |_ (_)) ((_)_  _((_)) |_   _| ((_)((_)_   _| |(_))  \ \/ /| |_  ((_)(_))  _((_)) (_))   _)((_)/ (_) /  (_)  
\__ \|  _|/ -_)/ _` || '  \()  | |  | '_|/ _` |/ _` |/ -_)  >  < |  _|| '_|/ -_)| '  \()/ -_)  \ V / | | _| () |   
|___/ \__|\___|\__,_||_|_|_|   |_|  |_|  \__,_|\__,_|\___| /_/\_\ \__||_|  \___||_|_|_| \___|   \_/  |_|(_)\__/                                                                                                                   
""")

#print(account_id_to_steam_id('3865252'))
#Build view with event loop
gui = vw.GUI()
gui.create()

#s = scpr.Scraper()
#print(len(s.getTradeURLsComments()), len({**s.getTradeURLsComments(), **s.getTradeURLsThreads()}))
#tt = th.TradeHandler(PriceAPIEndpoint.STEAMAPIS)
#s = tt.loginSteam()
#t = ap.AutoPoster(tt)
#t.postDiscussion(["https://steamcommunity.com/groups/CSGOTrader"], "Hallo", "Hallo")

"""handler = th.TradeHandler(PriceAPIEndpoint.STEAMAPIS)
scraper = scpr.Scraper()
#Login
handler.loginSteam()
inv = handler.get_my_inventory(GameOptions.CS)
s = sched.scheduler(time.time, time.sleep)
def start(sc):
    #Get Trade Links and SteamIds
    trade_urls = scraper.getTradeURLsComments()
    #Get user inventory
    print("Start Searching")
    for steam_id, url in trade_urls.items():
        if url in handler.get_session_trades():
            continue
        else:
            handler.append_session_trade(url)
        try:
            partner_inv = handler.get_partner_inventory(steam_id, GameOptions.CS, merge=True)
            trade = handler.calculateOptimalTrade(inv, partner_inv)
            print(trade)
            if trade is not None:
                handler.make_offer_with_url(trade["my_items"], trade["their_items"], url)
        except Exception as e:
            print("Error in creating trade. Message: {}", str(e))
    print("End Searching")
    s.enter(180, 1, start, (sc,))

s.enter(1, 1, start, (s,))
s.run()
"""
#####################
## Find sum test-cases
#####################
tradeHandler = th.TradeHandler(PriceAPIEndpoint.STEAMAPIS)
test = False
if test:
    numbers = [1,2,3,4,8]
    res = tradeHandler.find_closest_sum(numbers, 17, 0)
    print(res)

#####################
## Autoposter test-cases
#####################
"""print(SteamID.from_community_url('https://steamcommunity.com/groups/CSGOTrader/'))
tradeHandler = th.TradeHandler(PriceAPIEndpoint.STEAMAPIS)
test = False"""
if test:
    session = tradeHandler.loginSteam()
    config = tradeHandler.readConfig('./config.json')
    poster = ap.AutoPoster(session)
    res = poster.postComments(config['groups']['urls']['autoposter'], '[H] Items [W] Offers')
    print(res)



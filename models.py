import enum
from collections import namedtuple
from threading import Thread, Event
from time import sleep

# StoppableThread is from user Dolphin, from http://stackoverflow.com/questions/5849484/how-to-exit-a-multithreaded-program
class StoppableThread(Thread):  

    def __init__(self):
        Thread.__init__(self)
        self.stop_event = Event()        

    def stop(self):
        if self.isAlive() == True:
            # set event to signal thread to terminate
            self.stop_event.set()
            # block calling thread until thread really has terminated
            self.join()

class IntervalTimer(StoppableThread):

    def __init__(self, interval, worker_func, *args):
        super().__init__()
        self._interval = interval
        self._worker_func = worker_func

    def run(self):
        while not self.stop_event.is_set():
            self._worker_func()
            sleep(self._interval)


class GameOptions:
    PredefinedOptions = namedtuple('PredefinedOptions', ['app_id', 'context_id'])

    STEAM = PredefinedOptions('753', '6')
    DOTA2 = PredefinedOptions('570', '2')
    CS = PredefinedOptions('730', '2')
    TF2 = PredefinedOptions('440', '2')
    PUBG = PredefinedOptions('578080', '2')
    RUST = PredefinedOptions('252490', '2')

    def __init__(self, app_id: str, context_id: str) -> None:
        self.app_id = app_id
        self.context_id = context_id

class PriceAPIEndpoint(enum.IntEnum):
    BITSKINS = 1
    STEAMAPIS = 2
    INTERN = 3

class InventoryType(enum.IntEnum):
    MY = 1,
    THEIR = 2

class TradingStrategy(enum.IntEnum):
    BOT = 1,
    USER = 2

class Asset:
    def __init__(self, asset_id: str, game: GameOptions, amount: int = 1) -> None:
        self.asset_id = asset_id
        self.game = game
        self.amount = amount

    def to_dict(self):
        return {
            'appid': int(self.game.app_id),
            'contextid': self.game.context_id,
            'amount': self.amount,
            'assetid': self.asset_id
        }


class Currency(enum.IntEnum):
    USD = 1
    GBP = 2
    EURO = 3
    CHF = 4
    RUB = 5


class TradeOfferState(enum.IntEnum):
    Invalid = 1
    Active = 2
    Accepted = 3
    Countered = 4
    Expired = 5
    Canceled = 6
    Declined = 7
    InvalidItems = 8
    ConfirmationNeed = 9
    CanceledBySecondaryFactor = 10
    StateInEscrow = 11


class SteamUrl:
    API_URL = "https://api.steampowered.com"
    COMMUNITY_URL = "https://steamcommunity.com"
    STORE_URL = 'https://store.steampowered.com'


class Endpoints:
    CHAT_LOGIN = SteamUrl.API_URL + "/ISteamWebUserPresenceOAuth/Logon/v1"
    SEND_MESSAGE = SteamUrl.API_URL + "/ISteamWebUserPresenceOAuth/Message/v1"
    CHAT_LOGOUT = SteamUrl.API_URL + "/ISteamWebUserPresenceOAuth/Logoff/v1"
    CHAT_POLL = SteamUrl.API_URL + "/ISteamWebUserPresenceOAuth/Poll/v1"
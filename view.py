import tkinter as tk
import tradeHandler as th
import scraper as scpr
import autoposter as ap
from utils import GameOptions, text_between, account_id_to_steam_id, steam_id_to_account_id, reverseDict, get_value_in_nested_dict
from models import PriceAPIEndpoint, GameOptions, IntervalTimer
import sched, time
import PySimpleGUI as sg
import  threading as t
from timeloop import Timeloop
from datetime import timedelta
import json

class GUI():

    def __init__(self):
       self.config = self.__readConfig('./config.json')
       self.handler = None
       self.scraper = None

    def create(self):
        output_column = [
                [sg.Text('Auto Trade Finder Modul', size=[50, 2])],
                [sg.HorizontalSeparator(pad=None)],
                [sg.Output(size=(100, 30))],
                [sg.Button('START', disabled=True, button_color=(sg.YELLOWS[0], sg.BLUES[0])),
                sg.Button('STOP', disabled=True, button_color=(sg.YELLOWS[0], sg.GREENS[0]))]
                ]
        settings_column = [ 
            [sg.Text('Login Info:', size=[30, 1], font=("Helvetica", 15))],
            [sg.Text('Username: '), sg.Input(self.__getTextFromConfig('username'), key='username'), sg.Text('Password: '), sg.Input(self.__getTextFromConfig('password'), key='password')],
            [sg.Text('Margins:', size=[30,1], font=("Helvetica", 15))],
            [sg.Text('Min Downgrade'), sg.Spin([i for i in range(-50,50)], initial_value=self.__getTextFromConfig('min_margin_downgrade'), key='min_margin_downgrade'), 
            sg.Text('Max Downgrade'), sg.Spin([i for i in range(-50,50)], initial_value=self.__getTextFromConfig('max_margin_downgrade'), key='max_margin_downgrade')],
            [sg.Text('Min Upgrade'), sg.Spin([i for i in range(-50,50)], initial_value=self.__getTextFromConfig('min_margin_upgrade'), key='min_margin_upgrade'), 
            sg.Text('Max Upgrade'), sg.Spin([i for i in range(-50,50)], initial_value=self.__getTextFromConfig('max_margin_upgrade'), key='max_margin_upgrade')],
            [sg.Text('Avoid Items in MY Inventory:', size=[22, 1], font=("Helvetica", 15)), sg.Text('Avoid Items in THEIR Inventory:', size=[22, 1], font=("Helvetica", 15))],
            [sg.Listbox(values=self.__getTextFromConfig('my_inv'), size=(30,5), key='_LISTBOX_MY'), sg.Listbox(values=self.__getTextFromConfig('their_inv'), size=(30,5), key='_LISTBOX_THEIR')],
            [sg.Button('Add', size=[14,1], key='_ADD_MY'), sg.Button('Delete', size=[14,1], key='_DELETE_MY'), sg.Button('Add', size=[14,1], key='_ADD_THEIR'), sg.Button('Delete', size=[14,1], key='_DELETE_THEIR')]

        ]

        settings_frame = [
            [sg.Frame('Settings', settings_column, font=("Helvetica", 20), title_color='white')],
            [sg.Button('SAVE SETTINGS'), sg.Button('CREATE SESSION')]
        ]
        
        group_autowrite_column = [
            [sg.Text('Auto Trade Post Modul', size=[50, 2])],
            [sg.HorizontalSeparator(pad=None)],
            [sg.InputText(self.__getTextFromConfig('title'), key='title')],
            [sg.Multiline(self.__getTextFromConfig('message'), size=(45, 5), key='message')],
            [sg.Text('Post Frequenz(s)'), sg.Spin([i for i in range(10,5000)], initial_value=self.__getTextFromConfig('freq'), key='freq')],
            [sg.Checkbox('Comments', default=True, key="p_comment"), sg.Checkbox('Discussions', key='p_discussion')],
            [sg.HorizontalSeparator(pad=None)],
            [sg.Button('START POSTER', disabled=True, key='_START_POSTER'), sg.Button('STOP POSTER', disabled=True, key='_STOP_POSTER')]
        ]

        layout = [
            [
                sg.Column(settings_frame, element_justification='l'), 
                sg.VerticalSeparator(pad=None), sg.Column(output_column, element_justification='l'), 
                sg.VerticalSeparator(pad=None), sg.Column(group_autowrite_column, element_justification='l') 
            ]
        ]
        window = sg.Window('', layout, default_element_size=(30, 2))

        while True:
                event, value = window.read()
                if not self.__event_handler(event, value, window):
                    break
        window.close()
        



    def __event_handler(self, event, values, window)->bool:
        if event == 'START':
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
            window.FindElement('START').Update(disabled=True)
            window.FindElement('STOP').Update(disabled=False)
            inv = self.handler.get_my_inventory(GameOptions.CS)
            global thread
            thread = t.Thread(
                target=self.__start,
                args=(self.scraper, self.handler, inv, window),
                daemon=True
            )
            thread.start()
        elif event == 'STOP':   
            self.__stop(window)
        elif event == 'ADD GROUP LINK':
            self.config['groups']['urls']['autoposter']['groups'].append(values['_GROUPLINKIN'])
            self.__writeConfig()
            window.Element('_GROUPLIST').update(values=self.config['groups']['urls']['autoposter']['groups'])
        elif event == 'SAVE SETTINGS':
            for k, v in values.items():
                self.config = self.__updateConfig(self.config, k, v)
            self.__writeConfig()
            sg.popup('Settings saved!')
        elif event == 'CREATE SESSION':
            self.handler = th.TradeHandler(PriceAPIEndpoint.STEAMAPIS)
            self.scraper = scpr.Scraper()
            _session = self.handler.loginSteam()
            self.poster = ap.AutoPoster(_session)
            window.FindElement('START').Update(disabled=False)
            window.FindElement('_START_POSTER').Update(disabled=False)
        elif event == '_START_POSTER':
            print("Starting to Post Comments and Discussions!")
            window.FindElement('_START_POSTER').Update(disabled=True)
            window.FindElement('_STOP_POSTER').Update(disabled=False)
            message = values['message']
            freq = values['freq']
            title = values['title']
            com, disc = values['p_comment'], values['p_discussion']
            for k, v in values.items():
                self.config = self.__updateConfig(self.config, k, v)
            self.__writeConfig()

            global post_thread
            post_thread = t.Thread(
                target=self.__start_auto_poster,
                args=(self.__getTextFromConfig('autoposter'), title, message, freq, com, disc),
                daemon=True
            )
            post_thread.start()
            
        elif event == '_STOP_POSTER':
            self.__stop_auto_poster(window)
        elif event == '_ADD_MY':
            item = sg.popup_get_text('Add new Element to avoid.')
            self.config['trades']['avoid']['my_inv'].append(item)
            window.Element('_LISTBOX_MY').update(values=self.config['trades']['avoid']['my_inv'])
        elif event == '_DELETE_MY':
            items = values['_LISTBOX_MY']
            self.config['trades']['avoid']['my_inv'] = [x for x in self.config['trades']['avoid']['my_inv'] if x not in items]
            window.Element('_LISTBOX_MY').update(values=self.config['trades']['avoid']['my_inv'])
        elif event == '_ADD_THEIR':
            item = sg.popup_get_text('Add new Element to avoid.')
            self.config['trades']['avoid']['their_inv'].append(item)
            window.Element('_LISTBOX_THEIR').update(values=self.config['trades']['avoid']['their_inv'])
        elif event == '_DELETE_THEIR':
            items = values['_LISTBOX_THEIR']
            self.config['trades']['avoid']['their_inv'] = [x for x in self.config['trades']['avoid']['their_inv'] if x not in items]
            window.Element('_LISTBOX_THEIR').update(values=self.config['trades']['avoid']['their_inv'])
        elif event == 'EXIT' or event == sg.WIN_CLOSED:
            return False

        return True
    
    def __start_auto_poster(self, urls, title, message, freq, com=True, disc=True):
        thread = t.current_thread()
        counter = freq #Set to frequnz for instant searching when calling the method 
        while getattr(thread, "do_run", True):
            if counter >= freq:
                print("Posted new Comment and Thread in all groups!")
                time.sleep(5)
                if com:
                    self.poster.postComments(urls, message)
                time.sleep(2)
                if disc:
                    self.poster.postDiscussion(urls, title, message)
                counter = 0
            time.sleep(1)
            counter += 1 
    def __stop_auto_poster(self, window):
        print("Stopped the AutoPoster")
        post_thread.do_run = False
        post_thread.join()
        window.FindElement('_START_POSTER').Update(disabled=False)
        window.FindElement('_STOP_POSTER').Update(disabled=True)

    def __start(self, scraper, handler, inv, window):
        thread = t.current_thread()
        counter = 180 #Set to frequnz for instant searching when calling the method 
        while getattr(thread, "do_run", True):
            if counter >= 180: #search frequenz in seconds
                #Get Trade Links and SteamIds
                trade_urls = {**scraper.getTradeURLsComments(), **scraper.getTradeURLsThreads()}
                #Get user inventory
                print("Start Searching")
                trade_counter = 0
                for steam_id, url in trade_urls.items():
                    if url in handler.get_session_trades():
                        continue
                    else:
                        handler.append_session_trade(url)
                    try:
                        partner_inv = handler.get_partner_inventory(steam_id, GameOptions.CS, merge=True)
                        trade = handler.calculateOptimalTrade(inv, partner_inv)
                        if trade is not None:
                            message = "Hey, im interested in your items and i think i made a fair offer. If you want to discuss please add me or send a counter-offer."
                            handler.make_offer_with_url(trade["my_items"], trade["their_items"], url, message=message)
                            trade_counter += 1
                    except Exception as e:
                        print("Error in creating trade. Message: {}".format(str(e)))
                print("End Searching for this period. Found: {} possible trades.".format(trade_counter))
                counter = 0
            time.sleep(1)
            counter += 1 

    def __stop(self, window):
        print("Stopped the Bot")
        thread.do_run = False
        thread.join()
        window.FindElement('START').Update(disabled=False)
        window.FindElement('STOP').Update(disabled=True)

    def __readConfig(self, path):
        with open(path) as file:
            return json.load(file)

    def __writeConfig(self):
        with open('./config.json', 'w') as outfile:
                json.dump(self.config, outfile)

    def __getTextFromConfig(self, key):
        return next(get_value_in_nested_dict(self.config, key))

    def __updateConfig(self, dic, key, value):
        for k, v in dic.items():
            if k == key:
                dic[k] = value
            elif isinstance(v, dict):
                dic[k] = self.__updateConfig(v, key, value)
        return dic


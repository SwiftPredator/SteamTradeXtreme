import tkinter as tk
import tradeHandler as th
import scraper as scpr
import autoposter as ap
from utils import GameOptions, text_between, account_id_to_steam_id, steam_id_to_account_id, reverseDict, get_value_in_nested_dict, resource_path, log_status
from models import PriceAPIEndpoint, GameOptions, IntervalTimer, TradingStrategy
import sched, time
import PySimpleGUI as sg
import  threading as t
from timeloop import Timeloop
from datetime import timedelta
import json
import random
import traceback

class GUI():

    def __init__(self):
       self.config = self.__readConfig(resource_path('config.json'))
       self.handler = None
       self.scraper = None

    def create(self):
        output_column = [
                [sg.Text('Auto Trade Finder Modul', size=[50, 2])],
                [sg.HorizontalSeparator(pad=None)],
                [sg.Text('Your Inventory:', size=[50, 2]), sg.Text('Items to trade:', size=[50, 2])],
                [sg.Listbox(values=[], size=[50, 15], enable_events=True, key='_AVA_ITEMS'), sg.Listbox(values=[], size=[50, 15], enable_events=True, key='_SEL_ITEMS')],
                [sg.Radio('Let Bot select items', "RADIO1", default=True, key='_bot_trade'), sg.Radio('Take user choosen items', "RADIO1", key='_user_trade')],
                [sg.Text('Trade Message:', size=[50, 2])],
                [sg.Multiline(self.__getTextFromConfig('trade_message'), size=(100, 4), key='_trade_message')],
                [sg.HorizontalSeparator(pad=None)],
                [sg.Text('Information-Output:', size=(50, 2))],
                #[sg.Output(size=(100, 20))],
                [sg.Button('START', disabled=True, button_color=(sg.YELLOWS[0], sg.BLUES[0])),
                sg.Button('STOP', disabled=True, button_color=(sg.YELLOWS[0], sg.GREENS[0]))]
                ]
        settings_column = [ 
            [sg.Text('SteamID: '), sg.Input(self.__getTextFromConfig('steam_id'), key='steam_id')],
            [sg.Text('Login Info:', size=[30, 1], font=("Helvetica", 15))],
            [sg.Text('Username: '), sg.Input(self.__getTextFromConfig('username'), key='username'), sg.Text('Password: '), sg.Input(self.__getTextFromConfig('password'), key='password')],
            [sg.Text('Price-API Info:', size=[30, 1], font=("Helvetica", 15))],
            [sg.Combo(['Intern Price-List(no regular update)', 'steamapis.com'], default_value=self.__getTextFromConfig('api_method'), key='api_method'), sg.Text('Key(only for steamapis):'), sg.Input(self.__getTextFromConfig('api_key'), key='api_key')],
            [sg.Text('Margins:', size=[30,1], font=("Helvetica", 15))],
            [sg.Text('Min Downgrade'), sg.Spin([i for i in range(-50,50)], initial_value=self.__getTextFromConfig('min_margin_downgrade'), key='min_margin_downgrade'), 
            sg.Text('Max Downgrade'), sg.Spin([i for i in range(-50,50)], initial_value=self.__getTextFromConfig('max_margin_downgrade'), key='max_margin_downgrade')],
            [sg.Text('Min Upgrade'), sg.Spin([i for i in range(-50,50)], initial_value=self.__getTextFromConfig('min_margin_upgrade'), key='min_margin_upgrade'), 
            sg.Text('Max Upgrade'), sg.Spin([i for i in range(-50,50)], initial_value=self.__getTextFromConfig('max_margin_upgrade'), key='max_margin_upgrade')],
            [sg.Text('Avoid Items in MY Inventory:', size=[22, 1], font=("Helvetica", 15)), sg.Text('Avoid Items in THEIR Inventory:', size=[22, 1], font=("Helvetica", 15))],
            [sg.Listbox(values=self.__getTextFromConfig('my_inv'), size=(30,5), key='_LISTBOX_MY'), sg.Listbox(values=self.__getTextFromConfig('their_inv'), size=(30,5), key='_LISTBOX_THEIR')],
            [sg.Button('Add', size=[14,1], key='_ADD_MY'), sg.Button('Delete', size=[14,1], key='_DELETE_MY'), sg.Button('Add', size=[14,1], key='_ADD_THEIR'), sg.Button('Delete', size=[14,1], key='_DELETE_THEIR')],
            [sg.Text('Discussion Links:', size=[30, 1], font=("Helvetica", 15)), sg.Text('Comment Section Links:', size=[30, 1], font=("Helvetica", 15))],
            [sg.Listbox(values=self.__getTextFromConfig('threads'), size=(40,10), key='_LISTBOX_THREADS'), sg.Listbox(values=self.__getTextFromConfig('comments'), size=(40,10), key='_LISTBOX_COMMENTS')],
            [sg.Button('Add', size=[18,1], key='_ADD_THREAD'), sg.Button('Delete', size=[18,1], key='_DELETE_THREAD'), sg.Button('Add', size=[18, 1], key='_ADD_COMMENT'), sg.Button('Delete', size=[18,1], key='_DELETE_COMMENT')]

        ]

        settings_frame = [
            [sg.Frame('Settings', settings_column, font=("Helvetica", 20), title_color='white')],
            [sg.Button('SAVE SETTINGS'), sg.Button('CREATE SESSION', button_color=(sg.YELLOWS[0], sg.BLUES[0]))]
        ]
        
        group_autowrite_column = [
            [sg.InputText(self.__getTextFromConfig('title'), key='title')],
            [sg.Multiline(self.__getTextFromConfig('message'), size=(45, 5), key='message')],
            [sg.Text('Available Groups:', size=[50, 1])],
            [sg.Listbox(values=self.__getTextFromConfig('avb'), size=(45, 5), enable_events=True, key='_LISTBOX_A_POST_GROUPS')],
            [sg.Text('Selected Groups:', size=[50, 1])], 
            [sg.Listbox(values=self.__getTextFromConfig('sld'), size=(45, 5), enable_events=True, key='_LISTBOX_S_POST_GROUPS')],
            [sg.Text('Post Frequenz(s)'), sg.Spin([i for i in range(10,5000)], initial_value=self.__getTextFromConfig('freq'), key='freq')],
            [sg.Checkbox('Comments', default=True, key="p_comment"), sg.Checkbox('Discussions', key='p_discussion')],
            [sg.HorizontalSeparator(pad=None)]
        ]

        autoposter_frame = [
            [sg.Frame('Auto Post Modul', group_autowrite_column, font=("Helvetica", 20), title_color='white')],
            [sg.Button('START POSTER', disabled=True, key='_START_POSTER'), sg.Button('STOP POSTER', disabled=True, key='_STOP_POSTER')]
        ]

        layout = [
            [
                sg.Column(settings_frame, element_justification='l'), 
                sg.VerticalSeparator(pad=None), sg.Column(output_column, element_justification='l'), 
                sg.VerticalSeparator(pad=None), sg.Column(autoposter_frame, element_justification='l') 
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
            window.FindElement('START').Update(disabled=True)
            window.FindElement('STOP').Update(disabled=False)
            for k, v in values.items():
                self.config = self.__updateConfig(self.config, k, v)
            self.__writeConfig()
            inv = self.handler.get_my_inventory(GameOptions.CS)
            t_message = values['_trade_message']
            trade_strategy = TradingStrategy.BOT if values['_bot_trade'] else TradingStrategy.USER
            selected_items = window.Element('_SEL_ITEMS').get_list_values()
            global thread
            thread = t.Thread(
                target=self.__start,
                args=(self.scraper, self.handler, inv, window, trade_strategy, selected_items, t_message),
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
            api = PriceAPIEndpoint.STEAMAPIS if values['api_method'] == 'steamapis.com' else PriceAPIEndpoint.INTERN
            self.handler = th.TradeHandler(api)
            self.scraper = scpr.Scraper()
            _session = self.handler.loginSteam()
            self.poster = ap.AutoPoster(_session)
            window.FindElement('START').Update(disabled=False)
            window.FindElement('_START_POSTER').Update(disabled=False)
            self.__updateInventoryListBox(window)
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
                args=(self.__getTextFromConfig('sld'), title, message, freq, com, disc),
                daemon=True
            )
            post_thread.start()
        elif event == '_AVA_ITEMS':
            s_values = values[event]
            o_values = window.Element('_SEL_ITEMS').get_list_values()
            for s in s_values:
                if s not in o_values:
                    o_values.append(s)
            window.Element('_SEL_ITEMS').Update(values=o_values)
        elif event == '_SEL_ITEMS':
            s_values = values[event]
            o_values = window.Element('_SEL_ITEMS').get_list_values()
            for s in s_values:
                o_values.remove(s)
            window.Element('_SEL_ITEMS').update(values=o_values)
        elif event == '_LISTBOX_A_POST_GROUPS':
            s_values = values[event]
            config_value = self.__getTextFromConfig('sld')
            if s_values not in config_value:
                for s in s_values:
                    config_value.append(s)
                window.Element('_LISTBOX_S_POST_GROUPS').update(values=config_value)
                self.__updateConfig(self.config, 'sld', config_value)
        elif event == '_LISTBOX_S_POST_GROUPS':
            s_values = values[event]
            config_value = [x for x in self.__getTextFromConfig('sld') if x not in s_values]
            window.Element('_LISTBOX_S_POST_GROUPS').update(values=config_value)
            self.__updateConfig(self.config, 'sld', config_value)
        elif event == '_STOP_POSTER':
            self.__stop_auto_poster(window)
        elif event == '_ADD_MY':
            self.__add_to_listbox('_LISTBOX_MY', 'Add new Element to avoid.', 'my_inv', values)
        elif event == '_DELETE_MY':
            self.__delete_from_listbox('_LISTBOX_MY', 'my_inv',  window, values)
        elif event == '_ADD_THEIR':
            self.__add_to_listbox('_LISTBOX_THEIR', 'Add new Element to avoid.', 'their_inv', values)
        elif event == '_DELETE_THEIR':
            self.__delete_from_listbox('_LISTBOX_THEIR', 'their_inv',  window, values)
        elif event == '_ADD_THREAD':
            self.__add_to_listbox('_LISTBOX_THREADS', 'Add new Link.', 'threads', window)
        elif event == '_DELETE_THREAD':
            self.__delete_from_listbox('_LISTBOX_THREADS', 'threads',  window, values)
        elif event == '_ADD_COMMENT':
            self.__add_to_listbox('_LISTBOX_COMMENTS', 'Add new Link.', 'comments', window)
        elif event == '_DELETE_COMMENT':
            self.__delete_from_listbox('_LISTBOX_COMMENTS', 'comments',  window, values)
        elif event == 'EXIT' or event == sg.WIN_CLOSED:
            return False

        return True

    def __add_to_listbox(self, listboxid, poptext, configpath, window):
        item = sg.popup_get_text(poptext)
        config_value = self.__getTextFromConfig(configpath)
        config_value.append(item)
        window.Element(listboxid).update(values=config_value)

    def __delete_from_listbox(self, listboxid, configpath, window, values):
        items = values[listboxid]
        config_value = self.__getTextFromConfig(configpath)
        new_config_value = [x for x in config_value if x not in items]
        window.Element(listboxid).update(values=new_config_value)
        self.__updateConfig(self.config, configpath, new_config_value)
        
    
    def __start_auto_poster(self, urls, title, message, freq, com=True, disc=True):
        thread = t.current_thread()
        counter = freq #Set to frequnz for instant searching when calling the method
        while getattr(thread, "do_run", True):
            if counter >= freq:
                log_status("Posted new Comment and Thread in all selected groups!")
                time.sleep(5)
                if com:
                    self.poster.postComments(urls, message)
                time.sleep(15)
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

    def __start(self, scraper, handler, inv, window, trade_strategy, selected_items, t_message):
        thread = t.current_thread()
        counter = 180 #Set to frequnz for instant searching when calling the method 
        log_status("Searching for trades...")
        while getattr(thread, "do_run", True):
            if counter >= 180: #search frequenz in seconds
                #Get Trade Links and SteamIds
                trade_urls = {**scraper.getTradeURLsComments(), **scraper.getTradeURLsThreads()}
                trade_counter = 0
                for steam_id, url in trade_urls.items():
                    if url in handler.get_session_trades():
                        continue
                    else:
                        handler.append_session_trade(url)
                    try:
                        partner_inv = handler.get_partner_inventory(steam_id, GameOptions.CS, merge=True)
                        trade = handler.calculateOptimalTrade(inv, partner_inv, trade_strategy, selected_items)
                        if trade is not None:
                            message = t_message
                            handler.make_offer_with_url(trade["my_items"], trade["their_items"], url, message=message)
                            trade_counter += 1
                            log_status("Created trade for you!")
                    except Exception as e:
                        log_status("Error in creating trade. Message: {}".format(str(e)))
                        #traceback.print_exc()
                log_status("End Searching for this period. Found: {} possible trades! Check your mobile App!".format(trade_counter))
                counter = 0
            time.sleep(1)
            counter += 1 

    def __stop(self, window):
        log_status("Stopped the Trading-Bot!")
        thread.do_run = False
        thread.join()
        window.FindElement('START').Update(disabled=False)
        window.FindElement('STOP').Update(disabled=True)


    def __updateInventoryListBox(self, window):
        inv = self.handler.get_my_inventory(GameOptions.CS)
        window.FindElement('_AVA_ITEMS').Update(values=[x['market_hash_name'] for x in inv.values() if x["tradable"]])

    def __readConfig(self, path):
        with open(path) as file:
            return json.load(file)

    def __writeConfig(self):
        with open(resource_path('config.json'), 'w') as outfile:
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


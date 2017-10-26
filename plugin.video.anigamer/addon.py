#! /usr/bin/python
# coding=UTF-8

# anigamer player
# author: YWJamesLin

import os
import sys
from datetime import datetime
import math

import xbmcaddon
import xbmcplugin
import xbmcgui

import re

import requests
import pickle
from bs4 import BeautifulSoup as BS
from urlparse import parse_qsl

# Parse plugin metadata
__url__ = sys.argv[0]
__handle__ = int (sys.argv[1])
xbmcplugin.setContent (__handle__,'movies')

# Check temp dir. exists
tempDir = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8')
if not os.path.isdir (tempDir) :
    os.makedirs (tempDir)

# Class to handle bahamut login, animate data and play video
class GamerAction () :
    def __init__(self) :
        self.this_addon = xbmcaddon.Addon ()
        self.authSite = 'https://user.gamer.com.tw'
        self.animeSite = 'https://ani.gamer.com.tw'

    # Check whether logined or not
    def check_login (self) :
        if os.path.isfile (tempDir + '/cookie') :
            with open (tempDir + '/cookie', 'r') as f :

                # Fetch saved cookie and session info
                cookies = requests.utils.cookiejar_from_dict (pickle.load (f))
                self.sessionAgent = requests.session ()
                self.sessionAgent.cookies = cookies
                f.close ()

            self.headers = {
                        'user-agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                        'origin' : self.animeSite
            }

            t = int(math.floor(((datetime.today()-datetime.fromtimestamp(0)).total_seconds()) * 1000 + 1))
            self.sessionAgent.get ("https://www.gamer.com.tw/ajax/notify.php?a=1&time={0}".format (t), headers = {
                'user-agent' : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
                'referer' : "https://www.gamer.com.tw"
                })
            with open (tempDir + '/cookie', 'w+') as f :
                pickle.dump (requests.utils.dict_from_cookiejar (self.sessionAgent.cookies), f)
                f.close ()

            return True
        else :
            return False

    # show main menu
    def list_main (self) :
        __language__ = self.this_addon.getLocalizedString

        thisList = []

        all_item = xbmcgui.ListItem (label = __language__ (33001))
        url = '{0}?action=list_all&page=1'.format (__url__)
        thisList.append ((url, all_item, True))

        favor_item = xbmcgui.ListItem (label = __language__ (33002))
        url = '{0}?action=list_favor'.format (__url__)
        thisList.append ((url, favor_item, True))

        xbmcplugin.addDirectoryItems (__handle__, thisList, len (thisList))
        xbmcplugin.endOfDirectory (__handle__)

    # list all animes separated by page
    def list_all (self, page) :
        __language__ = self.this_addon.getLocalizedString

        thisList = []

        result = self.sessionAgent.get (self.animeSite + '/animeList.php', params = { 'page' : page, 'c' : '0','sort' : '0' }, headers = self.headers)
        soup = BS (result.content.decode ('utf-8'), 'html.parser')
        anime_list = soup.find ('ul', {'class':'anime_list'})


        # create anime list
        for anime_item in anime_list.find_all ('li') :
            picBlock = anime_item.find ('div', { 'class' : 'pic lazyload' })
            nameBlock = anime_item.find ('div', { 'class' : 'info' })
            name = nameBlock.b.text
            pic = picBlock['data-bg']
            ref = anime_item.a ['href']
            sn = re.sub (r"a.+sn=", "", ref)
            list_item = xbmcgui.ListItem (label = name)
            list_item.setArt ({'thumb': pic})
            url = "{0}?action=anime_huei&sn={1}".format (__url__, sn)
            thisList.append ((url, list_item, True))

        # create nextpage item
        nextpage_item = xbmcgui.ListItem (label = __language__ (33011))
        url = "{0}?action=list_all&page={1}".format (__url__, int (page) + 1)
        thisList.append ((url, nextpage_item, True))

        xbmcplugin.addDirectoryItems (__handle__, thisList, len (thisList))
        xbmcplugin.addSortMethod (__handle__, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod (__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.endOfDirectory (__handle__)

    # list favorite animes
    def list_favor (self) :
        result = self.sessionAgent.get (self.animeSite + '/mygather.php', headers = self.headers)
        soup = BS (result.content.decode ('utf-8'), 'html.parser')
        anime_list = soup.find ('ul', { 'class' : 'anime_list' })

        thisList = []

        # create anime list
        for anime_item in anime_list.find_all ('li') :
            nameBlock = anime_item.find ('div', { 'class' : 'info' })
            picBlock = anime_item.find ('div', { 'class' : 'pic lazyload' })
            name = nameBlock.b.text
            pic = picBlock['data-bg']
            ref = anime_item.a ['href']
            sn = re.sub (r"a.+sn=", "", ref)
            list_item = xbmcgui.ListItem (label = name, iconImage = pic)
            url = "{0}?action=anime_huei&sn={1}".format (__url__, sn)
            thisList.append ((url, list_item, True))

        xbmcplugin.addDirectoryItems (__handle__, thisList, len (thisList))
        xbmcplugin.addSortMethod (__handle__, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod (__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.endOfDirectory (__handle__)

    # list vol.
    def anime_huei (self, sn) :
        result = self.sessionAgent.get (self.animeSite + '/animeRef.php?sn=' + sn, headers = self.headers)
        soup = BS (result.content.decode ('utf-8'), 'html.parser')

        # get anime title
        title = soup.head.title.text
        title = re.sub(r"(\[[0-9]+\])? - .+", "", title)

        anime_list = soup.find ('ul', { 'id' : 'vul0_000' })
        thisList = []
        # handle if has no vol. list
        if anime_list is None :
            singleResult = self.sessionAgent.get (self.animeSite + '/animeRef.php?sn=' + sn, allow_redirects = False, headers = self.headers)
            newsn = singleResult.headers ['Location']
            newsn = re.sub (r".+\?sn=", "", newsn)
            list_item = xbmcgui.ListItem (label = title)
            url = "{0}?action=play&sn={1}&name={2}".format (__url__, newsn, title.encode('utf-8'))
            thisList.append ((url, list_item, False))
        # create vol. list
        else :
            for anime_item in anime_list.find_all ('li') :
                ref = anime_item.a ['href']
                sn = re.sub (r"\?sn=", "", ref)
                name = title + " " + anime_item.a.text
                list_item = xbmcgui.ListItem (label = name)
                url = "{0}?action=play&sn={1}&name={2}".format (__url__, sn, name.encode ('utf-8'))
                thisList.append ((url, list_item, False))
        xbmcplugin.addDirectoryItems (__handle__, thisList, len (thisList))
        xbmcplugin.addSortMethod (__handle__, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod (__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.endOfDirectory (__handle__)

    # create video link and play on kodi
    def play (self, sn, name) :
        result = self.sessionAgent.get (self.animeSite + '/ajax/getdeviceid.php', headers = self.headers)
        jsonData = result.json ()
        deviceID = jsonData ['deviceid']

        result = self.sessionAgent.get (self.animeSite + '/ajax/m3u8.php?sn=' + sn + '&device=' + deviceID, headers = self.headers)
        jsonData = result.json ()
        src = re.sub(r"([a-zA-Z]+:)?//", "", jsonData ['src'])
        src = "https://" + src

        result = self.sessionAgent.get (src)
        spstr = result.text.split ()
        newsrc = re.sub (r"\/index.+", "", src)
        thisAnime = xbmcgui.ListItem (name)
        thisAnime.setInfo ('video', {'Title': name, 'Genre': 'Animation'})
        xbmc.Player ().play (newsrc + '/' + spstr[-1], thisAnime)

    def queue (self, url, name) :
        queued = xbmcgui.ListItem(name)
        xbmc.PlayList(1).add (url, queued);

def router (paramstring, action):
    if action.check_login () == False :
        quit ()
    params = dict (parse_qsl (paramstring[1:]))
    if params :
        if params ['action'] == 'list_all' :
            action.list_all (params ['page'])
        elif params ['action'] == 'list_favor' :
            action.list_favor ()
        elif params ['action'] == 'anime_huei' :
            action.anime_huei (params['sn'])
        elif params ['action'] == 'play' :
            action.play (params['sn'], params['name'].decode('utf-8'))
    else :
        action.list_main ()

## Main
action = GamerAction ()
if __name__ == '__main__' :
    router (sys.argv[2], action)

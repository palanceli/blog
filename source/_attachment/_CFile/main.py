# -*- coding: utf-8 -*-
import logging
import wx
import wx.grid
import sqlite3
import ConfigParser
import os
import sys

class CData(object):
    def __init__(self, dataPath):
        self.data = []
        conn = sqlite3.connect(dataPath)
        cursor = conn.cursor()
        logging.debug('open data file:%s' % dataPath)
        sqlString = 'CREATE TABLE TableMain (Title text, Content text)' 
        cursor.execute(sqlString)

        sqlString = 'SELECT rowid, Title, Content FROM TableMain'
        cursor.execute(sqlString)
        result = cursor.fetchall()
        for row in result:
            rowid = row[0]
            title = row[1]
            content = row[2]
            self.data.append([rowid, title, content])

        print self.data
            
class CConfig(object):
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        configPath = os.path.join(os.path.expanduser('~'), '.cfile')

        config.read(configPath)
        self.dataPath = config.get('config', 'datapath')
        
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'CFile', size=(800, 420))

        self.config = CConfig()
        self.cdata = CData(self.config.dataPath)
        
        panel = wx.Panel(self, -1)
        vSizer = wx.BoxSizer(wx.VERTICAL)

        self.grid = wx.grid.Grid(panel, -1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.grid, 1, wx.ALL|wx.EXPAND, 5)
        vSizer.Add(sizer, 1, wx.ALL|wx.EXPAND)

        self.text = wx.TextCtrl(panel, -1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.text, 1, wx.ALL|wx.EXPAND, 5)
        vSizer.Add(sizer, 0, wx.ALL|wx.EXPAND)
        
        panel.SetSizer(vSizer)
        
    def OnClose(self, event):
        wx.Exit()

class MainApp(wx.App):
    def __init__(self, redirect = False, filename=None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = MainFrame()
        self.frame.Show()
        self.frame.Center()
        self.SetTopWindow(self.frame)
        return True

if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M')
    app = MainApp()
    app.MainLoop()

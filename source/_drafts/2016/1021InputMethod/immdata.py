# -*- coding:utf-8 -*-
import logging


class IMMData(object):
    def __init__(self):
        self.coreData = {'Composition' : ['', ''], # (当前值, 默认值)
                         'CompDisplay' : ['', ''],
                         'Candidates'  : [[], []],
                         'Completed'   : ['', ''],
                         'cursorPos'   : [0,  0],
        }
        self.settings = {'maxCandCount' : [5, 5],
        }

    def GetCoreData(self, key):
        return self.coreData[key][0]

    def SetCoreData(self, key, value):
        self.coreData[key][0] = value
        return self.coreData[key][0]

    def ResetCoreData(self, *keylist):
        if keylist == None or len(keylist) == 0:
            for k, v in self.coreData.items():
                self.coreData[k][0] = self.coreData[k][1]
        else:
            for k in keylist:
                self.coreData[k][0] = self.coreData[k][1]

    def GetSetting(self, key):
        return self.settings[key][0]

    def SetSetting(self, key, value):
        self.settings[key][0] = value
        return self.settings[key][0]

    def ResetSetting(self, *keylist):
        if keylist == None or len(keylist) == 0:
            for k, v in self.settings.items():
                self.settings[k][0] = self.settings[k][1]
        else:
            for k in keylist:
                self.settings[k][0] = self.settings[k][1]



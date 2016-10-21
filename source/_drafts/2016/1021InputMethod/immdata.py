# -*- coding:utf-8 -*-

class IMMData(object):
    def __init__(self):
        self.coreData = {'Composition' : '', 'Candidates' : [], 'Completed' : ''}
        self.settings = {'maxCandCount' : 5}

    def GetCoreData(self, key):
        return self.coreData[key]

    def SetCoreData(self, key, value):
        self.coreData[key] = value
        return self.coreData[key]

    def GetSetting(self, key):
        return self.settings[key]

    def SetSetting(self, key, value):
        self.settings[key] = value
        return self.settings[key]



# -*- coding:utf-8 -*-
import logging
import sys
import tty
import termios
import immdata
import immconv

class IMMState(object):
    currState = None
    
    def __init__(self, imm):
        self.imm = imm

    @staticmethod
    def GetState(self):
        if IMMState.currState == None:
            IMMState.currState = IMMReadyState.GetInstance()
        return IMMState.currState

    @staticmethod
    def SetState(state):
        IMMState.currState = state
        return IMMState.currState

    def ProcessChar(self, ch):
        pass

    def GetStateName(self):
        return 'IMMState'

class IMMReadyState(IMMState):
    selfObj = None

    @staticmethod
    def GetInstance():
        if IMMReadyState.selfObj == None:
            IMMReadyState.selfObj = IMMReadyState(InputMethodManager.GetInstance())
        return IMMReadyState.selfObj
        
    def __init__(self, imm):
        IMMState.__init__(self, imm)

    def GetStateName(self):
        return 'IMMReadyState'

    def ProcessChar(self, ch):
        if ch.islower():
            currState = IMMState.SetState(IMMPinyinState.GetInstance())
            currState.ProcessChar(ch)
        elif ch.isdigit() or ch.isupper():
            self.imm.SetComposition('')
            self.imm.SetCandidates([])
            self.imm.SetCompleted(ch)

class IMMPinyinState(IMMState):
    selfObj = None
    
    @staticmethod
    def GetInstance():
        if IMMPinyinState.selfObj == None:
            IMMPinyinState.selfObj = IMMPinyinState(InputMethodManager.GetInstance())
        return IMMPinyinState.selfObj

    def GetStateName(self):
        return 'IMMPinyinState'

    def ProcessChar(self, ch):
        if ch.isalpha():
            self.imm.SetCoreData('Composition', self.imm.GetCoreData('Composition') + ch)
            convertor = self.imm.immConvertor
            self.imm.SetCoreData('Candidates', convertor.ConvertPinyin(self.imm.GetCoreData('Composition')))
        elif ch.isdigit():
            i = int(ch)
            if i > self.imm.GetSetting('maxCandCount') and i > len(self.imm.GetCoreData('Candidates')):
                pass
            else:
                self.imm.SetCoreData('Completed', self.imm.GetCoreData('Candidates')[i - 1])
                self.imm.SetCoreData('Composition', '')
                self.imm.SetCoreData('Candidates', [])

class InputMethodManager(object):
    selfObj = None

    @staticmethod
    def GetInstance():
        if InputMethodManager.selfObj == None:
            InputMethodManager.selfObj = InputMethodManager()
        return InputMethodManager.selfObj
    
    def __init__(self):
        self.immData = immdata.IMMData()
        self.immConvertor = immconv.IMMConvertor(self.immData)

    def SetCoreData(self, key, value):
        return self.immData.SetCoreData(key, value)

    def GetCoreData(self, key):
        return self.immData.GetCoreData(key)

    def SetSetting(self, key, value):
        return self.immData.SetSetting(key, value)

    def GetSetting(self, key):
        return self.immData.GetSetting(key)
        
    def ProcessChar(self, ch):
        state = IMMState.currState
        state.ProcessChar(ch)

class MainProc(object):
    def __init__(self):
        self.imm = InputMethodManager.GetInstance()
        IMMState.currState = IMMReadyState.GetInstance()
        
    def Run(self):
        fd = sys.stdin.fileno()
        oldSettings = termios.tcgetattr(fd)

        ctlString = None
        try:
            while True:
                tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
                ch = sys.stdin.read(1)
                if ch == '\n' or ch == '\r':
                    if len(self.imm.GetCoreData('Composition')) == 0:
                        return
                    
                if ctlString != None:   # 当前正在输入控制字符
                    if ch != '>':
                        ctlString += ch # 如果当前字符不是“>”，则继续输入控制字符
                    else:               # 如果当前字符是“>”，把控制字符输入IMM
                        self.imm.ProcessChar(ctlString)
                        ctlString = None
                else:
                    if ch == '<':       # 当前输入字符是“<”，则进入控制字符模式
                        ctlString = ''
                    else:
                        self.imm.ProcessChar(ch)
                if ctlString == None:
                    sys.stdout.write('输入串:%s\r\n' % self.imm.GetCoreData('Composition'))
                    candString = ''
                    for i in range(self.imm.GetSetting('maxCandCount')):
                        if i >= len(self.imm.GetCoreData('Candidates')):
                            break
                        candString += '%d:%s ' % (i+1, self.imm.GetCoreData('Candidates')[i])
                    sys.stdout.write('候选串:%s\r\n' % candString)
                    sys.stdout.write('上屏串:%s\r\n' % self.imm.GetCoreData('Completed'))
                    sys.stdout.write('当前状态:%s\r\n' % IMMState.currState.GetStateName())
                    sys.stdout.write('\n')
                    
                    if len(self.imm.GetCoreData('Completed')) > 0:
                        self.imm.SetCoreData('Composition', '')
                        self.imm.SetCoreData('Candidates', [])
                        self.imm.SetCoreData('Completed', '')
                else:
                    sys.stdout.write('控制串:%s\r\n\n' % ctlString)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)

if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)
    mainProc = MainProc()
    mainProc.Run()

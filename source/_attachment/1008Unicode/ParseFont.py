# -*- coding:utf-8 -*-

import logging
import struct
import sys
import fontTools
import fontTools.ttLib
import traceback
import os

class FontParser(object):
    class FontStat(object):
        def __init__(self):
            self.result = {'CJK':[0x4E00, 0x9FFF, 0, []], \
                           'ExtA':[0x3400, 0x4DBF, 0, []], \
                           'ExtB':[0x20000, 0x2A6DF, 0, []],\
                           'ExtC':[0x2A700, 0x2B73F, 0, []],\
                           'ExtD':[0x2B740, 0x2B81F, 0, []],\
                           'ExtE':[0x2B820, 0x2CEAF, 0, []],\
                           'CI':[0xF900, 0xFAFF, 0, []],\
                           'CIS':[0x2F800, 0x2FA1F, 0, []]}

        def Add(self, code):
            for k, v in self.result.items():
                if code >= v[0] and code <= v[1]:
                    try:
                        v[3].index(code)
                    except:
                        v[3].append(code)
                        v[2] += 1

        def Show(self):
            for k, v in self.result.items():
                logging.debug('%s:%d' % (k, v[2]))
        
    def parse(self, font):
        result = {'CJK':[0x4E00, 0x9FFF, 0], \
                  'ExtA':[0x3400, 0x4DBF, 0], \
                  'ExtB':[0x20000, 0x2A6DF, 0],\
                  'ExtC':[0x2A700, 0x2B73F, 0],\
                  'ExtD':[0x2B740, 0x2B81F, 0],\
                  'ExtE':[0x2B820, 0x2CEAF, 0],\
                  'CI':[0xF900, 0xFAFF, 0],\
                  'CIS':[0x2F800, 0x2FA1F, 0]}
        
        for name in font.getGlyphNames():
            if not name.startswith('uni'):
                continue
            try:
                code = int(float.fromhex(name[3 : ]))
            except:
                #traceback.print_exc()
                continue
                    
            for k, v in result.items():
                if code >= v[0] and code <= v[1]:
                    v[2] += 1
                        
        for k, v in result.items():
            logging.debug('%s:%d' % (k, v[2]))
            
    def parse4(self, font):
        for name in font.getGlyphNames():
            id = font.getGlyphID(name)
            logging.debug('name:%s, id:%d' % (name, id))
            
    def parse2(self, font):
        for k, v in font.items():
            logging.debug('k:%s, v:%s' % (k, v))
            
    def parse3(self, font):
        cnt = 0
        for cmap in font['cmap'].tables:
            if cmap.isUnicode():
                cnt += 1
        logging.debug('unicode: %d' % cnt)

    def parse5(self, font):
        stat = self.FontStat()
        for t in font['cmap'].tables:
            for k, v in t.cmap.items():
                stat.Add(k)
        stat.Show()
                
        
    def ParseTTC(self, fontPath, fontNumber):
        logging.debug('Parsing %s' % (fontPath))
        for fontNumber in range(fontNumber):
            font = fontTools.ttLib.TTFont(fontPath, fontNumber=fontNumber)
            #self.parse(font)

    def ParseTTF(self, fontPath):
        logging.debug('Parsing %s' % (fontPath))
        font = fontTools.ttLib.TTFont(fontPath)
        #for t in font['cmap'].tables:
        #    for k, v in t.cmap.items():
        #        print k, v
        #sys.exit(0)
        self.parse5(font)

if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)
    fontDir = '/Users/palance/Downloads/fonts'
    fontParser = FontParser()
    #fontParser.ParseTTF(os.path.join(fontDir, 'winxp', 'MSYH.TTF'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'winxp', 'simsun_2.ttf'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'win7', 'msyh.ttf'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'win7', 'simsun_1.ttf'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'Android7.1', 'DroidSansFallback.ttf'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'iOS9', 'PingFang_2.ttf'))
    fontParser.ParseTTF(os.path.join(fontDir, 'macOS_Serra_10.12.3', 'PingFang.ttc'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'win7', 'mingliu', 'mingliu_2.ttf'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'win7', 'msmincho', 'msmincho_1.ttf'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'win7', 'batang', 'batang_0.ttf'))
    #fontParser.ParseTTF(os.path.join(fontDir, 'win7', 'simsunb.ttf'))

# -*- coding:utf-8 -*-

import logging
import struct
import sys
import fontTools
import fontTools.ttLib
import traceback

class FontParser(object):
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
                traceback.print_exc()
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

    def ParseTTC(self, fontPath):
        for fontNumber in range(35):
            font = fontTools.ttLib.TTFont(fontPath, fontNumber=fontNumber)
            #self.parse(font)

    def ParseTTF(self, fontPath):
        font = fontTools.ttLib.TTFont(fontPath)
        self.parse(font)

if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)
    fontParser = FontParser()
    #fontParser.ParseTTC('./PingFang.ttc')
    fontParser.ParseTTF('/Users/palance/Downloads/fonts/winxp/MSYH.TTF')

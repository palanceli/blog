# -*- coding:utf-8 -*-

import logging
import struct
import sys
import fontTools
import fontTools.ttLib

class FontParser(object):
    def parse(self, font):
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
        #self.parse(font)

if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)
    fontParser = FontParser()
    fontParser.ParseTTC('./PingFang.ttc')
    fontParser.ParseTTF('./华文仿宋.ttf')

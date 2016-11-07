# -*- coding:utf-8 -*-
import logging
import optparse
import sys

''' 动态规划 '''

class Ex01(object):
    ''' 人民币面值有1元、2元、5元、10元、20元、50元、100元，给出X元最少需要几张纸币？'''
    def Main(self):
        self.result = {1:0, 2:0, 5:0, 10:0, 20:0, 50:0, 100:0}
        x = 211
        msg = '共需要纸币%d张。' % self.proc(x)
        if self.result[100] > 0:
            msg += ' %d张100元' % self.result[100]
        if self.result[50] > 0:
            msg += ' %d张50元' % self.result[50]
        if self.result[20] > 0:
            msg += ' %d张20元' % self.result[20]
        if self.result[10] > 0:
            msg += ' %d张10元' % self.result[10]
        if self.result[5] > 0:
            msg += ' %d张5元' % self.result[5]
        if self.result[2] > 0:
            msg += ' %d张2元' % self.result[2]
        if self.result[1] > 0:
            msg += ' %d张1元' % self.result[1]
        logging.debug(msg)

    def proc(self, value):
        if value == 0:
            return 0

        if value >= 100:
            self.result[100] += 1
            return 1 + self.proc(value - 100)
        elif value >= 50:
            self.result[50] += 1
            return 1 + self.proc(value - 50)
        elif value >= 20:
            self.result[20] += 1
            return 1 + self.proc(value - 20)
        elif value >= 10:
            self.result[10] += 1
            return 1 + self.proc(value - 10)
        elif value >= 5:
            self.result[5] += 1
            return 1 + self.proc(value - 5)
        elif value >= 2:
            self.result[2] += 1
            return 1 + self.proc(value - 2)
        elif value == 1:
            self.result[1] += 1
            return 1
        else:
            return 0


if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)

    optParser = optparse.OptionParser()
    (opts, args) = optParser.parse_args()
    # 只接收一个参数
    if len(args) != 1:
        logging.error('参数错误！调用格式python xxx.py <ClassName>.<procName>')
        sys.exit(0)

    # 把class name 和proc name解析出来
    clsName, procName = args[0].split('.')
    # 实例化并调用
    cls = getattr(sys.modules['__main__'], clsName)
    proc = getattr(cls(), procName)
    proc()

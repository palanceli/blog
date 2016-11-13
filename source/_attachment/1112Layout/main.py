# -*- coding:utf-8 -*-

import logging
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QFrame
from PyQt5 import QtCore


class MyLayout(object):
    def __init__(self, name, widget, **kw):
        # name 名字
        # widget 所在的父窗口
        # layouts 所包含的子layout
        # parentLayout 所在的父layout
        # weightX weightY 在父layout中的拉伸比例
        # marginU marginD marginL marginR 上下左右margin值
        self.data = {}
        self.setData('name', name)
        self.setData('widget', widget)
        self.setData('layouts', [])

        for k, v in kw.items():
            self.setData(k, v)
        if 'parentLayout' not in self.data:
            self.setData('parentLayout', None)
        if 'weight' not in self.data:
            self.setData('weight', 1)

        self.createLabel()

    def createLabel(self):
        self.label = QLabel(self.getData('name'), self.getData('widget'))
        self.label.setFrameStyle(QFrame.Box)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

    def Adjust(self):
        x, y = self.getData('x'), self.getData('y'),
        w, h = self.getData('w'), self.getData('h')
        # x、y是相对于父layout的偏移，应当一直找到最顶层
        parentLayout = self.getData('parentLayout')
        while parentLayout is not None:
            x += parentLayout.getData('x')
            y += parentLayout.getData('y')
            parentLayout = parentLayout.getData('parentLayout')

        text = '%s(%d, %d, %d, %d, %.1f)' % (
            self.getData('name'),
            x, y, w, h, self.getData('weight'))

        self.label.setText(text)
        self.label.resize(w, h)
        self.label.move(x, y)

        logging.debug(text)

    def getData(self, key):
        return self.data[key]

    def setData(self, key, value):
        self.data[key] = value
        if key.startswith('fixed'):
            key = key[5:].lower()
            self.data[key] = value
            logging.debug('add {%s:%s}' % (key, value))

    def hasData(self, key):
        return key in self.data

    def AddLayout(self, newLayout):
        # for debug
        name = newLayout.getData('name').strip()
        parentLayout = newLayout.getData('parentLayout')
        while parentLayout is not None:
            name = ' ' + name
            parentLayout = parentLayout.getData('parentLayout')
        newLayout.setData('name', name)
        # endof debug

        self.getData('layouts').append(newLayout)
        self.Adjust()


class MyVLayout(MyLayout):
    def AddStretch(self, weight):
        name = '%s工' % self.getData('name')
        newLayout = MyLayout(name=name, widget=self.getData('widget'),
                             parentLayout=self, fixedW=self.getData('w'),
                             weight=weight)
        super().AddLayout(newLayout)

    def Adjust(self):
        # VLayout的Adjust主要解决个子项的高度
        logging.debug('Adjust{{{')
        marginL = 0
        if self.hasData('marginL'):
            marginL = self.getData('marginL')

        layouts = self.getData('layouts')
        fixedHeightSum = 0  # 子项中已定高的总和
        weightSum = 0       # 子项中已指定的权重和
        for i in layouts:
            if i.hasData('fixeH'):
                fixedHeightSum += i.getData('fixedH')
            if i.hasData('weight'):
                weightSum += i.getData('weight')

        currY = 0
        if self.hasData('marginU'):
            currY = self.getData('marginU')
        if not self.hasData('fixedH'):
            # 如果不定高，则所有子项必然定高，且没有stretch，
            # 自己的高度由子项和决定，个子项的x、y坐标由前面的子项决定
            for i in layouts:
                i.setData('x', marginL)
                i.setData('y', currY)
                currY += i.getData('h')
            if self.hasData('marginD'):
                currY += self.getData('marginD')
            self.setData('h', currY)
        else:
            # 如果定高，则子项中可能有定宽的，也可能有stretch
            # 根据heightRemained计算各stretch的高度，子项的x、y由前面的子项决定
            heightRemained = self.getData('fixedH') - weightSum
            for i in layouts:
                i.setData('x', marginL)
                i.setData('y', currY)
                if not i.hasData('fixedH'):       # 如果子项不定高，计算其高度
                    subItemHeight = heightRemained * i.getData('weight') \
                                    / weightSum
                    i.setData('h', subItemHeight)
                    currY += subItemHeight
                else:
                    currY += i.getData('h')
        super().Adjust()
        for i in layouts:
            i.Adjust()
        logging.debug('Adjust}}}')


class MyHLayout(MyLayout):
    def AddStretch(self, weight):
        name = '%sH' % self.getData('name')
        height = self.getData('h')
        if self.hasData('marginU'):
            height -= self.getData('marginU')
        if self.hasData('marginD'):
            height -= self.getData('marginD')
        newLayout = MyLayout(name=name, widget=self.getData('widget'),
                             parentLayout=self,
                             fixedH=height, weight=weight)
        super().AddLayout(newLayout)

    def Adjust(self):
        # HLayout的Adjust主要解决的是各子项的宽度，
        if self.getData('name') == 'root':
            logging.debug(' ')
        logging.debug('Adjust{{{')
        marginU = 0
        if self.hasData('marginU'):
            marginU = self.getData('marginU')

        layouts = self.getData('layouts')
        fixedWidthSum = 0   # 子项中已定宽的总和
        if self.hasData('marginL'):
            fixedWidthSum += self.getData('marginL')
        if self.hasData('marginR'):
            fixedWidthSum += self.getData('marginR')
            
        weightSum = 0       # 子项中已指定的权重和
        for i in layouts:
            if i.hasData('fixedW'):
                fixedWidthSum += i.getData('fixedW')
            if i.hasData('weight'):
                weightSum += i.getData('weight')

        currX = 0
        if self.hasData('marginL'):
            currX = self.getData('marginL')
        if not self.hasData('fixedW'):
            # 如果不定宽，则所有子项必然定宽，且没有stretch，
            # 自己的宽度由子项和决定，各子项的x、y坐标由前面的子项决定
            for i in layouts:
                i.setData('x', currX)
                i.setData('y', marginU)
                currX += i.getData('w')
            if self.hasData('marginR'):
                currX += self.getData('marginR')
            self.setData('w', currX)
        else:
            # 如果定宽，则子项中可能有定宽的，也可能有stretch，
            # 根据weightRemained计算各stretch的宽度，子项的x、y由前面的子项决定
            widthRemained = self.getData('fixedW') - fixedWidthSum
            for i in layouts:
                i.setData('x', currX)
                i.setData('y', marginU)
                if not i.hasData('fixedW'):     # 如果子项不是定宽，计算其宽度
                    subItemWidth = widthRemained * i.getData('weight') \
                                   / weightSum
                    i.setData('w', subItemWidth)
                    currX += subItemWidth
                else:
                    currX += i.getData('w')

        super().Adjust()
        for i in layouts:
            i.Adjust()

        logging.debug('Adjust}}}')


class MyPageLayout(MyLayout):
    def __init__(self, name, widget, **kw):
        super().__init__(name, widget, **kw)
        self.setData('widthHeightTimes', 1.5)

    def getData(self, key):
        if key == 'w' or key == 'fixedW':
            return self.getData('h') * self.getData('widthHeightTimes')
        return super().getData(key)


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI_tc3()
        self.show()

    def initUI_tc3(self):
        self.resize(1200, 600)
        rootLayoutX = 0
        rootLayoutY = 100
        rootLayoutH = 400
        marginUp = rootLayoutH * 0.5 / 7.5
        marginDown = rootLayoutH * 0.5 / 7.5
        marginLeft = marginUp * 2
        marginRight = marginUp * 2
        marginMid = marginUp * 0.6
        pageHeight = rootLayoutH - marginUp - marginDown
        pageWidth = pageHeight * 1.6

        # 根布局root，根据客户端传入的屏幕指标定宽定高
        rootLayout = MyHLayout('root', self, parentLayout=None,
                               fixedX=rootLayoutX, fixedY=rootLayoutY,
                               fixedH=rootLayoutH,
                               marginU=marginUp, marginD=marginDown,
                               marginL=marginLeft, marginR=marginRight)

        # 一级Page1布局，根据客户端传入的屏幕指标定高、宽度根据高计算出来
        P1 = MyVLayout('P1', self, parentLayout=rootLayout,
                       fixedW=pageWidth, fixedH=pageHeight)
        rootLayout.AddLayout(P1)

        # Page1内布局
        P1L1 = MyHLayout('P1L1', self, parentLayout=P1,
                         fixedW=pageWidth,
                         marginL=marginMid, marginU=marginUp*0.5,
                         marginR=marginMid, marginD=marginUp*0.5,
                         weight=3.7)

        P1.AddLayout(P1L1)
        # layout.AddStretch(3.7)
        P1.AddStretch(1.4)
        P1.AddStretch(1.4)

        P1L1.AddStretch(3)
        P1L1.AddStretch(6.3)

        # 一级margin布局，根据客户端传入的屏幕指标定宽定高
        M1 = MyLayout('M1', self, parentLayout=rootLayout,
                      fixedW=marginMid, fixedH=pageHeight)
        rootLayout.AddLayout(M1)

        # 一级Page布局
        P2 = MyPageLayout('P2', self, parentLayout=rootLayout,
                          fixedH=pageHeight)
        rootLayout.AddLayout(P2)
        # 页面内二级布局V

    def initUI_tc2(self):
        self.resize(450, 800)

        rootLayout = MyHLayout('root', self, parentLayout=None,
                               x=0, y=400, w=450, h=400)
        rootLayout.AddStretch(0.5)
        rootLayout.AddStretch(9)
        rootLayout.AddStretch(0.5)

    def initUI_tc1(self):
        self.resize(450, 800)

        rootLayout = MyVLayout('root', self, parentLayout=None,
                               x=0, y=400, w=450, h=400)
        rootLayout.AddStretch(0.5)
        rootLayout.AddStretch(9)
        rootLayout.AddStretch(0.5)

if __name__ == '__main__':
    logFmt = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=logFmt, datefmt='%H:%M',)
    app = QApplication(sys.argv)
    mainWidget = MainWidget()
    sys.exit(app.exec_())

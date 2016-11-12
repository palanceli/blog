# -*- coding:utf-8 -*-

import logging
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QLabel, QFrame
from PyQt5 import QtCore

class MyLayout(object):
    def __init__(self, name, widget, **kw):
        self.data = {"name":name, "widget":widget, "layouts":[]}
        if 'parentLayout' not in self.data:
            self.data['parentLayout'] = None
        self.data.update(kw)

    def createLabel(self):
        label = QLabel(self.getData('name'), self.getData('widget'))
        label.setFrameStyle(QFrame.Box)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.resize(self.getData('w'), self.getData('h'))
        label.move(self.getData('x'), self.getData('y'))
        
    def getData(self, key):
        return self.data[key]
        
    def AddLayout(self, layout):
        self.getData('layouts').append(layout)

    def AddStretch(self, weight):
        pass


class MyVLayout(MyLayout):
    def __init__(self, name, widget, **kw):
        super().__init__(name, widget, **kw)
        self.createLabel()


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.show()

    def initUI(self):
        self.resize(450, 800)

        rootLayout = MyVLayout('root', self, parentLayout=None, x=0, y=400, w=450, h=400)
        rootLayout.AddStretch(0.5)
        rootLayout.AddStretch(9)
        rootLayout.AddStretch(0.5)

if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)
    app = QApplication(sys.argv)
    mainWidget = MainWidget()
    sys.exit(app.exec_())

# -*- coding:utf-8 -*-
# -*- py-python-command: "/usr/bin/python3"; -*-

import logging
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, \
    QLineEdit, QLabel, QListWidget
import imm


class QLineEdit4Ime(QLineEdit):
    def __init__(self, inputMethodManager, parent):
        super().__init__(parent)
        self.imm = inputMethodManager

    def getIMM(self):
        return self.imm

    def keyPressEvent(self, event):
        logging.debug(event.text())
        self.getIMM().ProcessChar(event.text())
        if len(self.getIMM().GetCoreData('Completed')) > 0:
            text = self.text()
            text += self.getIMM().GetCoreData('Completed')
            self.setText(text)
            self.getIMM().ResetCoreData()
        
        self.parentWidget().ImeKeyPressEvent()


class ImePanel(QWidget):
    def __init__(self, inputMethodManager):
        super().__init__()
        self.imm = inputMethodManager
        self.qLineImmDict = {}
        self.initUI()

    def getIMM(self):
        return self.imm

    def initUI(self):
        self.resize(800, 600)
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        subvbox = QVBoxLayout()

        subhbox = QHBoxLayout()
        label = QLabel('当前状态：', self)
        subhbox.addWidget(label)
        self.stateNameEditBox = QLineEdit(self)
        self.stateNameEditBox.setReadOnly(True)
        subhbox.addWidget(self.stateNameEditBox)
        subhbox.setStretchFactor(self.stateNameEditBox, 2)
        self.qLineImmDict[self.stateNameEditBox] = 'currStateName'
        subvbox.addLayout(subhbox)
 
        subhbox = QHBoxLayout()
        label = QLabel('光标位置：', self)
        subhbox.addWidget(label)
        self.cursorPosEditBox = QLineEdit(self)
        self.cursorPosEditBox.setReadOnly(True)
        self.cursorPosEditBox.resize(100, 30)
        subhbox.addWidget(self.cursorPosEditBox)
        subvbox.addLayout(subhbox)
        self.qLineImmDict[self.cursorPosEditBox] = 'cursorPos'
 
        subhbox = QHBoxLayout()
        label = QLabel('上屏串：', self)
        subhbox.addWidget(label)
        self.completedEditBox = QLineEdit(self)
        self.completedEditBox.setReadOnly(True)
        subhbox.addWidget(self.completedEditBox)
        subvbox.addLayout(subhbox)  # 行---------------------
        self.qLineImmDict[self.completedEditBox] = 'Completed'
  
        subhbox = QHBoxLayout()
        label = QLabel('输入串：', self)
        subhbox.addWidget(label)
        self.compositionEditBox = QLineEdit(self)
        self.compositionEditBox.setReadOnly(True)
        subhbox.addWidget(self.compositionEditBox)
        self.qLineImmDict[self.compositionEditBox] = 'Composition'
        subvbox.addLayout(subhbox)
 
        subhbox = QHBoxLayout()
        label = QLabel('输入串显示为：', self)
        subhbox.addWidget(label)
        self.compDisplayEditBox = QLineEdit(self)
        self.compDisplayEditBox.setReadOnly(True)
        subhbox.addWidget(self.compDisplayEditBox)
        subvbox.addLayout(subhbox)  # 行---------------------
        self.qLineImmDict[self.compDisplayEditBox] = 'CompDisplay'
        hbox.addLayout(subvbox)

        subvbox = QVBoxLayout()
        label = QLabel('候选串', self)
        subvbox.addWidget(label)
        self.candList = QListWidget(self)
        subvbox.addWidget(self.candList)
        hbox.addLayout(subvbox)
        vbox.addLayout(hbox)

        hbox = QHBoxLayout()
        label = QLabel('在此输入：', self)
        hbox.addWidget(label)
        self.editorBox = QLineEdit4Ime(self.getIMM(), self)
        hbox.addWidget(self.editorBox)
        vbox.addLayout(hbox)  # 行---------------------

        vbox.addStretch(1)
        self.setLayout(vbox)

        self.show()

    def ImeKeyPressEvent(self):
        for k, v in self.qLineImmDict.items():
            if type(self.getIMM().GetCoreData(v)) == 'str':
                k.setText(self.getIMM().GetCoreData(v))
            else:
                k.setText(str(self.getIMM().GetCoreData(v)))
        self.candList.clear()
        for i in self.getIMM().GetCoreData('Candidates'):
            self.candList.addItem(i)

if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat,
                        datefmt='%H:%M',)
    app = QApplication(sys.argv)

    inputMethodManager = imm.InputMethodManager.GetInstance()
    inputMethodManager.Initialize()
    imePanel = ImePanel(inputMethodManager)

    sys.exit(app.exec_())

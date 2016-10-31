# -*- coding:utf-8 -*-
import logging
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, \
QLineEdit, QLabel

class ImePanel(QWidget):
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.resize(800, 600)
		vbox = QVBoxLayout()

		hbox = QHBoxLayout()
		label = QLabel('当前状态：', self)
		hbox.addWidget(label)
		self.stateNameEditBox = QLineEdit(self)
		self.stateNameEditBox.setReadOnly(True)
		hbox.addWidget(self.stateNameEditBox)
		hbox.setStretchFactor(self.stateNameEditBox, 2)

		label = QLabel('光标位置：', self)
		hbox.addWidget(label)
		self.cursorPosEditBox = QLineEdit(self)
		self.cursorPosEditBox.setReadOnly(True)
		self.cursorPosEditBox.resize(100, 30)
		hbox.addWidget(self.cursorPosEditBox)
		hbox.setStretchFactor(self.cursorPosEditBox, 1)

		label = QLabel('上屏串：', self)
		hbox.addWidget(label)
		self.selectedEditBox = QLineEdit(self)
		self.selectedEditBox.setReadOnly(True)
		hbox.addWidget(self.selectedEditBox)
		hbox.setStretchFactor(self.selectedEditBox, 3)
		vbox.addLayout(hbox)  # 行---------------------

		hbox = QHBoxLayout()
		label = QLabel('输入串：', self)
		hbox.addWidget(label)
		self.compositionEditBox = QLineEdit(self)
		self.compositionEditBox.setReadOnly(True)
		hbox.addWidget(self.compositionEditBox)

		label = QLabel('输入串显示为：', self)
		hbox.addWidget(label)
		self.compDisplayEditBox = QLineEdit(self)
		self.compDisplayEditBox.setReadOnly(True)
		hbox.addWidget(self.compDisplayEditBox)
		vbox.addLayout(hbox)  # 行---------------------

		hbox = QHBoxLayout()
		label = QLabel('在此输入：', self)
		hbox.addWidget(label)
		self.editorBox = QLineEdit(self)
		hbox.addWidget(self.editorBox)
		vbox.addLayout(hbox)  # 行---------------------

		vbox.addStretch(1)
		self.setLayout(vbox)

		self.show()


if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)
    app = QApplication(sys.argv)
    
    imePanel = ImePanel()

    sys.exit(app.exec_())

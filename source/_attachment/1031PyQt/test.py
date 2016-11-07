# -*- coding:utf-8 -*-
import logging
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, \
QLineEdit, QLabel, QPushButton

class MainWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.resize(400, 200)
		vbox = QVBoxLayout()

		# 第一行
		hbox = QHBoxLayout()
		label = QLabel('姓名：', self)
		hbox.addWidget(label)
		editBox = QLineEdit(self)
		hbox.addWidget(editBox)
		hbox.setStretchFactor(editBox, 2) # 设定三个控件横向拉伸比例为2:1:5

		label = QLabel('年龄：', self)
		hbox.addWidget(label)
		editBox = QLineEdit(self)
		hbox.addWidget(editBox)
		hbox.setStretchFactor(editBox, 1)

		label = QLabel('家庭住址：', self)
		hbox.addWidget(label)
		editBox = QLineEdit(self)
		hbox.addWidget(editBox)
		hbox.setStretchFactor(editBox, 5)
		vbox.addLayout(hbox)

		# 第二行
		hbox = QHBoxLayout()
		label = QLabel('电话：', self)
		hbox.addWidget(label)  # label按需分配，如果没有指定比例，QLineEdit平均分配
		editBox = QLineEdit(self)
		hbox.addWidget(editBox)

		label = QLabel('邮箱：', self)
		hbox.addWidget(label)
		editBox = QLineEdit(self)
		hbox.addWidget(editBox)
		vbox.addLayout(hbox)

		# 第三行	
		hbox = QHBoxLayout()
		label = QLabel('身份证号：', self)
		hbox.addWidget(label)
		editBox = QLineEdit(self)
		hbox.addWidget(editBox)
		vbox.addLayout(hbox)

		# 第四行
		hbox = QHBoxLayout()
		hbox.addStretch(2)        # 设定两个按钮的横向布局为 2 : 确定 : 取消 : 1
		btn = QPushButton('确定')
		hbox.addWidget(btn)

		btn = QPushButton('取消')
		hbox.addWidget(btn)
		hbox.addStretch(1)
		vbox.addLayout(hbox)

		vbox.addStretch(1)
		self.setLayout(vbox)

		self.show()

if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)
    app = QApplication(sys.argv)
    mainWidget = MainWidget()

    sys.exit(app.exec_())
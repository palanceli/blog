# -*- coding: utf8 -*-
#
import 	os
import 	logging
import	sys
import	optparse
import	datetime
import	time
import	argparse

'''
文件data中是du出来的结果，命令为：
$ du -ack /data/app/com.sohu.inputmethod.sogou-1
$ du -ack /data/app/com.baidu.input-1
$ du -ack /data/app/com.iflytek.inputmethod-1
$ du -ack /data/data/com.sohu.inputmethod.sogou
$ du -ack /data/data/com.baidu.input
$ du -ack /data/data/com.iflytek.inputmethod
格式为：path	Size(Kb)，如：
/data/data/com.baidu.input	6240 
/data/data/com.baidu.input/databases	180 
/data/data/com.baidu.input/databases/clipborad_records.db-journal	20 
/data/data/com.baidu.input/databases/clipborad_records.db	36 
'''
rootTypes = ('/data/data', '/data/app')
apkTypes = ('com.baidu.input', 'com.iflytek.inputmethod', 'com.sohu.inputmethod.sogou')

class FolderSize(object):
	def __init__(self, rootIdx, apkIdx, depth):
		self.dataPath = 'data'
		self.rootIdx = rootIdx
		self.apkIdx = apkIdx
		self.depth = depth

	def MainProc(self):
		with open(self.dataPath) as f:
			for line in f:
				size, path = line.strip().split()
				pathItems = path.split('/')

				if self.rootIdx != None:
					if not '/'.join(pathItems[:3]).startswith(rootTypes[self.rootIdx]):
						continue

				if self.apkIdx != None:
					if not pathItems[3].startswith(apkTypes[self.apkIdx]):
						continue

				if len(pathItems) == self.depth + 4:
					logging.debug('%-8s %s' % (size, '/'.join(pathItems)))

if __name__ == '__main__':
	loggingFormat	=	'%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
	logging.basicConfig(level=logging.DEBUG,	format=loggingFormat,	datefmt='%H:%M',	)
	parser = argparse.ArgumentParser(description='根据adb du 出来的数据完成各种统计')
	# parser.add_argument('folder', metavar='folder', nargs=1, help='要计算的文件夹')
	parser.add_argument('-r', '--root', type=int, help='''
		root：
		0:%s*
		1:%s*
		''' % rootTypes)
	parser.add_argument('-a', '--apk', type=int, help='''
		apk:
		0:%s*
		1:%s*
		2:%s*
		''' % apkTypes)
	parser.add_argument('-d', '--depth', type=int, help='要统计的路径深度')
	args = parser.parse_args()

	folderSize = FolderSize(args.root, args.apk, args.depth)
	folderSize.MainProc()

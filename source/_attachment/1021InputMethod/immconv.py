# -*- coding:utf-8 -*-
import immdata
import logging

class HzMap(object):
    ''' 汉字表 '''
    def __init__(self):
        self.filePath = 'hz_py.txt'
        self.aHz = {}
        self.loadFromTxt()

    def GetData(self):
        return self.aHz

    def loadFromTxt(self):
        cnt = 0
        with open(self.filePath) as f:
            for line in f:
                line = line.strip('\r\n')
                if len(line) == 0:
                    continue
                if line.isdigit():
                    continue
                line = line#.decode('utf-8')
                hz = line[0]
                py = line[1:]
                #if not self.aHz.has_key(py):
                if not py in self.aHz:
                    self.aHz[py] = [hz, ]
                else:
                    self.aHz[py].append(hz)

class PyMap(object):
    ''' 拼音表 '''
    def __init__(self):
        self.filePath = 'pinyin_list.txt'
        self.aPyStr = []
        self.loadFromTxt()
            
    def loadFromTxt(self):
        f = open(self.filePath)      
        for line in f:
            line = line.strip('\r\n')
            if len(line) == 0:
                continue
            if line.isdigit():
                continue
            if line.isupper():
                continue
            self.aPyStr.append(line)    
        f.close()
                
class PyNetMaker(object):
    def __init__(self):
        self.pyMap = PyMap()
        
    def findValidSyllable(self, str):
        if len(str) == 0:
            return []
        idxList = []
        hit = False
        for syllable in self.pyMap.aPyStr:
            if not hit:
                if syllable[0] == str[0]:
                    hit = True
            else:
                if syllable[0] != str[0]:
                    return idxList
            if str.startswith(syllable):
                idxList.append(self.pyMap.aPyStr.index(syllable))
        return idxList                  
        
    def preProcess(self, inputStr):
        seg = {}    # {..., n:[an, bn, cn...], ...} inputStr第n个字符开头能匹配到的所有音节串
        length = len(inputStr)
        for i in range(length):
            idxList = self.findValidSyllable(inputStr[i : ])
            seg[i] = [(len(self.pyMap.aPyStr[idx]) - 1) for idx in idxList]
        return seg
        
    def PrintSeg(self, seg):
        for k, v in seg.items():
            msg = 'x%d - ' % k
            for l in v:
                msg += '%d = %d, ' % (v.index(l), l)
            logging.debug(msg)
        
    def getPyNetString(self, inputStr, pyNet, seg):
        str = ''
        for i, j in pyNet:
            str += inputStr[i : i + seg[i][j] + 1]
            str += "'"
        return str
        
    def Proc(self, inputStr):
        seg = self.preProcess(inputStr)

        # i是第几个字符，j是该字符的第几条弧，pyNet是[(位置,弧长), ...]的序列
        i = 0
        j = 0
        pyNet = []
        result = []
        while True:
            if (i in seg) and (j < len(seg[i])):
                pyNet.append((i, j))
                i = i + seg[i][j] + 1
                j = 0
                if i == len(inputStr):
                    result.append(self.getPyNetString(inputStr, pyNet, seg))
            else:
                if i == 0:
                    return result
                i, j = pyNet.pop()
                j += 1
        return result

def combination(arr):
    ''' arr = [a0, a1, ..., an]返回[[ij0, ij1, ..., ijn], ]其中jx∈[0, ax), x∈[0, n]
    '''
    if arr == None or len(arr) == 0:
        return None
    result = []
    cArr = len(arr)

    if cArr == 1:
        for i in range(arr[0]):
            result.append([i, ])
    else:
        for i in range(arr[0]):
            subResult = combination(arr[1 : ])
            [j.insert(0, i) for j in subResult]
            result.extend(subResult)
    return result
    
class IMMConvertor(object):
    selfObj = None

    @staticmethod
    def GetInstance(immData):
        if IMMConvertor.selfObj == None:
            IMMConvertor.selfObj = IMMConvertor(immData)
        return IMMConvertor.selfObj

    def __init__(self, immData):
        self.immData = immData
        self.hzMap = HzMap()
        self.pyNetMaker = PyNetMaker()

    def ConvertPinyin(self, composition):
        return self.pyNetMaker.Proc(composition)

    def convertPinyinArray(self, compArray): # compArray = ['ni', 'hao']
        candidates = []
        cHans = [] # [Cni, Chao] 每一个拼音下面有多少汉字

        for py in compArray:
            cHans.append(len(self.hzMap.GetData()[py]))

        candIndex = combination(cHans) # [[iHZni, iHZhao], ] 每个拼音对应汉字的序号

        for i in candIndex: # i = [iHZni, iHZhao]
            candString = ''
            k = 0
            for j in i:
                py = compArray[k]
                candString += self.hzMap.GetData()[py][j]
                k += 1
            candidates.append(candString)
        return candidates            
                
    def ConvertPinyin2(self, composition):
        pinyinSegs = self.pyNetMaker.Proc(composition)
        if len(pinyinSegs) == 0:
            return (composition, [])
        pinyinArray = pinyinSegs[0].strip("'").split("'") # ['ni', 'hao']
        return (pinyinArray, self.convertPinyinArray(pinyinArray))

def tc01():
    hzMap = HzMap()
    for k, v in hzMap.aHz.items():
        msg = '%8s:' % k
        for i in v:
            msg += '%s ' % i
        logging.debug(msg)

def tc02():
    r = combination([3, 2, 2])
    logging.debug(r)

def tc03():
    immData = immdata.IMMData()
    immConvertor = IMMConvertor.GetInstance(immData)
    pinyinArray, candidates = immConvertor.ConvertPinyin2('ni')
    for cand in candidates:
        logging.debug('%s:%s' % (pinyinArray, cand))
        
if __name__ == '__main__':
    loggingFormat = '%(asctime)s %(lineno)04d %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=loggingFormat, datefmt='%H:%M',)
    
    tc03()

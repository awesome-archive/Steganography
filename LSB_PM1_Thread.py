#coding:utf-8

__author__ = 'g9752'

#import wx
#import PIL
#import Image
#import numpy as np
#import matplotlib.pyplot as plt
import struct
from PIL import Image
from wx.lib.pubsub import pub as Publisher
import threading
import random
import time

class LSB_PM1_Thread(threading.Thread):
    def __init__(self,src,dst,tofile):
        threading.Thread.__init__(self)
        self.src = src
        self.dst = dst
        self.tofile = tofile
        pass

    def run(self):
        starttime = time.clock()
        self.Encrypt(self.src,self.dst,self.tofile)
        endtime = time.clock()
        print "encrypt use time:", endtime-starttime
        pass

    def byte2list(self,byte):
        """
        将一个byte值转换成长度为8的字符列表，列表元素类型为 char
        :param byte: byte值
        :return: 长度为8的列表
        """

        byte = struct.unpack("B",byte)
        byte_b = bin(byte[0])          # 转成二进制
        byte_l = list(byte_b)       # 转成列表
        byte_l = byte_l[2:]         # 列表切片修饰
        while len(byte_l) < 8:      # 列表填充
            byte_l.insert(0,'0')
        return byte_l

    def dstfile2list(self,filename):
        """
        将文件转换成0,1的字节串的列表
        :param filename: 源文件名
        :return: 由文件二进制值组成的列表
        """
        fp = open(filename,'rb')
        bitlist = []
        byte = fp.read(1)
        while byte != "":
            bitlist += self.byte2list(byte)
            byte = fp.read(1)
        fp.close()
        return bitlist

    def AppendEndFlag(self,bitlist,flag="LSB"):
        """
        向bitlist中追加结束标志
        :param bitlist: 原bit列表
        :param flag: 默认结束标志 "LSB"
        :return: 添加结束标志后的 bit列表
        """
        for i in range(len(flag)):
            #byte = struct.unpack("b",flag[i])
            bitlist += self.byte2list(flag[i])
        return bitlist


    def Encrypt(self,src,dst,tofile,flag=None):
        """
        注释
        :param src:
        :param dst:
        :param tofile:
        :param flag:
        :return:
        """

        bitlist = self.dstfile2list(dst)
        bitlist = self.AppendEndFlag(bitlist)    #向字节列表中追加结束标志
        print 'bitlist length:',len(bitlist)

        ibitlist = 0
        try:
            im = Image.open(src)
            rgb_im = im.convert("RGB")
            width,height = im.size
            total = width * height
            for i in range(0,width):
                for j in range(0,height):
                    r,g,b = rgb_im.getpixel((i,j))
                    r1,g1,b1 = r,g,b
                    """
                    添加加密过程
                    """
                    # R
                    if ibitlist < len(bitlist):
                        ele = bitlist[ibitlist]
                        if ele == '0' and r % 2 == 1:
                            r1 = r + random.choice((-1,1))
                        if ele == '1' and r % 2 == 0:
                            r1 = r + random.choice((-1,1))
                        if r1 > 254:
                            r1 = r1 - 2
                        if r1 < 0 :
                            r1 = r1 + 2
                        ibitlist += 1
                    # G
                    if ibitlist < len(bitlist):
                        ele = bitlist[ibitlist]
                        if ele == '0' and g % 2 == 1:
                            g1 = g + random.choice((-1,1))
                        if ele == '1' and g % 2 == 0:
                            g1 = g + random.choice((-1,1))
                        if g1 > 254:
                            g1 = g1 - 2
                        if g1 < 0:
                            g1 = g1 + 2
                        ibitlist += 1
                    # B
                    if ibitlist < len(bitlist):
                        ele = bitlist[ibitlist]
                        if ele == '0' and b % 2 == 1:
                            b1 = b + random.choice((-1,1))
                        if ele == '1' and b % 2 == 0:
                            b1 = b + random.choice((-1,1))
                        if b1 > 254:
                            b1 = b1 - 2
                        if b1 < 0:
                            b1 = b1 + 2
                        ibitlist += 1
                    rgb_im.putpixel((i,j),(r1,g1,b1))
                    #print (i,j),(r,g,b),(r1,g1,b1)
                    """
                    提前完成加密操作
                    """
                    if ibitlist >= len(bitlist):
                        rgb_im.save(tofile)
                        Publisher.sendMessage("updateGauge_pm1",message=100)
                        return (True,u"成功完成LSB算法")
                    """
                    回送进度消息
                    """
                    process = (i) * height + j
                    process = process * 100 / total
                    Publisher.sendMessage("updateGauge_pm1",message=process)

            rgb_im.save(tofile)
            Publisher.sendMessage("updateGauge_pm1",message=100)
            pass

        finally:
            pass
        return (True,u"成功完成LSB算法")

class DeLSB_Thread(threading.Thread):
    def __init__(self,src,tofile):
        threading.Thread.__init__(self)
        self.src = src
        self.tofile = tofile

    def run(self):
        starttime = time.clock()
        self.Decrypt(self.src,self.tofile)
        endtime = time.clock()
        print "decrypt use time:", endtime-starttime
        pass

    def list2byte(self,lb):
        """
        将长度为8的bit列表转换成一个byte
        :param lb: 长度为8的bit列表
        :return: 根据列表转成的byte
        """
        try:
            byte = 0
            for i in range(len(lb)):
                if lb[i] == 1:
                    byte = byte << 1
                    byte = byte | 1
                if lb[i] == 0:
                    byte = byte << 1
            byte = struct.pack('B',byte)
            return byte
        except Exception:
            print lb

    def byte2list(self,byte):
        """
        将一个byte值转换成长度为8的字符列表，列表元素类型为 char
        :param byte: byte值
        :return: 长度为8的列表
        """

        byte = struct.unpack("B",byte)
        byte_b = bin(byte[0])          # 转成二进制
        byte_l = list(byte_b)       # 转成列表
        byte_l = byte_l[2:]         # 列表切片修饰
        while len(byte_l) < 8:      # 列表填充
            byte_l.insert(0,'0')
        return byte_l

    def Decrypt(self,src,tofile):
        """
        注释
        :param src:
        :param tofile:
        :return:
        """
        tofile = open(tofile,"wb")
        bytelist = []
        im = Image.open(src)
        rgb_im = im.convert("RGB")
        width,height = rgb_im.size
        for i in range(width):
            for j in range(height):
                r,g,b = rgb_im.getpixel((i,j))
                """
                添加解密过程：从像素信息中提取隐写数据加入到bypelist中
                """
                #r
                if r % 2 == 0:  #R的最低位为0
                    bytelist.append(0)
                if r % 2 == 1:  #R的最低位为1
                    bytelist.append(1)

                #g
                if g % 2 == 0:  #G的最低位为0
                    bytelist.append(0)
                if g % 2 == 1:  #G的最低位为1
                    bytelist.append(1)

                #r
                if b % 2 == 0:  #B的最低位为0
                    bytelist.append(0)
                if b % 2 == 1:  #B的最低位为1
                    bytelist.append(1)

                """
                回送进度消息
                """
                process = (i) * height + j
                process = process * 50 / (width * height)
                Publisher.sendMessage("updateGauge_pm1",message=process)
        print 'bitlist length: ',len(bytelist)
        len_list = len(bytelist)
        """
        获取flag的bit列表
        """
        flag = "LSB"
        flag_l = []
        for i in range(len(flag)):
            flag_l += self.byte2list(flag[i])
        flag_l = map(int,flag_l)

        while len(bytelist) != 0:
            tmp = []
            for t in range(8):
                tmp.append(bytelist.pop(0))

            """
            回送进度消息
            """
            process = ((len_list - len(bytelist)) * 50 / len_list) + 50
            Publisher.sendMessage("updateGauge_pm1",message=process)

            byte = self.list2byte(tmp)
            if byte == "L":
                for j in range(8,len(flag_l)):
                    if flag_l[j] != bytelist[j-8]:
                        break
                else:
                    Publisher.sendMessage("updateGauge_pm1",message=101)
                    tofile.close()
                    return (True,u"成功从图片中提取到隐写信息")

            tofile.write(byte)
            tofile.flush()
        tofile.close()
        return (True,u"成功从图片中提取到隐写信息")
        pass

if __name__ == "__main__":
    pass
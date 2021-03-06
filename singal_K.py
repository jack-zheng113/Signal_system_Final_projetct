import matplotlib.pyplot as plt
import numpy as np
import time
import time, random
import math
import serial
from collections import deque
from scipy.io import loadmat
from scipy import signal

# 第K組

class PlotData:
    def __init__(self, max_entries=30):
        self.axis_x = deque(maxlen=max_entries)
        self.axis_y = deque(maxlen=max_entries)
        self.axis_yac = deque(maxlen=max_entries)
        
        self.axis_yac_filter =deque(maxlen=max_entries)

        self.max1   = 0 #第一個頂峰大小
        self.time1  = 0 #第一個頂峰時間
        self.max2   = 0 #第二個頂峰大小
        self.time2  = 0 #第二個頂峰時間
        self.count1 = 0 #未刷新第一個頂峰的次數
        self.count2 = 0 #未刷新第二個頂峰的次數
        self.state  = 0 #抓取最大值數量(狀態)
        self.fre    = 0 #頻率(即時心律)
        self.total_fre   = 0 #加總頻率
        self.amount_fre  = 0 #抓取頻率的次數
        self.average_fre = 0 #平均的心律
        
    def add(self, x, y):
        self.axis_x.append(x)
        # self.axis_y.append(y)
        self.axis_yac.append(y-np.mean(self.axis_y))    #去除平均值(得AC成分)
        #十點平均率波
        self.axis_yac_filter = signal.lfilter([1/10,1/10,1/10,1/10,1/10,1/10,1/10,1/10,1/10,1/10],1,self.axis_yac)
       
    #計算心率的副程式   
    def f(self,value):       
        if(self.state == 0):                                #還沒抓任何值
            if(self.max1  <value):                          #開始抓第一個最大值
                self.max1 = value                           #把大小值丟入max1
                self.time1 = time.time()                    #抓取刷新max1時的時間
            else:                                           #若小於第一個頂峰大小
                self.count1 = self.count1+1                 #增加一次未刷新最大值紀錄
                if(self.count1 > 50):                       #若超過20次都沒刷新max1,那max1就定下來了
                    self.state = 1                          #表示抓到第一個頂峰的時間
                    self.count1 = 0                         #歸零未刷新最大值的紀錄
                    self.max1= 0                            #歸零第一個峰值
        if(self.state ==1):                                 #進入抓第二最大值
            if(self.max2 < value):                          #開始抓第二個最大值
                self.max2 = value                           #把大小值丟入max2
                self.time2 = time.time()                    #抓取刷新max2時的時間
            else:                                           #若小於第二個頂峰大小
                self.count2 =self.count2 + 1                #增加一次未刷新最大值紀錄
                if(self.count2 >50):                        #若超過20次都沒刷新max2,那max1就定下來了
                    self.state = 2                          #表示抓到第二個頂峰的時間
                    self.count2 = 0                         #歸零未刷新最大值的紀錄
                    self.max2 =0                            #歸零第二個峰值
        if(self.state ==2):                                 #有兩個頂峰時間就進入這裡
            self.fre = (60/(self.time2-self.time1))         #時間差的倒數 = 心率
            if(self.fre <110 and self.fre >40):             #去除掉過於密集的突波
               print("即時心律 : " , self.fre, "\t下/分鐘")  #印出即時心率
               self.total_fre += self.fre                   #加總心率
               self.amount_fre +=1                          #拿一次頻率就加一次次數
               self.average_fre =self.total_fre / self.amount_fre   #取平均心率
               print("平均心律 : ",self.average_fre, "\t下/分鐘\n")  #印出平均心率
            self.time1 = self.time2                         #把第二個峰頂時間丟到第一個
            self.time2 = 0                                  #歸零第二個頂峰時間
            self.state = 1                                  #回到已經有抓到第一個峰頂，開始抓第二個頂峰的狀態
           
#initial
fig, (ax,ax2,ax3) = plt.subplots(3,1)                       #三個圖   

plt.subplots_adjust(hspace=1)                               #調整表格間的高度(hspace)

line,  = ax.plot(np.random.randn(100))              
line2, = ax2.plot(np.random.randn(100))
line3, = ax3.plot(np.random.randn(100))
plt.show(block = False)
plt.setp(line2,color = 'r')              

PData= PlotData(500)
ax.set_ylim(250,450)
ax2.set_ylim(-5,5)                                          #圖表二的Y軸範圍
ax3.set_ylim(-5,5)                                          #圖表三的Y軸範圍

# plot parameters
print ('plotting data...')
# open serial port
strPort='com3'
ser = serial.Serial(strPort, 115200)
ser.flush()

start = time.time()

while True:
    
    for ii in range(10):
        
        try:
            data = float(ser.readline())                    
            PData.add(time.time() - start, data)            #刷新時間
            PData.f(data)                                   #跑心率的function
      
        except:
            pass

    ax.set_xlim(PData.axis_x[0], PData.axis_x[0]+5)             #當前時間到五秒後的時間
    ax2.set_xlim(PData.axis_x[0], PData.axis_x[0]+5)
    ax3.set_xlim(PData.axis_x[0], PData.axis_x[0]+5)    
    
    line.set_xdata(PData.axis_x)
    line.set_ydata(PData.axis_y)                                #原始值
    ax.set_title("Original data",fontsize = 15)                 #設標題
    ax.set_xlabel('time [s]')                                   #設X標題
    ax.set_ylabel(r'Amplitude')                                 #設Y標題
    
    line2.set_xdata(PData.axis_x)
    line2.set_ydata(PData.axis_yac)                             #除去直流位準的波型
    ax2.set_title("AC component ",fontsize =15)                 #設標題
    ax2.set_xlabel('time [s]')                                  #設X標題
    ax2.set_ylabel(r'Amplitude')                                #設Y標題
    
    line3.set_xdata(PData.axis_x)
    line3.set_ydata(PData.axis_yac_filter)                      #經過濾波器的波型
    ax3.set_title("AC component (after filter)",fontsize =15)   #設標題
    ax3.set_xlabel('time [s]')                                  #設X標題
    ax3.set_ylabel(r'Amplitude')                                #設Y標題

    fig.canvas.draw()
    fig.canvas.flush_events()
    
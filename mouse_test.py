import os,time
import pyautogui as pag

arr = []
num = 0
try:
    while num <= 5:
            print("Press Ctrl-C to end")
            x,y = pag.position() #返回鼠标的坐标
            posStr="Position:"+str(x).rjust(4)+','+str(y).rjust(4)
            print (posStr)#打印坐标
            time.sleep(0.1)
            num += 0.1
            arr.append({'x':x,"y":y})
            os.system('cls')#清楚屏幕

    print(arr)
except  KeyboardInterrupt:
    print ('end....')
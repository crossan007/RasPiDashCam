#!/usr/bin/python

# references: 
# https://github.com/Zulko/moviepy/blob/master/moviepy/video/io/ffmpeg_reader.py
# https://github.com/Zulko/moviepy/blob/master/moviepy/video/io/ffmpeg_writer.py
# https://libav.org/avconv.html#Pixel-Format
# http://stackoverflow.com/questions/18962785/oserror-errno-2-no-such-file-or-directory-while-using-python-subprocess-in-dj
# http://learnpythonthehardway.org/book/ex5.html
# http://stackoverflow.com/questions/14759637/python-pil-bytes-to-image
# http://zulko.github.io/blog/2013/09/27/read-and-write-video-frames-in-python-using-ffmpeg/


import subprocess as sp
import numpy
import os 
import shlex
import signal
import time
import gc
import datetime
import sys
import PIL
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import threading
import Queue
import syslog

date = " "
temp = " "
exitFlag = 0

q = Queue.Queue()


def updateVars():
    global date
    global temp
    global exitFlag
    print("Starting update vars")
    while not exitFlag:
        ts = time.time()
        date = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d-%H%M%S')
        temp = sp.Popen(["/opt/vc/bin/vcgencmd", "measure_temp"], stdout=sp.PIPE).communicate()[0]
        ts = time.time()
        time.sleep(1)
    print("Stopping update vars ")


def getFrames():
    global temp
    global exitFlag
    i=0
    w = 640
    h = 480
    nbytes = 3*w*h
    tempimg = ""
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",14)
    command = "/usr/bin/avconv -f video4linux2 -r 15 -input_format yuyv422 -video_size 640x480 -i /dev/video0 -f rawvideo -pix_fmt rgb24 pipe: "
    inputPipeline = sp.Popen(shlex.split(command), stdout = sp.PIPE,stderr=DEVNULL)
    while not exitFlag:
        buf=0
        tempimg = ""
        while buf<10:
            if i % 100 == 0:
                print( "Starting processing frame %d" %i)
            try:
                raw_image = inputPipeline.stdout.read(nbytes)
            except IOError as err:
                    ffmpeg_error = inputPipeline.stderr.read()
                    print (ffmpeg_error) 
            except: # catch *all* exceptions
                e = sys.exc_info()[0]
                print("Error: %s" % e )
            if len(raw_image) != nbytes:
                print("Warning, not reading right # byes, %d, %d" % ( len(raw_image), nbytes) )
            if i % 100 == 0:
                print("Manipulating frame %d" %i)
        
            img = Image.frombuffer('RGB', (640,480), raw_image, 'raw', 'RGB', 0, 1)
            draw=ImageDraw.Draw(img)
            draw.text((0, 460), temp ,(255,255,0),font=font)
            draw.text((160, 460), date ,(255,255,0),font=font)
            draw.text((580, 460), str(i) ,(255,255,0),font=font)
            draw = ImageDraw.Draw(img)
            tempimg+=img.tostring()
            del img
            del draw
            del raw_image
            gc.collect()
            i+=1
            buf+=1
        q.put(tempimg)
        
def putFrames():
    global exitFlag
    i=0
    command2 = "/usr/bin/avconv -f rawvideo -pix_fmt rgb24 -video_size 640x480 -r 15 -i pipe: -vf \"setpts=0.1*PTS\" -c:v libx264 -preset ultrafast -tune film -map 0 -f flv -f segment -segment_time 90 -r 90 \"vid-"+date+"-%03d.flv\""
    outputPipeline = sp.Popen(shlex.split(command2), stdout = DEVNULL, stderr = DEVNULL, stdin = sp.PIPE )
    while not exitFlag:
        img=q.get()
        if i % 10 == 0:
            print( "Starting push frame %d" %i)
        try:
            outputPipeline.stdin.write(img)
        except IOError as err:
            ffmpeg_error = outputPipeline.stderr.read()
            print(ffmpeg_error)
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            print("Error: %s" % e )
            ffmpeg_error = outputPipeline.stdout.read()
            print(ffmpeg_error)
        if i % 10 == 0:
            print( "Done with frame %d" %i)
        i+=1
    
    
try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

os.system("pkill avconv");


ts = time.time()
date = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d-%H%M%S')


#



thread = threading.Thread(target=getFrames)
thread.daemon = True
thread.start()

thread2 = threading.Thread(target=putFrames)
thread2.daemon = True
thread2.start()

thread3 = threading.Thread(target=updateVars)
thread3.daemon = True
thread3.start()

while True:
    time.sleep(10)
    print("vc.py still alive ")
    print("queue size: %d" % q.qsize())
    
exitFlag=1
inputPipeline.kill()
outputPipeline.kill()
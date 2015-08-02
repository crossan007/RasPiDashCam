#!/usr/bin/env python
#Test Script 


import av
import subprocess as sp
import time
import gc
import datetime
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import threading
import Queue
import syslog
import logging


logging.basicConfig(level=logging.INFO)
#av.logging.set_level(logging.INFO)

date = " "
temp = " "
exitFlag = 0
frameCount =0

q = Queue.Queue()

def updateVars():
        global date
        global temp
        print("Starting")
        while not exitFlag:
            ts = time.time()
            date = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d-%H%M%S')
            temp = sp.Popen(["/opt/vc/bin/vcgencmd", "measure_temp"], stdout=sp.PIPE).communicate()[0]
            ts = time.time()
            time.sleep(1)
        print("Stopping")
        
def readFrames():
    container = av.open(format="video4linux2",file='/dev/video0')
    video = next(s for s in container.streams if s.type == b'video')

    for packet in container.demux(video):
        for frame in packet.decode():
            #frame.to_image().save('frame-%04d.jpg' % frame.index)
            q.put(frame.to_image())
            
def writeFrames():
    global frameCount
    output = av.open(file='temp4.flv', mode='w')
    stream = output.add_stream("libx264", 15)
    stream.bit_rate = 8000000
    stream.pix_fmt = "yuv420p"
    stream.width = 640
    stream.height = 480
    print "stream is a: %s" % type(stream)
    while not exitFlag:
        temp=av.VideoFrame.from_image(q.get())
        #temp=temp.reformat(format="yuv420p")
        #print "Frame: %s" % temp
        packet = stream.encode(temp)
        #print "packet: %s" % packet
        if (type(packet) == "av.packet.Packet"):
            print "Found a packet, Muxing."
            output.mux(packet) 
       # else:
            #print "Not a packet. Not counting"
        frameCount +=1
        
    packet = stream.encode() 
    output.mux(packet)
    output.close()
        
    
        

thread = threading.Thread(target=updateVars)
thread.daemon = True
thread.start()


thread2 = threading.Thread(target=readFrames)
thread2.daemon = True
thread2.start()

thread3 = threading.Thread(target=writeFrames)
thread3.daemon = True
thread3.start()


a=0
while not exitFlag:
    diff=q.qsize()-a
    print "Frames since last: %d Frames Total: %d" % (diff,frameCount)
    
    a=q.qsize()
    time.sleep(1)
    if frameCount > 100:
        exitFlag = True
        




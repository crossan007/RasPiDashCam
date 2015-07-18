#!/usr/bin/python
import subprocess as sp
import numpy
import os 
import shlex
import signal
import time
import PIL
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

os.system("pkill avconv");
os.system("rm out*");
command = "/usr/bin/avconv -f video4linux2 -r 15 -input_format yuyv422 -video_size 640x480 -i /dev/video0 -f rawvideo -pix_fmt rgb24 pipe: "
pipe = sp.Popen(shlex.split(command), stdout = sp.PIPE, stderr = DEVNULL, stdin = DEVNULL )


command2 = "/usr/bin/avconv -f rawvideo -pix_fmt rgb24 -video_size 640x480 -r 15 -i pipe: -vf \"setpts=0.1*PTS\" -c:v libx264 -preset ultrafast -tune film -map 0 -f flv -r 90 out.flv"
pipe2 = sp.Popen(shlex.split(command2), stdout = sp.PIPE, stderr = sp.PIPE, stdin = sp.PIPE )

w = 640
h = 480
nbytes = 3*w*h
i=0
while True:
    raw_image = pipe.stdout.read(nbytes)
    #print "%s" % raw_image
    if len(raw_image) != nbytes:
        print "Warning, not reading right # byes, %d, %d" % ( len(raw_image), nbytes) 
    #print "Read %d bytes" % len(raw_image)
    # transform the byte read into a numpy array
    img = Image.frombuffer('RGB', (640,480), raw_image, 'raw', 'RGB', 0, 1)
    draw=ImageDraw.Draw(img)
    font = ImageFont.truetype("/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Bold.ttf",14)

    temp = sp.Popen(["/opt/vc/bin/vcgencmd", "measure_temp"], stdout=sp.PIPE).communicate()[0]

    draw.text((0, 460), temp ,(255,255,0),font=font)
    draw.text((580, 460), str(i) ,(255,255,0),font=font)

    draw = ImageDraw.Draw(img)
   # img.save("a_test.jpg")
    #print "%s" % img.tostring()
    try:
        pipe2.stdin.write(img.tostring())
    except IOError as err:
            ffmpeg_error = pipe2.stderr.read()

            print "%s" % ffmpeg_error
    i+=1
pipe.kill()
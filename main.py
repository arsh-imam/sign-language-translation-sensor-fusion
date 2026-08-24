import cv2
import time
import collections
import numpy as np
import imu_reader
import vision
import gesture_analyzer
import audio_sender

WORD_COOLDOWN     = 2.5
WORD_FLASH_DUR    = 1.5
CONFIRM_FRAMES    = 3
GRAPH_LEN         = 80
SHAPE_MEMORY_SEC  = 0.6

graph_ax = collections.deque([0.0] * GRAPH_LEN, maxlen=GRAPH_LEN)
graph_ay = collections.deque([0.0] * GRAPH_LEN, maxlen=GRAPH_LEN)
graph_az = collections.deque([0.0] * GRAPH_LEN, maxlen=GRAPH_LEN)

last_word_time    = 0.0
last_word         = ''
word_flash_until  = 0.0
consecutive_word  = ''
consecutive_count = 0
last_good_shape   = 'NONE'
last_good_shape_t = 0.0

def draw_hud(frame, shape, motion, word, snapshot):
    global graph_ax, graph_ay, graph_az
    h, w = frame.shape[:2]
    if snapshot:
        latest = snapshot[-1]
        graph_ax.append(latest[1])
        graph_ay.append(latest[2])
        graph_az.append(latest[3])
    overlay = frame.copy()
    cv2.rectangle(overlay, (10,10), (280,160), (20,20,20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    shape_color = {'INDEX':(0,255,255),'PALM':(255,200,0),'THUMB':(0,255,0),'PEACE':(255,0,200),'NONE':(100,100,100)}.get(shape,(200,200,200))
    cv2.putText(frame,'Shape:  '+shape,(20,45),cv2.FONT_HERSHEY_SIMPLEX,0.7,shape_color,2)
    mc = (100,100,255) if motion != 'STILL' else (150,150,150)
    cv2.putText(frame,'Motion: '+motion,(20,80),cv2.FONT_HERSHEY_SIMPLEX,0.7,mc,2)
    cv2.putText(frame,'Word:   '+word,(20,115),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)
    gx1,gy1,gx2,gy2 = w-220,10,w-10,160
    gw = gx2-gx1
    gh = gy2-gy1
    ov2 = frame.copy()
    cv2.rectangle(ov2,(gx1,gy1),(gx2,gy2),(20,20,20),-1)
    cv2.addWeighted(ov2,0.6,frame,0.4,0,frame)
    cv2.putText(frame,'Accel (IMU)',(gx1+10,gy1+18),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),2)
    def draw_line(deq,color,label,ly):
        vals=list(deq)
        pts=[]
        for i,v in enumerate(vals):
            px=gx1+int(i*gw/GRAPH_LEN)
            v2=max(-2.0,min(2.0,v))
            py=gy1+int((1-(v2+2.0)/4.0)*gh*0.8+gh*0.1)
            pts.append((px,py))
        for i in range(1,len(pts)):
            cv2.line(frame,pts[i-1],pts[i],color,1)
        if pts:
            cv2.putText(frame,label,(gx2-18,ly),cv2.FONT_HERSHEY_SIMPLEX,0.35,color,1)
    mid_y=gy1+gh//2
    cv2.line(frame,(gx1,mid_y),(gx2,mid_y),(60,60,60),1)
    draw_line(graph_ax,(100,100,255),'X',gy1+40)
    draw_line(graph_ay,(100,255,100),'Y',gy1+80)
    draw_line(graph_az,(255,100,100),'Z',gy1+120)
    if snapshot:
        peak_gy=max(max(abs(s[4]),abs(s[5]),abs(s[6])) for s in snapshot)
        br=min(peak_gy/300.0,1.0)
        bx2=10+int((w-20)*br)
        bc=(0,int(255*(1-br)),int(255*br))
        cv2.rectangle(frame,(10,h-30),(bx2,h-10),bc,-1)
        cv2.rectangle(frame,(10,h-30),(w-10,h-10),(80,80,80),1)
        cv2.putText(frame,'Gyro Intensity',(12,h-33),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),2)
    now=time.time()
    if now < word_flash_until and word:
        alpha=min(1.0,(word_flash_until-now)/0.4)
        fc=(int(255*alpha),int(255*alpha),int(100*alpha))
        ts=cv2.getTextSize(word,cv2.FONT_HERSHEY_DUPLEX,2.5,3)[0]
        tx=(w-ts[0])//2
        ty=(h+ts[1])//2
        cv2.putText(frame,word,(tx+3,ty+3),cv2.FONT_HERSHEY_DUPLEX,2.5,(0,0,0),4)
        cv2.putText(frame,word,(tx,ty),cv2.FONT_HERSHEY_DUPLEX,2.5,fc,3)
    return frame

def main():
    global last_word_time,last_word,word_flash_until
    global consecutive_word,consecutive_count
    global last_good_shape,last_good_shape_t
    print('[MAIN] Starting ISL Fusion System...')
    print('[MAIN] Press Q in the window to quit.')
    imu_reader.start()
    time.sleep(2.5)
    cv2.namedWindow('ISL Fusion',cv2.WINDOW_NORMAL)
    cv2.resizeWindow('ISL Fusion',800,500)
    while True:
        frame,shape  = vision.get_frame_and_shape()
        snapshot     = imu_reader.get_snapshot()
        motion       = gesture_analyzer.analyze(snapshot)
        now          = time.time()
        # Shape memory: if shape is NONE but we had a good shape recently, reuse it
        if shape not in ('NONE','UNKNOWN'):
            last_good_shape   = shape
            last_good_shape_t = now
        elif now - last_good_shape_t < SHAPE_MEMORY_SEC:
            shape = last_good_shape
        candidate = gesture_analyzer.get_word(shape, motion)
        if candidate and candidate == consecutive_word:
            consecutive_count += 1
        else:
            consecutive_word  = candidate if candidate else ''
            consecutive_count = 1
        if (consecutive_count >= CONFIRM_FRAMES
                and candidate
                and now - last_word_time > WORD_COOLDOWN):
            last_word         = candidate
            last_word_time    = now
            word_flash_until  = now + WORD_FLASH_DUR
            consecutive_count = 0
            audio_sender.send_word(candidate)
            print('[FUSION] '+shape+' + '+motion+' => '+candidate)
        frame = draw_hud(frame,shape,motion,last_word,snapshot)
        frame = cv2.resize(frame,(1280,720))
        cv2.imshow('ISL Fusion',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    print('[MAIN] Shutting down...')
    imu_reader.stop()
    vision.release()
    audio_sender.close()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
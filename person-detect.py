#!/usr/bin/env python

# WS server example

import asyncio
import websockets
import sys
import cv2
import json


c = 1

async def hello(websocket, path):
    cap = cv2.VideoCapture('udpsrc port=1338 ! application/x-rtp ! rtpjitterbuffer ! rtph264depay ! decodebin ! video/x-raw,format=I420 ! videoconvert !  appsink',cv2.CAP_GSTREAMER)
    frame_width = int( cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    frame_height =int( cap.get( cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
    
    out = cv2.VideoWriter("output.avi", fourcc, 5.0, (1280,720))

    ret, frame1 = cap.read()
    
    ret, frame2 = cap.read()
    while cap.isOpened():
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        cout = 0
        personList = []
        height, width = frame1.shape[:2]
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)

            if cv2.contourArea(contour) < 900:
                continue
            if(h/w) < 1:
                continue
            personList.append({"x":x+w/2, "y":y+h/2})
            cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame1, "Status: {}".format('Movement'), (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 0, 255), 3)
            cout+=1
        #cv2.drawContours(frame1, contours, -1, (0, 255, 0), 2)
        x = {
            "mh" : height,
            "mw" : width,
            "count" : cout,
            "persons" : personList
        }
        
        y = json.dumps(x)
        if(cout != 0):
            await websocket.send(y)   

        
        image = cv2.resize(frame1, (1280,720))
        out.write(image)
        cv2.imshow("feed", frame1)
        frame1 = frame2
        ret, frame2 = cap.read()


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    cap.release()
    out.release()

if __name__ == "__main__":
    start_server = websockets.serve(hello, "192.168.56.101", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
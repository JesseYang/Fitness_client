import socket
import os
import threading
import numpy as np
import struct
import cv2
import ctypes
from enum import Enum
import sys
from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

# from detect import DetectThread
# from capture import CaptureThread
# from visualize import VisualizeGUI
from audio import AudioThread

import pickle
import time
import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import askquestion
# from fitness import Extractor
from PIL import Image
from PIL import ImageTk
import uuid
import pdb
from GUI.widgets import *

from cfgs.config import cfg

from actions import *

class ClientAccept:
    def __init__(self, host='192.168.1.124', port=8117 ,client_host='192.168.1.108', client_port=8121, video_file=None):
        print(os.getpid())
        self.host = host
        self.port= port
        self.client_host=client_host
        self.client_port=client_port
        self.bufsize = 1024
        self.result_queue = Queue(maxsize=cfg.max_queue_len)
        self.video_file = video_file
        self.s_addr_port = (self.host, self.port)
        # self.init()
        self.img_dic = {}
        self.audio_thread = AudioThread()
        self.audio_thread.start()
        self.action = BackSquat()
        self.socket_client()
        # self.__init_gui() 

    def __init_gui(self):

        self.window = tk.Tk()
        self.window.wm_title('VideoText')
        self.window.config(background = '#FFFFFF')

        self.canvas = ICanvas(self.window, width = cfg.output_width, height = cfg.output_height)
        self.canvas.grid(row = 0, column = 0)

        self.fm_control = tk.Frame(self.window, width=cfg.output_width, height=20, background = 'white')
        self.fm_control.grid(row = 1, column=0, sticky=tk.W, padx=2, pady=5)

        self.lb_status = tk.Text(self.fm_control, height=18,  background = 'white')
        self.lb_status.grid(row = 0, column=2, padx=10, pady=5)
        # self.lb_status.insert(1.0,"因为你在我心中是那么的具体") 
        
        self.fm_status = tk.Frame(self.window, width = 100, height = 100, background = '#FFFFFF')
        self.fm_status.grid(row = 0, column=1, padx=0, pady=2)
  
        self.btn_prev_frame1 = tk.Button(self.fm_status, text='Start', command = self._start)
        self.btn_prev_frame1.grid(row = 0, column=0, padx=10, pady=2)
        
        self.btn_next_frame3 = tk.Button(self.fm_status, text='New', command = None)
        self.btn_next_frame3.grid(row = 1, column=0, padx=10, pady=20)
        self.window.resizable(False, False)
       
    def _start(self):

        client_thread = threading.Thread(target=self.send_to_server)
        client_thread.start()
        # result_thread.start()

        self.receive_data()

    def socket_client(self):

        # client_server = threading.Thread(target=self.receive_data)
        # client_server.start()

    
        self.__init_gui()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

       

    def receive_data(self):
        self.s =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        try:
            self.s.bind((self.client_host,self.client_port))
        except socket.error as e:
            print("Bind failed")
            print(e)
            
        self.s.listen(5)
        print("client server started...")
        print("pid:",os.getpid())

        conn, addr = self.s.accept()
        print("client server  connection from {0}".format(addr))
        idx = 0
        print(os.getpid())
        while True:
            show_time = time.time()
            buf = b""
            while True:
                tem_buf = conn.recv(self.bufsize)
                buf += tem_buf
                if len(tem_buf) != self.bufsize :
                    break
     
            img_id, result_peak = pickle.loads(buf)
            print("receive result time ", str(time.time() - show_time))
            # self.result_queue.put([img_id, result_peak[0]])
            if img_id == -1:
                # self.result_queue.put([addr, -1, 0])
                conn.close()
                break
            print(self.img_dic[img_id][1])
            print("============client server recevied data from server frame_id:%d  pid:%d" % (img_id, os.getpid()))
            tips, text, result_img = self.action.push_new_frame(result_peak[0], cv2.resize(self.img_dic[img_id][0], (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_CUBIC))

            if self.audio_thread.qsize() == 0 and self.audio_thread.is_playing == False:
                for tip in tips:
                    self.audio_thread.put(tip)

            result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
            # print("----------", result_img.shape)
            draw_time = time.time()
            idx+=1
            self.canvas.add(result_img)
            add_time = time.time()
            # cv2.imwrite(os.path.join("test",str(idx)+"_"+str(img_id)+".jpg"), result_img)
            if text != "" and text != None:
                self.lb_status.insert(1.0, '\n')
                self.lb_status.insert(1.0, text)
                self.lb_status.update_idletasks()
            # print(text)
            # self.window.update_idletasks()  #快速重画屏幕  
            self.window.update()

            print("show time ", str(time.time() - show_time), str(draw_time - show_time), str(add_time-draw_time), str(str(time.time()-add_time)))
            # print("-----draw over")
            end_time=time.time()
            print("********************** %d, time: %s, %s , %s " % (img_id, str(end_time-self.img_dic[img_id][1]), str(end_time), str(self.img_dic[img_id][1])))
        print("Client connection interrupted: {0}".format(addr))
        conn.close()
        self.s.close()
        print("{0} closed! ".format(addr))

    def on_closing(self):
        self.server.close()
        self.window.destroy()
        # sys.exit()
        quit()


    ##20180512.mp4
    def send_to_server(self, video_file=None):
        try:
            self.server =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        except Exception as e:
            print("Error create socket")
            sys.exit()
            # quit()

        try:
            # socket.setdefaulttimeout(5)
            self.server.connect(self.s_addr_port)
        except socket.error as e:
            print("Error connecting to server: %s" % e )
            sys.exit()
        except socket.timeout:
            print("connecting to server timeout")
            sys.exit()
        print("client connected the server %s, %d" % (self.host, self.port))
        print("pid",os.getpid())
        # print(video_file)
        from_camera = video_file == None
        print(cfg.cam_idx)
        cap = cv2.VideoCapture(cfg.cam_idx) if from_camera else cv2.VideoCapture(video_file)
        # frame = self.capture_run(cap, from_camera)
        frame_idx = 0
        if not cap.isOpened():
            print("open video failed")
            return


        while (True if from_camera == True else cap.isOpened()):
            start_time = time.time()
            ret, frame = cap.read()
           
            # time.sleep(0.05)
            if not ret:
                print("over")
                self.server.send(struct.pack("l99434s", int(-1), b''))
                break
            
            scale = 0.8

            y_start = int((480 - 480 * scale) / 2)
            y_end = int((480 - 480 * scale) / 2 + 480 * scale)

            x_start = int(640 - 640 * scale)
           
            # frame = frame[y_start:y_end, x_start:]

            if from_camera:
                frame = cv2.transpose(frame)
                frame = cv2.flip(frame, 1)
        
            # self.img_dic[frame_idx] = frame
            img_encode = cv2.imencode('.jpg', frame)[1]
            img_code = np.array(img_encode)
            str_encode = img_code.tostring()
         
            struc_2 = "ii%ds" % len(str_encode)
            data2 = struct.pack(struc_2, len(str_encode), int(frame_idx), str_encode)

            self.server.send(data2)
            self.img_dic[frame_idx] = (frame, start_time)
            print("send time ", str(time.time()-start_time))
            print("%s frame send over! pid: %d, %s" % (frame_idx, os.getpid(), str(start_time)))
            if frame_idx >= 1e+6:
                frame_idx = 0
            frame_idx +=1
        self.server.close()
        # cv2.destroyAllWindows()


if __name__ == '__main__':
    client_accept = ClientAccept()
    
    # client_accept.send_data()

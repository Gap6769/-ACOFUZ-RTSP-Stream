#!/usr/bin/env python

import tkinter
from tkinter import messagebox
import tkinter.filedialog
import cv2
import PIL.Image, PIL.ImageTk
import time
import threading
import os

HOME = os.path.dirname(os.path.abspath(__file__))

class MyVideoCapture:

    def __init__(self, video_source=0, width=None, height=None, fps=None):
    
        self.video_source = video_source
        self.width = width
        self.height = height
        self.fps = fps

        self.running = False
        

        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("[MyVideoCapture] Unable to open video source", video_source)

        if not self.width:
            self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))   
        if not self.height:
            self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)) 
        if not self.fps:
            try:
                self.fps = int(self.vid.get(cv2.CAP_PROP_FPS))  
            except:
                self.fps = 30

              
        self.ret = False
        self.frame = None
        
        self.convert_color = cv2.COLOR_BGR2RGB
      
        self.convert_pillow = True
        
        # Valores por defecto para grabación       
        self.recording = False
        self.recording_filename = 'output.mp4'
        self.recording_writer = None
        
  
        self.running = True
        self.thread = threading.Thread(target=self.process)
        self.thread.start()
        
    def snapshot(self, filename=None):
        if not self.ret:
            print('[MyVideoCapture] no frame for snapshot')
        else:
            if not filename:
                filename = time.strftime("frame-%d-%m-%Y-%H-%M-%S.jpg")
                
            if not self.convert_pillow:
                cv2.imwrite(filename, self.frame)
            else:
                self.frame.save(filename)
    
    def start_recording(self, filename=None):
        if self.recording:
            print('[MyVideoCapture] already recording:', self.recording_filename)
        else:
            if filename:
                self.recording_filename = filename
            else:
                self.recording_filename = time.strftime("%Y.%m.%d %H.%M.%S", time.localtime()) + ".avi"

            fourcc = cv2.VideoWriter_fourcc(*'MP42') 
            
            
            self.recording_writer = cv2.VideoWriter(self.recording_filename, fourcc, self.fps, (self.width, self.height))
            self.recording = True
            print('[MyVideoCapture] started recording:', self.recording_filename)
                   
    def stop_recording(self):
        if not self.recording:
            print('[MyVideoCapture] not recording')
        else:
            self.recording = False
            self.recording_writer.release() 
            print('[MyVideoCapture] stop recording:', self.recording_filename)
               
    def record(self, frame):
      
        if self.recording_writer and self.recording_writer.isOpened():
            self.recording_writer.write(frame)
 
     
    def process(self):
        while self.running:
            ret, frame = self.vid.read()
            
            if ret:

                frame = cv2.resize(frame, (self.width, self.height))

                if self.recording:
                    self.record(frame)
                    
                if self.convert_pillow:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = PIL.Image.fromarray(frame)
            else:
                print('[MyVideoCapture] stream end:', self.video_source)

                self.running = False
                if self.recording:
                    self.stop_recording()
                break
                

            self.ret = ret
            self.frame = frame


            time.sleep(1/self.fps)
        
    def get_frame(self):
        return self.ret, self.frame
    

    def __del__(self):
  
        if self.running:
            self.running = False
            self.thread.join()

  
        if self.vid.isOpened():
            self.vid.release()
            
 
class tkCamera(tkinter.Frame):

    def __init__(self, parent, text="", video_source=0, width=None, height=None):
        super().__init__(parent)
        
        self.video_source = video_source
        self.width  = width
        self.height = height


        self.vid = MyVideoCapture(self.video_source, self.width, self.height)
                
        self.label = tkinter.Label(self, text=text)
        self.label.pack()
        
        self.canvas = tkinter.Canvas(self, width=self.vid.width, height=self.vid.height)
        self.canvas.pack()

        # boton de grabacion
        self.btn_snapshot = tkinter.Button(self, text="Start Recording", command=self.start)
        self.btn_snapshot.pack(anchor='center', side='left')
        
        self.btn_snapshot = tkinter.Button(self, text="Stop Recording", command=self.stop)
        self.btn_snapshot.pack(anchor='center', side='left')
         
        # captura de pantalla
        self.btn_snapshot = tkinter.Button(self, text="Snapshot", command=self.snapshot)
        self.btn_snapshot.pack(anchor='center', side='left')

        # input
        self.btn_snapshot = tkinter.Button(self, text="Select Source", command=self.select_source)
        self.btn_snapshot.pack(anchor='center', side='left')
         

        self.delay = int(1000/self.vid.fps)


        print('[tkCamera] source:', self.video_source)
        print('[tkCamera] fps:', self.vid.fps, 'delay:', self.delay)
        
        self.image = None
        
        self.dialog = None
                
        self.running = True
        self.update_frame()

    def start(self):

        self.vid.start_recording()

    def stop(self):

        self.vid.stop_recording()
    
    def snapshot(self):


        self.vid.snapshot()
            
    def update_frame(self):

        ret, frame = self.vid.get_frame()
        
        if ret:

            self.image = frame
            self.photo = PIL.ImageTk.PhotoImage(image=self.image)
            self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        
        if self.running:
            self.after(self.delay, self.update_frame)

    def select_source(self):
        
        if not self.dialog:
            self.dialog = tkinter.Toplevel(self)

            tkinter.Label(self.dialog, text="Sources: \n").pack(fill='both', expand=True)
            
            for item in sources:
                name, source = item
                b = tkinter.Button(self.dialog, text=name, command=lambda data=item:self.on_select(data))
                b.pack(fill='both', expand=True)
                
            b = tkinter.Button(self.dialog, text="Open File...", command=self.on_select_file)
            b.pack(fill='both', expand=True)
            tkinter.Label(self.dialog, text='Enter RTSP link:\n').pack(fill='both', expand=True)
            inputtxt = tkinter.Text(self.dialog, height=1, width=20)
            inputtxt.pack(fill='both')
            c = tkinter.Button(self.dialog, text="Connect",command= lambda: self.on_input_adress(inputtxt.get("1.0", "end-1c")))
            c.pack(fill='both', expand=True)
                
    def on_select(self, item):
            name, source = item
            print('selected:', name, source)

            self.label['text'] = name
            self.video_source = source
            self.vid = MyVideoCapture(self.video_source, self.width, self.height)

            self.dialog.destroy()
            self.dialog = None  

    def on_input_adress(self,input):
        try:
            adress = input
            print('adress:', adress)
            self.label['text'] = 'RTSP link'
            self.video_source = adress
            self.vid = MyVideoCapture(self.video_source, self.width, self.height)
            self.dialog.destroy()
            self.dialog = None  
        except:
            print('error')
            messagebox.showinfo("Error", "Wrong adress")

    def on_select_file(self):
        
        
        result = tkinter.filedialog.askopenfilename(
                                        initialdir=".", 
                                        title="Select video file", 
                                        filetypes=(("AVI files", "*.avi"), ("MP4 files","*.mp4"), ("all files","*.*"))
                                    )
        
        if result:
            self.label['text'] = result.split('/')[-1]
            self.video_source = result
            self.vid = MyVideoCapture(self.video_source, self.width, self.height)

            self.dialog.destroy()
            self.dialog = None        
        
class App:

    def __init__(self, window, window_title, video_sources):
        self.window = window

        self.window.title(window_title)
        
        self.vids = []

        columns = 2
        for number, source in enumerate(video_sources):
            text, stream = source
            vid = tkCamera(self.window, text, stream, 400, 300)
            x = number % columns
            y = number // columns
            vid.grid(row=y, column=x)
            self.vids.append(vid)
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def on_closing(self, event=None):
        print('[App] stoping threads')
        for source in self.vids:
            source.vid.running = False
        print('[App] exit')
        self.window.destroy()


if __name__ == '__main__':     

    # Nuevos source peuden ser agregados aca:  (nombre, source)
    sources = [
        ('me', 0), 
        ('Kirchhoff Institute for Physics, Germany', 'http://pendelcam.kip.uni-heidelberg.de/mjpg/video.mjpg'),
        ('Blanton Bottling, Kentucky, USA', 'http://camera.buffalotrace.com/mjpg/video.mjpg'),
        ('Butovo, Moscow, Russia', 'http://camera.butovo.com/mjpg/video.mjpg'),
        ('Purdue Engineering Mall, USA', 'http://webcam01.ecn.purdue.edu/mjpg/video.mjpg'),
        ('Tokyo, Japan', 'http://61.211.241.239/nphMotionJpeg?Resolution=320x240&Quality=Standard'),
       
    ]
        
    # Crea la ventana
    App(tkinter.Tk(), "Tkinter and OpenCV", sources)

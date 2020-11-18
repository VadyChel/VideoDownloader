import os
from pytube import YouTube
from tkinter import *
from tkinter.ttk import Combobox
  
window = Tk()
window.title("VideoDownloader")
window.iconbitmap(os.path.dirname(os.path.abspath(__file__))+"/resources/img/logo.ico")
window.geometry("1200x700")

def clicked():
	yt = YouTube(txt.get())
	combo = Combobox(window)
	resolutions = sorted(list(set([
			stream.resolution 
			for stream in yt.streams.filter(
				type="video")
			])), 
			key=lambda key: int(key[:-1]),
			reverse=True
		)
	combo["values"] = resolutions
	combo.current(0)
	combo.grid(column=0, row=1)
	stream = yt.streams.filter(res=combo.get(), type="video").first()
	stream.download(filename=stream.title)

txt = Entry(window, width=100)
txt.grid(column=0, row=0)
btn = Button(window, text="Скачать!", command=clicked)  
btn.grid(column=1, row=0)

window.mainloop()
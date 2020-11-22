import os
import requests
from PIL import Image, ImageTk
from threading import Thread
from pytube import *
from tkinter import *
from tkinter.filedialog import *
from tkinter.ttk import *

class VideoDownloader:
	def __init__(self, window):
		self.window = window
		self.progress = 0
		self.current_stream = None
		self.thread = None
		self.save_directory = None

		self.window.title("VideoDownloader")
		self.window.iconbitmap(os.path.dirname(os.path.abspath(__file__))+"/resources/img/logo.ico")
		self.window.geometry("750x350")
		self.window.resizable(width=False, height=False)

		self.create_gui()

	def show_progress_bar(self, stream:Stream, chunk:int, bytes_remaining:int) -> int:
		new_progress = round(100-((bytes_remaining/stream.filesize_approx)*100))
		if new_progress != self.progress:
			self.progress = new_progress
			self.progress_text.configure(text=str(self.progress)+"%")
			self.progress_bar["value"] = self.progress

		if self.progress >= 100:
			self.thread.join()

	def clicked(self):
		self.yt = YouTube(self.url_sender.get())
		self.yt.register_on_progress_callback(self.show_progress_bar)

		self.search_btn.destroy()

		self.combo = Combobox(self.window, width=15)
		resolutions = sorted(list(set([
				stream.resolution 
				for stream in self.yt.streams.filter(
					type="video",
					subtype="mp4",
					progressive=True)])), 
				key=lambda key: int(key[:-1]),
				reverse=True
			)
		self.combo["values"] = resolutions
		self.combo.current(0)
		self.combo.grid(column=2, row=1, padx=25, sticky=S)

		self.download_btn = Button(self.window, text="Скачать!", command=self.download)  
		self.download_btn.grid(column=4, row=0)

		self.progress_bar = Progressbar(
			self.window, 
			length=350, 
			mode='determinate'
		)
		self.progress_bar.grid(column=0, row=1, sticky=W)
		
		self.progress_text = Label(self.window, text=str(self.progress)+"%")
		self.progress_text.grid(column=1, row=1, sticky=W)

		stream = self.yt.streams.filter(
			res=self.combo.get(), 
			type="video",
			subtype="mp4",
			progressive=True).first()
		self.current_stream = stream

	def create_gui(self):
		self.url_sender = Entry(self.window, width=90)
		self.url_sender.grid(column=0, row=0, columnspan=3)
		self.search_btn = Button(self.window, text="Поиск", command=self.clicked)  
		self.search_btn.grid(column=4, row=0)

	def download(self):
		self.set_save_directory()
		self.download_btn.destroy()
		self.combo.destroy()

		self.video_resolution = Label(self.window, text=self.current_stream.resolution)
		self.video_resolution.grid(column=2, row=1, padx=25, sticky=S)

		self.stop_btn = Button(self.window, text="Остановить", command=self.kill_thread)  
		self.stop_btn.grid(column=4, row=0)
		self.pause_btn = Button(self.window, text="Пауза", command=self.kill_thread)  
		self.pause_btn.grid(column=5, row=0)

		# image_url = requests.get(self.yt.thumbnail_url) 
		# image_file = open(os.environ["TEMP"]+"\CurrentVideoImage.jpg")
		# image_file.write(image_url.content)
		# image_file.close()

		# image_obj = Image.open(os.environ["TEMP"]+"\CurrentVideoImage.jpg")
		# image = ImageTk.PhotoImage(image_obj)

		# label = Label(image=photo)
		# label.pack()

		self.thread = Thread(target=self.download_stream)
		self.thread.start()

	def set_save_directory(self):
		self.save_directory = askdirectory()
		
	def download_stream(self) -> None:
		self.current_stream.download(filename=self.current_stream.title, output_path=self.save_directory)

	def kill_thread(self):
		self.thread.terminate()
		
if __name__ == "__main__":
	root = Tk()
	downloader = VideoDownloader(root)
	if downloader.thread is not None:
		root.protocol("WM_DELETE_WINDOW", downloader.kill_thread)
	root.mainloop()
import os
from threading import Thread
from pytube import *
from tkinter import *
from tkinter.ttk import Combobox

class VideoDownloader:
	def __init__(self, window):
		self.window = window
		self.progress = 0
		self.current_stream = None
		self.thread = None
		self.window.title("VideoDownloader")
		self.window.iconbitmap(os.path.dirname(os.path.abspath(__file__))+"/resources/img/logo.ico")
		self.window.geometry("1200x700")
		self.window.resizable(width=False, height=False)

	def show_progress_bar(self, stream:Stream, chunk:int, bytes_remaining:int) -> int:
		new_progress = round(100-((bytes_remaining/stream.filesize_approx)*100))
		self.progress = new_progress if new_progress != self.progress else self.progress
		self.progress_text.configure(text=str(self.progress))

	def clicked(self):
		yt = YouTube(self.url_sender.get())
		yt.register_on_progress_callback(self.show_progress_bar)

		self.search_btn.destroy()

		self.combo = Combobox(self.window)
		resolutions = sorted(list(set([
				stream.resolution 
				for stream in yt.streams.filter(
					type="video")
				])), 
				key=lambda key: int(key[:-1]),
				reverse=True
			)
		self.combo["values"] = resolutions
		self.combo.current(0)
		self.combo.grid(column=0, row=1)

		self.download_btn = Button(self.window, text="Скачать!", command=self.create_thread)  
		self.download_btn.grid(column=2, row=0)
		self.stop_btn = Button(self.window, text="Остановить", command=self.kill_thread)  
		self.stop_btn.grid(column=2, row=1)
		
		self.progress_text = Label(self.window, text=str(self.progress))
		self.progress_text.grid(column=1, row=1)

		stream = yt.streams.filter(
			res=self.combo.get(), 
			type="video").first()
		self.current_stream = stream

	def create_gui(self):
		self.url_sender = Entry(self.window, width=100)
		self.url_sender.grid(column=0, row=0)
		self.search_btn = Button(self.window, text="Поиск", command=self.clicked)  
		self.search_btn.grid(column=1, row=0)

	def create_thread(self):
		self.thread = Thread(target=self.download)
		self.thread.start()
		
	def download(self) -> None:
		self.current_stream.download(filename=self.current_stream.title)

	def kill_thread(self):
		self.thread.terminate()
		
if __name__ == "__main__":
	root = Tk()
	downloader = VideoDownloader(root)
	if downloader.thread is not None:
		root.protocol("WM_DELETE_WINDOW", downloader.kill_thread)
	root.mainloop()
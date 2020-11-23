import os
import re
import time
import ctypes
import subprocess
import requests
import ffmpeg
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
		self.current_video = None
		self.current_audio = None
		self.thread = None
		self.save_directory = None
		self.start_time = 0
		self.finish_time = 0
		self.stop_concatenating = False

		self.create_gui()

	def create_gui(self) -> None:
		self.window.title("VideoDownloader")
		self.window.iconbitmap(
			os.path.dirname(os.path.abspath(__file__)) + "/resources/img/logo.ico"
		)
		self.window.geometry("750x350")
		self.window.resizable(width=False, height=False)

		self.url_sender = Entry(self.window, width=90)
		self.url_sender.grid(column=0, row=0, columnspan=3)
		self.url_sender.bind("<Control-KeyPress>", self.bind_keys)

		self.search_btn = Button(self.window, text="Search", command=self.clicked)
		self.search_btn.grid(column=4, row=0)

	def is_ru_lang_keyboard(self) -> bool:
		u = ctypes.windll.LoadLibrary("user32.dll")
		pf = getattr(u, "GetKeyboardLayout")
		return hex(pf(0)) == '0x4190419'

	def bind_keys(self, event) -> None:
		if self.is_ru_lang_keyboard():
			if event.keycode==86:
				event.widget.event_generate("<<Paste>>")
			elif event.keycode==67: 
				event.widget.event_generate("<<Copy>>")    
			elif event.keycode==88: 
				event.widget.event_generate("<<Cut>>")    
			elif event.keycode==65535: 
				event.widget.event_generate("<<Clear>>")
			elif event.keycode==65: 
				event.widget.event_generate("<<SelectAll>>")

	def show_progress_bar(
		self, stream: Stream, chunk: int, bytes_remaining: int
	) -> int:
		new_progress = round((1 - bytes_remaining / self.current_stream.filesize) * 100)
		if new_progress != self.progress:
			self.progress = new_progress
			self.progress_text.configure(text=str(self.progress) + "%\t" + self.current_video.resolution)
			self.progress_bar["value"] = self.progress

	def clicked(self) -> None:
		self.yt = YouTube(self.url_sender.get())
		self.yt.register_on_progress_callback(self.show_progress_bar)

		self.search_btn.destroy()
		resolutions = self.get_video_resolutions()

		self.combo = Combobox(self.window, width=15)
		self.combo["values"] = resolutions
		self.combo.current(0)
		self.combo.grid(column=2, row=1, padx=25, sticky=S)
		self.combo.bind("<<ComboboxSelected>>", self.set_video_resolution)
		self.video_resolution = resolutions[0]

		self.progress_bar = Progressbar(self.window, length=350, mode="determinate")
		self.progress_bar.grid(column=0, row=1, sticky=W)

		self.progress_text = Label(self.window, text=str(self.progress) + "%")
		self.progress_text.grid(column=1, row=1, sticky=W)

		self.download_btn = Button(self.window, text="Download", command=self.download)
		self.download_btn.grid(column=4, row=0)

	def get_video_resolutions(self) -> list:
		resolutions = sorted(
			list(
				set(
					[
						stream.resolution
						for stream in self.yt.streams.filter(
							custom_filter_functions=[
								lambda s: s.subtype == "mp4" or s.subtype == "webm"
							],
							only_video=True,
						)
						if stream.resolution is not None
					]
				)
			),
			key=lambda key: int(key[:-1]),
			reverse=True,
		)
		return resolutions

	def set_video_resolution(self, event) -> None:
		self.video_resolution = self.combo.get()

	def get_video_stream(self) -> None:
		self.current_video = self.yt.streams.filter(
			custom_filter_functions=[
				lambda s: (s.subtype == "mp4") or (s.subtype == "webm")
			],
			res=self.video_resolution,
			only_video=True,
		).first()

	def get_audio_stream(self) -> None:
		self.current_audio = self.yt.streams.filter(
			only_audio=True, subtype="mp4"
		).first()

	def download(self) -> None:
		self.set_save_directory()

		self.download_btn.destroy()
		self.combo.destroy()

		self.get_audio_stream()
		self.get_video_stream()

		self.downloading_info = Label(self.window, text="Preparation...")
		self.downloading_info.grid(column=2, row=1, padx=25, sticky=S)

		self.stop_btn = Button(self.window, text="Stop", command=self.kill_thread)
		self.stop_btn.grid(column=4, row=0)
		self.pause_btn = Button(self.window, text="Pause", command=self.kill_thread)
		self.pause_btn.grid(column=5, row=0)

		# image_url = requests.get(self.yt.thumbnail_url)
		# image_file = open(os.environ["TEMP"]+"\CurrentVideoImage.jpg")
		# image_file.write(image_url.content)
		# image_file.close()

		# image_obj = Image.open(os.environ["TEMP"]+"\CurrentVideoImage.jpg")
		# image = ImageTk.PhotoImage(image_obj)

		# label = Label(image=photo)
		# label.pack()

		self.create_streams_thread()

	def set_save_directory(self) -> None:
		self.save_directory = askdirectory()

	def download_video(self) -> None:
		self.start_time = time.time()
		self.downloading_info.configure(text="Video upload")

		self.current_stream = self.current_video
		self.current_video.download(filename="Video", output_path=self.save_directory)

	def download_audio(self) -> None:
		self.downloading_info.configure(text="Audio upload")

		self.current_stream = self.current_audio
		self.current_audio.download(filename="Audio", output_path=self.save_directory)

		self.connect_streams()
		self.finish_time = time.time()
		self.downloading_info.configure(text=f"Uploaded in {str(self.finish_time - self.start_time)}")

	def connect_streams(self) -> None:
		self.downloading_info.configure(text="Concatenating streams")

		self.stop_concatenating = True
		Thread(target=self.concatenating_streams_proggress).start()

		video_title = re.sub("[^\w\-_\. ]", "", self.current_video.title)
		video_path = self.save_directory + "/Video." + self.current_video.subtype
		audio_path = self.save_directory + "/Audio." + self.current_audio.subtype
		output_path = self.save_directory + f"/{video_title}.mp4"

		command = f"""ffmpeg -i "{video_path}" -i "{audio_path}" -c copy "{output_path}" """
		print(command)
		subprocess.run(command)

		os.remove(video_path)
		os.remove(audio_path)

		self.stop_concatenating = False

	def concatenating_streams_proggress(self):
		self.progress_bar.configure(mode="indeterminate")
		while self.stop_concatenating:
			if self.progress_bar["value"] >= 100:
				self.progress_bar["value"] = 10

			self.progress_bar["value"] += 10
			time.sleep(0.5)

		self.progress_bar.configure(mode="determinate")
		self.progress_bar["value"] = 100
		self.progress_text.configure(text="100%\t"+self.current_video.resolution)

	def download_streams(self) -> None:
		self.download_video()
		self.download_audio()

	def create_streams_thread(self) -> None:
		self.thread = Thread(target=self.download_streams)
		self.thread.start()

	def kill_thread(self) -> None:
		self.thread.terminate()


if __name__ == "__main__":
	root = Tk()
	downloader = VideoDownloader(root)
	if downloader.thread is not None:
		root.protocol("WM_DELETE_WINDOW", downloader.kill_thread)
	root.mainloop()

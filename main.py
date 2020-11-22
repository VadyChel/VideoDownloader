import os
import sys
import subprocess
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
		self.current_video = None
		self.current_audio = None
		self.video_thread = None
		self.audio_thread = None
		self.save_directory = None

		self.create_gui()

	def create_gui(self):
		self.window.title("VideoDownloader")
		self.window.iconbitmap(
			os.path.dirname(os.path.abspath(__file__)) + "/resources/img/logo.ico"
		)
		self.window.geometry("750x350")
		self.window.resizable(width=False, height=False)

		self.url_sender = Entry(self.window, width=90)
		self.url_sender.grid(column=0, row=0, columnspan=3)
		self.search_btn = Button(self.window, text="Поиск", command=self.clicked)
		self.search_btn.grid(column=4, row=0)

	def show_progress_bar(
		self, stream: Stream, chunk: int, bytes_remaining: int
	) -> int:
		new_progress = round((1 - bytes_remaining / self.current_stream.filesize) * 100)
		if new_progress != self.progress:
			self.progress = new_progress
			self.progress_text.configure(text=str(self.progress) + "%")
			self.progress_bar["value"] = self.progress

		if self.current_video is None:
			self.create_audio_thread()
		elif self.current_audio is None:
			print("done")
			self.connect_streams()

	def clicked(self):
		self.yt = YouTube(self.url_sender.get())
		self.yt.register_on_progress_callback(self.show_progress_bar)

		self.search_btn.destroy()

		self.combo = Combobox(self.window, width=15)
		resolutions = sorted(
			list(
				set(
					[
						stream.resolution
						for stream in self.yt.streams.filter(
							custom_filter_functions=[
								lambda s: (s.subtype == "mp4") or (s.subtype == "webm")
							],
							only_video=True,
						)
					]
				)
			),
			key=lambda key: int(key[:-1]),
			reverse=True,
		)
		self.combo["values"] = resolutions
		self.combo.current(0)
		self.combo.grid(column=2, row=1, padx=25, sticky=S)
		self.combo.bind("<<ComboboxSelected>>", self.set_video_resolution)
		self.video_resolution = resolutions[0]

		self.progress_bar = Progressbar(self.window, length=350, mode="determinate")
		self.progress_bar.grid(column=0, row=1, sticky=W)

		self.progress_text = Label(self.window, text=str(self.progress) + "%")
		self.progress_text.grid(column=1, row=1, sticky=W)

		self.download_btn = Button(self.window, text="Скачать!", command=self.download)
		self.download_btn.grid(column=4, row=0)

	def set_video_resolution(self, event):
		self.video_resolution = self.combo.get()

	def get_video_stream(self):
		self.current_video = self.yt.streams.filter(
			custom_filter_functions=[
				lambda s: (s.subtype == "mp4") or (s.subtype == "webm")
			],
			res=self.video_resolution,
			only_video=True,
		).first()

	def get_audio_stream(self):
		self.current_audio = self.yt.streams.filter(
			only_audio=True, subtype="mp4"
		).first()

	def download(self):
		self.set_save_directory()

		self.download_btn.destroy()
		self.combo.destroy()

		self.get_audio_stream()
		self.get_video_stream()

		self.stream_type = Label(self.window, text=self.current_video.resolution)
		self.stream_type.grid(column=2, row=1, padx=25, sticky=S)

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

		self.create_video_thread()

	def set_save_directory(self):
		self.save_directory = askdirectory()

	def download_video(self) -> None:
		self.current_video.download(filename="Video", output_path=self.save_directory)
		if self.progress >= 100:
			print("done1")
			self.current_video = None

	def download_audio(self) -> None:
		self.current_audio.download(filename="Audio", output_path=self.save_directory)
		if self.progress >= 100:
			print("done2")
			self.current_audio = None

	def connect_streams(self) -> None:
		video_path = self.save_directory + "/Video" + self.current_video.subtype
		audio_path = self.save_directory + "/Audio" + self.current_audio.subtype
		subprocess.run(
			f"""ffmpeg -i {video_path} -i {audio_path} -c copy "{self.current_stream.title}.mp4" """
		)
		os.remove(video_path)
		os.remove(audio_path)

	def create_video_thread(self) -> None:
		self.current_stream = self.current_video
		self.thread = Thread(target=self.download_video)
		self.thread.start()

	def create_audio_thread(self) -> None:
		self.current_stream = self.current_audio
		self.thread = Thread(target=self.download_audio)
		self.thread.start()

	def kill_thread(self):
		self.thread.terminate()


if __name__ == "__main__":
	root = Tk()
	downloader = VideoDownloader(root)
	if downloader.video_thread is not None:
		root.protocol("WM_DELETE_WINDOW", downloader.kill_thread)
	root.mainloop()

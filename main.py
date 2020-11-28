import os
import re
import time
import requests
import datetime
import ctypes
import subprocess
from tooltip import ToolTip
from hurry.filesize import size
from tkinter.font import Font
from PIL import Image as PIL_IMAGE, ImageTk
from threading import Thread
from pytube import *
from tkinter import Tk
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
		self.save_directory = (
			os.environ.get("USERPROFILE") or os.environ.get("HOME")
		) + "\VideoDownloader"
		try:
			os.mkdir(self.save_directory)
		except OSError:
			pass
		self.start_time = 0
		self.finish_time = 0
		self.stop_concatenating = False

		self.create_app()

	def create_app(self) -> None:
		self.window.title("VideoDownloader")
		self.window.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "/logo.ico")
		self.window.geometry("750x350")
		self.window.resizable(width=False, height=False)

		self.style = Style()
		self.style.configure(
			"VideoTitle.TLabel", font=("Segoe UI", 18), foreground="#444444"
		)
		self.style.configure(
			"SearchButton.TButton", font=("Segoe UI", 16), foreground="#444444"
		)
		self.style.configure(
			"DownloadButton.TButton", font=("Segoe UI", 16), foreground="#444444"
		)
		self.style.configure(
			"StopButton.TButton", font=("Segoe UI", 16), foreground="#444444"
		)
		self.style.configure(
			"PauseButton.TButton", font=("Segoe UI", 16), foreground="#444444"
		)
		self.style.configure(
			"UrlSender.TEntry", font=("Segoe UI", 18), foreground="#444444"
		)

		self.create_gui()

	def show_progress_bar(
		self, stream: Stream, chunk: int, bytes_remaining: int
	) -> int:
		self.downloaded_filesize.configure(
			text=f"{size(int(self.current_stream.filesize))}/{size(int(self.current_stream.filesize - bytes_remaining))}"
		)
		new_progress = round((1 - bytes_remaining / self.current_stream.filesize) * 100)
		if new_progress != self.progress:
			self.progress = new_progress
			self.progress_text.configure(text=str(self.progress) + "%")
			self.progress_bar["value"] = self.progress

	def clicked(self) -> None:
		self.yt = YouTube(self.url_sender.get())
		self.yt.register_on_progress_callback(self.show_progress_bar)

		self.remove_all_widgets()
		self.create_gui()
		self.create_gui_after_click()

	def create_gui(self) -> None:
		self.url_sender = Entry(self.window, style="UrlSender.TEntry")
		self.url_sender.place(x=10, y=10, width=580, height=40)

		self.search_btn = Button(
			self.window,
			text="Search",
			command=self.clicked,
			style="SearchButton.TButton",
		)
		self.search_btn.place(x=600, y=10, width=140, height=40)

	def create_gui_after_click(self) -> None:
		self.video_title = Label(
			self.window,
			text=self.yt.title
			if len(self.yt.title) < 34
			else self.yt.title[:34] + "...",
			style="VideoTitle.TLabel",
		)
		self.video_title.place(x=10, y=290, width=440, height=40)
		self.title_tooltip = ToolTip(self.video_title)
		self.video_title.bind("<Enter>", self.show_full_title)
		self.video_title.bind("<Leave>", self.remove_full_title)

		video_thumbnail = self.get_video_thumbnail()
		self.video_icon = Label(image=video_thumbnail)
		self.video_icon.image = video_thumbnail
		self.video_icon.place(x=10, y=70, width=330, height=200)

		self.progress_bar = Progressbar(self.window, mode="determinate")
		self.progress_bar.place(x=360, y=245, width=330, height=25)

		self.progress_text = Label(self.window, text=str(self.progress) + "%")
		self.progress_text.place(x=700, y=245, width=35, height=25)

		self.save_directory_text = Label(self.window, text=self.save_directory)
		self.save_directory_text.place(x=360, y=70, width=275, height=30)

		self.edit_save_path_btn = Button(
			self.window, text="Save As", command=self.set_save_directory
		)
		self.edit_save_path_btn.place(x=645, y=70, width=95, height=30)

		self.resolution_combo_info = Label(self.window, text="Resolution")
		self.resolution_combo_info.place(x=360, y=110, width=120, height=20)

		self.caption_combo_info = Label(self.window, text="Captions")
		self.caption_combo_info.place(x=490, y=110, width=120, height=20)

		self.format_combo_info = Label(self.window, text="Format video")
		self.format_combo_info.place(x=620, y=110, width=120, height=20)

		self.resolution_combo = Combobox(self.window, state="readonly")
		self.caption_combo = Combobox(self.window, state="readonly")
		self.format_combo = Combobox(self.window, state="readonly")

		self.configure_combos()

		self.resolution_combo.place(x=360, y=140, width=120, height=30)
		self.caption_combo.place(x=490, y=140, width=120, height=30)
		self.format_combo.place(x=620, y=140, width=120, height=30)

		self.download_btn = Button(
			self.window,
			text="Download",
			command=self.download,
			style="DownloadButton.TButton",
		)
		self.download_btn.place(x=605, y=290, width=130, height=40)

	def configure_combos(self):
		resolutions = self.get_video_resolutions()
		self.resolution_combo["values"] = resolutions
		self.resolution_combo.current(0)
		self.resolution_combo.bind("<<ComboboxSelected>>", self.set_video_resolution)
		self.video_resolution = resolutions[0]

		captions = [c.name for c in self.yt.captions]
		captions.insert(0, "None")
		captions.insert(1, "All")
		self.caption_combo["values"] = captions
		self.caption_combo.current(0)
		self.caption_combo.bind("<<ComboboxSelected>>", self.set_caption)
		self.caption_lang = captions[0]

		self.format_combo["values"] = ("mp4", "mkv", "avi")
		self.format_combo.current(0)
		self.format_combo.bind("<<ComboboxSelected>>", self.set_video_format)
		self.video_format = "mp4"

	def set_video_resolution(self, event) -> None:
		self.video_resolution = self.resolution_combo.get()

	def set_caption(self, event) -> None:
		self.caption = self.caption_combo.get()

	def set_video_format(self, event) -> None:
		self.video_format = self.format_combo.get()

	def set_save_directory(self) -> None:
		save_directory = askdirectory()
		if save_directory != "":
			self.save_directory = save_directory
			self.save_directory_text.configure(text=self.save_directory)

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

	def get_video_thumbnail(self) -> ImageTk:
		image_obj = requests.get(self.yt.thumbnail_url)
		image_file = open(os.environ["TEMP"] + "\\video_image.png", "wb")
		image_file.write(image_obj.content)
		image_file.close()

		image = PIL_IMAGE.open(os.environ["TEMP"] + "\\video_image.png").resize(
			(330, 200)
		)
		image_tk = ImageTk.PhotoImage(image=image)

		return image_tk

	def download(self) -> None:
		self.download_btn.destroy()
		self.remove_combos()

		self.get_audio_stream()
		self.get_video_stream()

		self.downloading_info = Label(self.window, text="Preparation...")
		self.downloading_info.place(x=360, y=210, width=195, height=25)

		self.downloaded_filesize = Label(self.window, text=f"0M/0M")
		self.downloaded_filesize.place(x=565, y=210, width=90, height=25)

		self.downloaded_video_resolution = Label(
			self.window, text=self.video_resolution
		)
		self.downloaded_video_resolution.place(x=665, y=210, width=70, height=25)

		self.stop_btn = Button(
			self.window,
			text="Stop",
			command=self.stop_download,
			style="StopButton.TButton",
		)
		self.stop_btn.place(x=465, y=290, width=130, height=40)
		self.pause_btn = Button(
			self.window,
			text="Pause",
			command=self.kill_thread,
			style="PauseButton.TButton",
		)
		self.pause_btn.place(x=605, y=290, width=130, height=40)

		self.create_streams_thread()

	def download_video(self) -> None:
		self.start_time = datetime.datetime.now()
		self.downloading_info.configure(text="Video upload")

		self.current_stream = self.current_video
		self.current_video.download(filename="Video", output_path=self.save_directory)

	def download_audio(self) -> None:
		self.downloading_info.configure(text="Audio upload")

		self.current_stream = self.current_audio
		self.current_audio.download(filename="Audio", output_path=self.save_directory)

		self.connect_streams()
		self.finish_time = datetime.datetime.now()

		seconds = (self.finish_time - self.start_time).seconds
		uploading_time = (
			str(round(seconds % 3600 / 60.0)) + "m"
			if seconds % 3600 / 60.0 > 1
			else str(round(seconds)) + "s"
		)

		self.downloading_info.configure(text=f"Uploaded in {uploading_time}")

	def connect_streams(self) -> None:
		self.downloading_info.configure(text="Concatenating streams")

		self.stop_concatenating = True
		Thread(target=self.concatenating_streams_proggress).start()

		video_title = re.sub("[^\w\-_\. ]", "", self.current_video.title)
		video_path = self.save_directory + "/Video." + self.current_video.subtype
		audio_path = self.save_directory + "/Audio." + self.current_audio.subtype

		for f in os.listdir(self.save_directory):
			if len(list(f[:-4])) > 1:
				if list(f[:-4])[::-1][0] == ")":
					num = int(list(f[:-4])[::-1][1]) + 1
					video_title += f"""({num})"""
					break

			if f == video_title + ".mp4":
				video_title += "(1)"
				break

		output_path = self.save_directory + f"/{video_title}." + self.video_format

		command = (
			f"""ffmpeg -i "{video_path}" -i "{audio_path}" -c copy "{output_path}" """
		)
		subprocess.run(command)

		os.remove(video_path)
		os.remove(audio_path)

		self.stop_concatenating = False

	def concatenating_streams_proggress(self):
		self.progress_bar.configure(mode="indeterminate")
		while self.stop_concatenating:
			if self.progress_bar["value"] >= 100:
				self.progress_bar["value"] = 0

			self.progress_bar["value"] += 10
			time.sleep(0.2)

		self.progress_bar.configure(mode="determinate")
		self.progress_bar["value"] = 100
		self.progress_text.configure(text="100%")

	def download_streams(self) -> None:
		self.download_video()
		self.download_audio()

	def create_streams_thread(self) -> None:
		self.thread = Thread(target=self.download_streams)
		self.thread.start()

	def stop_download(self) -> None:
		self.stop_download = False

	def show_full_title(self, event):
		self.title_tooltip.showtip(self.yt.title)

	def remove_full_title(self, event):
		self.title_tooltip.hidetip()

	def remove_combos(self) -> None:
		self.resolution_combo_info.destroy()
		self.format_combo_info.destroy()
		self.caption_combo_info.destroy()

		self.resolution_combo.destroy()
		self.format_combo.destroy()
		self.caption_combo.destroy()

	def remove_all_widgets(self) -> None:
		for widget in self.window.winfo_children():
			widget.destroy()

	def kill_thread(self) -> None:
		self.thread.terminate()


if __name__ == "__main__":
	root = Tk()
	downloader = VideoDownloader(root)
	if downloader.thread is not None:
		root.protocol("WM_DELETE_WINDOW", downloader.kill_thread)
	root.mainloop()

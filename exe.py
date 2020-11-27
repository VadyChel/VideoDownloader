import cx_Freeze
import sys
import matplotlib

base = None

if sys.platform == "win32":
    base = "Win32GUI"
elif sys.platform == "win64":
    base = "Win64GUI"

executables = [cx_Freeze.Executable("main.py", base=base, icon="logo.ico")]

cx_Freeze.setup(
    name="VideoDownloader",
    options={
        "build_exe": {
			"optimize": 1,
			"excludes": [
				"PyQt5", 
				"sqlite3", 
				"numpy", 
				"PySide2", 
				"multiprocessing", 
				"asyncio", 
				"certifi", 
				"chardet", 
				"collections", 
				"distutils", 
				"email", 
				"encodings",
				"html",
				"http",
				"idna",
				"logging",
				"urllib",
				"urllib3",
				"xml",
				"unittest",
				"test"
			],
            "packages": [
                "tkinter",
                "requests",
                "ctypes",
                "hurry.filesize",
                "PIL",
                "pytube",
            ],
            "include_files": ["logo.ico", "ffmpeg/"],
        },
    },
    version="0.1",
    executables=executables,
)

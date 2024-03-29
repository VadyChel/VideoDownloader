import re
from tkinter import Label, LEFT, SOLID, Toplevel


class ToolTip:
	def __init__(self, widget):
		self.widget = widget
		self.tipwindow = None
		self.id = None
		self.x = self.y = 0

	def showtip(self, text):
		self.text = text
		if self.tipwindow or not self.text:
			return
		x, y, _, cy = self.widget.bbox("insert")
		x = x + self.widget.winfo_rootx() + 57
		y = y + cy + self.widget.winfo_rooty() + 27
		self.tipwindow = tw = Toplevel(self.widget)
		tw.wm_overrideredirect(1)
		tw.wm_geometry("+%d+%d" % (x, y))
		label = Label(
			tw,
			text=self.text,
			justify=LEFT,
			background="#ffffe0",
			relief=SOLID,
			borderwidth=1,
			font=("tahoma", "8", "normal"),
		)
		label.pack(ipadx=1)

	def hidetip(self):
		tw = self.tipwindow
		self.tipwindow = None
		if tw is not None:
			tw.destroy()

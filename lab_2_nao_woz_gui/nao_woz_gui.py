import tkinter as tk
from tkinter import messagebox


class NaoControlPanel:
	"""Desktop control panel for a NAO Wizard-of-Oz interaction session."""

	COLORS = {
		"window": "#eeeeee",
		"panel": "#f4f4f4",
		"border": "#b8b8b8",
		"text": "#171717",
		"blue": "#2396e8",
		"green": "#4caf50",
		"red": "#ef5350",
		"yellow": "#f3c64f",
	}

	def __init__(self, root):
		self.root = root
		self.root.title("NAO Robot Live Interaction Control Panel")
		self.root.geometry("750x900")
		self.root.minsize(680, 760)
		self.root.configure(bg=self.COLORS["window"])

		self.robot_ip = tk.StringVar(value="10.117.35.236")
		self.connection_status = tk.StringVar(value="Status: Disconnected")
		self.speech_text = tk.StringVar()
		self.event_status = tk.StringVar(value="Ready for an interaction session")
		self.video_running = True
		self.video_canvas = None

		self._build_header()
		self._build_connection_section()
		self._build_speech_section()
		self._build_behavior_section()
		self._build_video_section()
		self._draw_video_preview()

	def _section(self, parent, title):
		return tk.LabelFrame(
			parent,
			text=title,
			bg=self.COLORS["panel"],
			fg=self.COLORS["text"],
			font=("TkDefaultFont", 10, "bold"),
			padx=16,
			pady=10,
			bd=1,
			relief="groove",
		)

	def _button(self, parent, text, command, **kwargs):
		options = {
			"font": ("TkDefaultFont", 10),
			"height": 1,
			"relief": "raised",
			"bd": 1,
			"cursor": "hand2",
			"padx": 10,
			"pady": 4,
		}
		options.update(kwargs)
		return tk.Button(parent, text=text, command=command, **options)

	def _build_header(self):
		header = tk.Frame(self.root, bg=self.COLORS["window"], height=38)
		header.pack(fill="x")
		header.pack_propagate(False)
		tk.Label(
			header,
			text="NAO Robot Live Interaction Control Panel",
			bg=self.COLORS["window"],
			fg="#444444",
			font=("TkDefaultFont", 11, "bold"),
		).pack(pady=9)

	def _build_connection_section(self):
		section = self._section(self.root, "Robot Connection")
		section.pack(fill="x", padx=15, pady=(8, 8))

		tk.Label(section, text="Robot IP:", bg=self.COLORS["panel"]).grid(
			row=0, column=0, sticky="w", padx=(2, 8), pady=4
		)
		tk.Entry(section, textvariable=self.robot_ip, width=15, font=("TkDefaultFont", 10)).grid(
			row=0, column=1, sticky="w", pady=4
		)
		self.connect_button = self._button(
			section, "Connect", self._toggle_connection, bg=self.COLORS["green"], fg="white", width=10
		)
		self.connect_button.grid(row=0, column=2, padx=(16, 0), pady=2)
		tk.Label(
			section,
			textvariable=self.connection_status,
			bg=self.COLORS["panel"],
			fg="#008000",
			font=("TkDefaultFont", 10, "italic"),
		).grid(row=0, column=3, sticky="e", padx=(35, 0))
		section.columnconfigure(3, weight=1)

	def _build_speech_section(self):
		section = self._section(self.root, "Conversational Abilities & Utterances")
		section.pack(fill="x", padx=15, pady=0)

		tk.Label(section, text="Pre-scripted Utterances:", bg=self.COLORS["panel"]).pack(anchor="w")
		utterances = tk.Frame(section, bg=self.COLORS["panel"])
		utterances.pack(fill="x", pady=(11, 15))
		for index, text in enumerate(("Greeting", "Gratitude", "Transition", "Farewell")):
			self._button(
				utterances,
				text,
				lambda phrase=text: self._send_speech(phrase),
				width=13,
				bg="#dddddd",
			).grid(row=0, column=index, padx=(5 if index else 0, 10), sticky="ew")
			utterances.columnconfigure(index, weight=1)

		tk.Label(section, text="Custom Speech Entry:", bg=self.COLORS["panel"]).pack(anchor="w")
		speech_row = tk.Frame(section, bg=self.COLORS["panel"])
		speech_row.pack(fill="x", pady=(9, 3))
		entry = tk.Entry(speech_row, textvariable=self.speech_text, font=("TkDefaultFont", 10))
		entry.pack(side="left", fill="x", expand=True, ipady=5)
		self._button(
			speech_row,
			"Send Speech",
			lambda: self._send_speech(self.speech_text.get()),
			bg=self.COLORS["blue"],
			fg="white",
			width=12,
		).pack(side="left", padx=(12, 0))
		entry.bind("<Return>", lambda _event: self._send_speech(self.speech_text.get()))

	def _build_behavior_section(self):
		section = self._section(self.root, "Non-Verbal Behaviors & Controls")
		section.pack(fill="x", padx=15, pady=15)

		groups = (
			("Nonverbal Gestures", ("Wave Hand (sitting)", "Wave Hand (standing)", "Nodding while Standing")),
			("LED Facial Displays", ("LED: Blue (Thinking)", "LED: Green (Happy)", "LED: Red (Alert)")),
			("Posture Changes", ("Stand", "Crouch", "Sit")),
		)
		for column, (title, actions) in enumerate(groups):
			group = tk.LabelFrame(
				section,
				text=title,
				bg=self.COLORS["panel"],
				fg=self.COLORS["text"],
				padx=10,
				pady=8,
			)
			group.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0))
			section.columnconfigure(column, weight=1)
			for row, action in enumerate(actions):
				color = self.COLORS["blue"] if "Blue" in action else self.COLORS["green"] if "Green" in action else self.COLORS["red"] if "Red" in action else "#dddddd"
				foreground = "white" if color != "#dddddd" else self.COLORS["text"]
				self._button(
					group,
					action,
					lambda command=action: self._announce(command),
					bg=color,
					fg=foreground,
					width=19,
				).pack(fill="x", pady=(0 if row == 0 else 10, 0))

	def _build_video_section(self):
		section = self._section(self.root, "Live Robot Vision")
		section.pack(fill="both", expand=True, padx=15, pady=(0, 0))
		self.video_canvas = tk.Canvas(
			section,
			width=320,
			height=240,
			bg="#252b33",
			highlightthickness=1,
			highlightbackground="#8c8c8c",
		)
		self.video_canvas.pack(pady=(4, 7))
		self.video_button = self._button(
			section,
			"Stop Video Feed",
			self._toggle_video,
			bg=self.COLORS["red"],
			fg="white",
			width=14,
		)
		self.video_button.pack()
		tk.Label(section, textvariable=self.event_status, bg=self.COLORS["panel"], fg="#555555").pack(pady=(8, 0))

	def _draw_video_preview(self):
		canvas = self.video_canvas
		canvas.delete("all")
		canvas.create_rectangle(0, 0, 320, 240, fill="#26313b", outline="")
		canvas.create_rectangle(0, 0, 320, 55, fill="#425563", outline="")
		canvas.create_text(12, 17, text="LIVE ROBOT CAMERA", anchor="w", fill="#d8e3e9", font=("TkDefaultFont", 9, "bold"))
		canvas.create_oval(288, 10, 300, 22, fill="#e64b4b", outline="")
		canvas.create_text(305, 16, text="REC", fill="#ffffff", font=("TkDefaultFont", 8, "bold"))
		canvas.create_rectangle(28, 78, 292, 198, fill="#202830", outline="#81909a", width=2)
		canvas.create_text(
			160,
			138,
			text="NO FEED FOUND" if self.video_running else "VIDEO FEED STOPPED",
			fill="#f4f4f4",
			font=("TkDefaultFont", 12, "bold"),
		)

	def _toggle_connection(self):
		connected = self.connection_status.get().startswith("Status: Connected")
		if connected:
			self.connection_status.set("Status: Disconnected")
			self.connect_button.configure(text="Connect", bg=self.COLORS["green"])
			self.event_status.set("Robot disconnected")
		else:
			address = self.robot_ip.get().strip() or "unknown address"
			self.connection_status.set(f"Status: Connected ({address})")
			self.connect_button.configure(text="Disconnect", bg=self.COLORS["red"])
			self.event_status.set(f"Connected to NAO at {address}")

	def _send_speech(self, phrase):
		phrase = phrase.strip()
		if not phrase:
			messagebox.showinfo("Speech", "Enter a phrase before sending speech.")
			return
		self.speech_text.set(phrase)
		self.event_status.set(f'NAO says: "{phrase}"')

	def _announce(self, command):
		self.event_status.set(f"Action queued: {command}")

	def _toggle_video(self):
		self.video_running = not self.video_running
		self.video_button.configure(
			text="Stop Video Feed" if self.video_running else "Start Video Feed",
			bg=self.COLORS["red"] if self.video_running else self.COLORS["green"],
		)
		self.event_status.set("Live video feed running" if self.video_running else "Live video feed stopped")
		self._draw_video_preview()


def main():
	root = tk.Tk()
	NaoControlPanel(root)
	root.mainloop()


if __name__ == "__main__":
	main()
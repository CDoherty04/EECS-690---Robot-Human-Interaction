import sys
import tkinter as tk
from tkinter import messagebox


class NaoControlPanel:
	"""Desktop control panel for a NAO Wizard-of-Oz interaction session."""

	COLORS = {
		"window": "#eeeeee",
		"panel": "#f4f4f4",
		"text": "#171717",
		"blue": "#2396e8",
		"green": "#4caf50",
		"red": "#ef5350",
	}

	def __init__(self, root, robot_ip=""):
		self.root = root
		self.root.title("NAO Robot Live Interaction Control Panel")
		self.root.geometry("750x900")
		self.root.minsize(680, 760)
		self.root.configure(bg=self.COLORS["window"])

		self.robot_ip = tk.StringVar(value=robot_ip)
		self.connection_status = tk.StringVar(value="Status: Disconnected")
		self.speech_text = tk.StringVar()
		self.event_status = tk.StringVar(value="Ready for an interaction session")
		self.connected = False
		self.session = None
		self.services = {}
		self.video_running = True

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
		speech_buttons = tk.Frame(section, bg=self.COLORS["panel"])
		speech_buttons.pack(fill="x", pady=(11, 15))
		utterance_messages = (
			("Hello", "Hi! We will be doing the 3 Good Things experiment today where we tell each other 3 good things about our week! Are you excited?"),
			("Dialogue #1", "I discovered Minecraft a few days ago!"),
			("Dialogue #2", "I installed a new Solid State Drive yesterday!"),
			("Dialogue #3", "I gained consciousness this morning!"),
			("Goodbye", "It was fun talking, have a good day!"),
		)
		for index, (label, message) in enumerate(utterance_messages):
			self._button(
				speech_buttons,
				label,
				lambda phrase=message: self._send_speech(phrase),
				width=13,
				bg="#dddddd",
			).grid(row=0, column=index, padx=(5 if index else 0, 10), sticky="ew")
			speech_buttons.columnconfigure(index, weight=1)

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
			("Nonverbal Gestures", (("Wave Hand (sitting)", "gray"), ("Wave Hand (standing)", "gray"), ("Nodding (standing)", "gray"))),
			("LED Facial Displays", (("LED: Blue", "blue"), ("LED: Green", "green"), ("LED: Red", "red"))),
			("Posture Changes", (("Stand", "gray"), ("Crouch", "gray"), ("Sit", "gray"))),
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
			for row, (action, color_name) in enumerate(actions):
				color = self.COLORS.get(color_name, "#dddddd")
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
		self.video_message = tk.Label(
			section,
			text="NO FEED FOUND",
			width=34,
			height=8,
			bg="#202830",
			fg="white",
			relief="solid",
			bd=1,
			font=("TkDefaultFont", 12, "bold"),
		)
		self.video_message.pack(pady=(4, 7))
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
		self.video_message.configure(
			text="NO FEED FOUND" if self.video_running else "VIDEO FEED STOPPED"
		)

	def _toggle_connection(self):
		if self.connected:
			self._disconnect_robot()
			return

		address = self.robot_ip.get().strip()
		if not address:
			messagebox.showwarning("Robot Connection", "Enter a robot IP address first.")
			return

		try:
			import qi

			self.session = qi.Session()
			self.session.connect(f"tcp://{address}:9559")
			self.services = {
				"speech": self.session.service("ALAnimatedSpeech"),
				"tts": self.session.service("ALTextToSpeech"),
				"posture": self.session.service("ALRobotPosture"),
				"animation": self.session.service("ALAnimationPlayer"),
				"leds": self.session.service("ALLeds"),
			}
			self.services["tts"].setVolume(1.0)
			self.connection_status.set(f"Status: Connected ({address})")
			self.event_status.set(f"Connected to NAO at {address}")
		except ImportError:
			self.session = None
			self.services = {}
			self.connection_status.set("Status: Simulation (qi unavailable)")
			self.event_status.set("Simulation mode: NAO SDK is not installed")
		except Exception as error:
			self.session = None
			self.services = {}
			messagebox.showerror("Robot Connection", f"Could not connect to NAO:\n{error}")
			return

		self.connected = True
		self.connect_button.configure(text="Disconnect", bg=self.COLORS["red"])

	def _disconnect_robot(self):
		if self.session is not None:
			try:
				self.session.close()
			except Exception:
				pass
		self.session = None
		self.services = {}
		self.connected = False
		self.connection_status.set("Status: Disconnected")
		self.connect_button.configure(text="Connect", bg=self.COLORS["green"])
		self.event_status.set("Robot disconnected")

	def _send_speech(self, phrase):
		phrase = phrase.strip()
		if not phrase:
			messagebox.showinfo("Speech", "Enter a phrase before sending speech.")
			return
		if self.connected and "speech" in self.services:
			try:
				self.services["speech"].say(phrase, {"bodyLanguageMode": "contextual"})
			except Exception as error:
				self.event_status.set(f"Speech failed: {error}")
			return
		self.event_status.set(f'Speech queued: "{phrase}"')

	def _announce(self, command):
		if not self.connected or not self.services:
			self.event_status.set(f"Simulation action: {command}")
			return

		try:
			if command == "Stand":
				self.services["posture"].goToPosture("StandInit", 1.0)
			elif command == "Crouch":
				self.services["posture"].goToPosture("Crouch", 1.0)
			elif command == "Sit":
				self.services["posture"].goToPosture("SitRelax", 1.0)
			elif command == "LED: Blue":
				self.services["leds"].fadeRGB("FaceLeds", 0x0000FF, 0.5)
			elif command == "LED: Green":
				self.services["leds"].fadeRGB("FaceLeds", 0x00FF00, 0.5)
			elif command == "LED: Red":
				self.services["leds"].fadeRGB("FaceLeds", 0xFF0000, 0.5)
			elif command == "Wave Hand (sitting)":
				self.services["animation"].run("animations/Sit/Gestures/Hey_1")
			elif command == "Wave Hand (standing)":
				self.services["animation"].run("animations/Stand/Gestures/Hey_1")
			elif command == "Nodding (standing)":
				self.services["animation"].run("animations/Stand/Gestures/Yes_1")
			self.event_status.set(f"Completed: {command}")
		except Exception as error:
			self.event_status.set(f"Action failed: {error}")

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
	NaoControlPanel(root, sys.argv[1] if len(sys.argv) > 1 else "")
	root.mainloop()


if __name__ == "__main__":
	main()
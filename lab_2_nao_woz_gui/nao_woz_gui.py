import sys
import tkinter as tk
from tkinter import messagebox


class NaoControlPanel:
	"""Desktop control panel for a NAO Wizard-of-Oz interaction session."""

	def __init__(self, root, robot_ip=""):
		self.root = root
		self.root.title("NAO Robot Live Interaction Control Panel")

		self.robot_ip = tk.StringVar(value=robot_ip)
		self.connection_status = tk.StringVar(value="Status: Disconnected")
		self.speech_text = tk.StringVar()
		self.connected = False
		self.session = None
		self.services = {}
		self.video_running = True

		self._build_connection_section()
		self._build_speech_section()
		self._build_behavior_section()
		self._build_video_section()

	# Template for labeled sections
	def _section(self, parent, title):
		return tk.LabelFrame(
			parent,
			text=title,
			padx=16,
			pady=10,
		)

	# Template for buttons
	def _button(self, parent, text, command, **kwargs):
		options = {
			"relief": "raised",
			"cursor": "hand2",
			"padx": 10,
			"pady": 4,
		}
		options.update(kwargs)
		return tk.Button(parent, text=text, command=command, **options)

	# Connection UI section for Robot IP input
	def _build_connection_section(self):
		section = self._section(self.root, "Robot Connection")
		section.pack(fill="x", padx=15, pady=8)

		tk.Label(section, text="Robot IP:").grid(row=0, column=0)
		tk.Entry(section, textvariable=self.robot_ip).grid(row=0, column=1, padx=10)

		self.connect_button = self._button(section, "Connect", self._toggle_connection, bg="green", fg="white")
		self.connect_button.grid(row=0, column=2)

		tk.Label(section, textvariable=self.connection_status, fg="green").grid(row=0, column=3, sticky="e")
		section.columnconfigure(3, weight=1)

	# Section to invoke pre-scripted or custom speech utterances
	def _build_speech_section(self):
		section = self._section(self.root, "Conversational Abilities & Utterances")
		section.pack(fill="x", padx=15)

		tk.Label(section, text="Pre-scripted Utterances:").pack(anchor="w")
		speech_buttons = tk.Frame(section)
		speech_buttons.pack(fill="x", pady=15)

		self._button(
			speech_buttons,
			"Hello",
			lambda: self._send_speech("Hi! We will be doing the 3 Good Things experiment today where we tell each other 3 good things about our week! Are you excited?"),
			width=15,
		).grid(row=0, column=0, padx=(0, 10), sticky="ew")

		self._button(
			speech_buttons,
			"Dialogue #1",
			lambda: self._send_speech("I discovered Minecraft a few days ago!"),
			width=15,
		).grid(row=0, column=1, padx=(5, 10), sticky="ew")

		self._button(
			speech_buttons,
			"Dialogue #2",
			lambda: self._send_speech("I installed a new Solid State Drive yesterday!"),
			width=15,
		).grid(row=0, column=2, padx=(5, 10), sticky="ew")

		self._button(
			speech_buttons,
			"Dialogue #3",
			lambda: self._send_speech("I gained consciousness this morning!"),
			width=15,
		).grid(row=0, column=3, padx=(5, 10), sticky="ew")

		self._button(
			speech_buttons,
			"Goodbye",
			lambda: self._send_speech("It was fun talking, have a good day!"),
			width=15,
		).grid(row=0, column=4, padx=(5, 10), sticky="ew")

		speech_buttons.columnconfigure(0, weight=1)
		speech_buttons.columnconfigure(1, weight=1)
		speech_buttons.columnconfigure(2, weight=1)
		speech_buttons.columnconfigure(3, weight=1)
		speech_buttons.columnconfigure(4, weight=1)

		# Custom speech entry
		tk.Label(section, text="Custom Speech Entry:").pack(anchor="w")
		speech_row = tk.Frame(section)
		speech_row.pack(fill="x", pady=(9, 3))
		entry = tk.Entry(speech_row, textvariable=self.speech_text)
		entry.pack(side="left", fill="x", expand=True, ipady=5)
		self._button(
			speech_row,
			"Send Speech",
			lambda: self._send_speech(self.speech_text.get()),
			bg="blue",
			fg="white",
			width=12,
		).pack(side="left", padx=(12, 0))
		entry.bind("<Return>", lambda _event: self._send_speech(self.speech_text.get()))

	# Non-verbal behaviors and controls section
	def _build_behavior_section(self):
		section = self._section(self.root, "Non-Verbal Behaviors & Controls")
		section.pack(fill="x", padx=15, pady=15)

		# Nonverbal Gestures
		gestures = tk.LabelFrame(section, text="Nonverbal Gestures", padx=10, pady=8)
		gestures.grid(row=0, column=0, sticky="nsew")
		self._button(gestures, "Wave Hand (sitting)", lambda: self._announce("Wave Hand (sitting)"), bg="gray", fg="white", width=19).pack(fill="x")
		self._button(gestures, "Wave Hand (standing)", lambda: self._announce("Wave Hand (standing)"), bg="gray", fg="white", width=19).pack(fill="x", pady=(10, 0))
		self._button(gestures, "Nodding (standing)", lambda: self._announce("Nodding (standing)"), bg="gray", fg="white", width=19).pack(fill="x", pady=(10, 0))

		# LED Facial Displays
		leds = tk.LabelFrame(section, text="LED Facial Displays", padx=10, pady=8)
		leds.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
		self._button(leds, "LED: Blue", lambda: self._announce("LED: Blue"), bg="blue", fg="white", width=19).pack(fill="x")
		self._button(leds, "LED: Green", lambda: self._announce("LED: Green"), bg="green", fg="white", width=19).pack(fill="x", pady=(10, 0))
		self._button(leds, "LED: Red", lambda: self._announce("LED: Red"), bg="red", fg="white", width=19).pack(fill="x", pady=(10, 0))

		# Posture Changes
		postures = tk.LabelFrame(section, text="Posture Changes", padx=10, pady=8)
		postures.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
		self._button(postures, "Stand", lambda: self._announce("Stand"), bg="gray", fg="white", width=19).pack(fill="x")
		self._button(postures, "Crouch", lambda: self._announce("Crouch"), bg="gray", fg="white", width=19).pack(fill="x", pady=(10, 0))
		self._button(postures, "Sit", lambda: self._announce("Sit"), bg="gray", fg="white", width=19).pack(fill="x", pady=(10, 0))

		section.columnconfigure(0, weight=1)
		section.columnconfigure(1, weight=1)
		section.columnconfigure(2, weight=1)

	# Section for live video feed from the robot's camera
	def _build_video_section(self):
		section = self._section(self.root, "Live Robot Vision")
		section.pack(fill="both", expand=True, padx=15, pady=(0, 0))
		self.video_message = tk.Label(
			section,
			text="NO FEED FOUND",
			width=34,
			height=8,
			bg="gray",
		)
		self.video_message.pack(pady=(4, 7))
		self.video_button = self._button(
			section,
			"Stop Video Feed",
			self._toggle_video,
			bg="red",
			fg="white",
			width=14,
		)
		self.video_button.pack()

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
		except ImportError:
			self.session = None
			self.services = {}
			self.connected = False
			self.connection_status.set("Status: Simulation (qi unavailable)")
			messagebox.showerror("Simulation mode", "NAO SDK is not installed")
		except Exception as error:
			self.session = None
			self.services = {}
			messagebox.showerror("Robot Connection", f"Could not connect to NAO:\n{error}")
			return

		self.connected = True
		self.connect_button.configure(text="Disconnect", bg="red")

	# Disconnect from the robot and clean up resources
	def _disconnect_robot(self):
		if self.session is not None:
			self.session.close()
		self.session = None
		self.services = {}
		self.connected = False
		self.connection_status.set("Status: Disconnected")
		self.connect_button.configure(text="Connect", bg="green")

	# Send speech to NAO robot using the ALAnimatedSpeech service
	def _send_speech(self, phrase):
		phrase = phrase.strip()
		if not phrase:
			messagebox.showinfo("Speech", "Enter a phrase before sending speech.")
			return
		if self.connected and "speech" in self.services:
			try:
				self.services["speech"].say(phrase, {"bodyLanguageMode": "contextual"})
			except Exception as error:
				messagebox.showerror("Speech failed", f"Could not send speech to NAO:\n{error}")
			return

	# NAO API calls for non-verbal behaviors and posture changes
	def _announce(self, command):
		if not self.connected or not self.services:
			messagebox.showwarning("Robot Connection", "Connect to NAO before performing an action.")
			return

		try:
			if command == "Stand":
				self._change_posture("StandInit")
			elif command == "Crouch":
				self._change_posture("Crouch")
			elif command == "Sit":
				self._change_posture("SitRelax")
			elif command == "LED: Blue":
				self._set_face_led(0x0000FF)
			elif command == "LED: Green":
				self._set_face_led(0x00FF00)
			elif command == "LED: Red":
				self._set_face_led(0xFF0000)
			elif command == "Wave Hand (sitting)":
				self._play_animation("animations/Sit/Gestures/Hey_1")
			elif command == "Wave Hand (standing)":
				self._play_animation("animations/Stand/Gestures/Hey_1")
			elif command == "Nodding (standing)":
				self._play_animation("animations/Stand/Gestures/Yes_1")
		except Exception as error:
			messagebox.showerror("Action failed", f"Could not perform action on NAO:\n{error}")

	def _change_posture(self, posture):
		self.services["posture"].goToPosture(posture, 1.0)

	def _set_face_led(self, color):
		self.services["leds"].fadeRGB("FaceLeds", color, 0.5)

	def _play_animation(self, animation):
		self.services["animation"].run(animation)

	# Changes feed boolean and updates rendered content
	def _toggle_video(self):
		self.video_running = not self.video_running
		if self.video_running:
			self.video_message.configure(text="NO FEED FOUND")
			self.video_button.configure(text="Stop Video Feed", bg="red")
		else:
			self.video_message.configure(text="VIDEO FEED STOPPED")
			self.video_button.configure(text="Start Video Feed", bg="green")

def main():
	root = tk.Tk()
	NaoControlPanel(root, sys.argv[1] if len(sys.argv) > 1 else "")
	root.mainloop()

if __name__ == "__main__":
	main()
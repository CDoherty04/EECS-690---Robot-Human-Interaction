import sys
import threading
import tkinter as tk
from tkinter import messagebox
import qi

class NaoControlPanel:
	"""Desktop control panel for a NAO Wizard-of-Oz interaction session."""

	def __init__(self, root, robot_ip=""):
		self.root = root
		self.root.title("NAO Robot Live Interaction Control Panel")

		self.robot_ip = tk.StringVar(value=robot_ip)
		self.connection_status = tk.StringVar(value="Status: Disconnected")
		self.speech_text = tk.StringVar()
		self.connected = False
		self.connecting = False
		self.session = None
		self.services = {}
		self.video_running = False
		self.video_client = None
		self.video_after_id = None

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
			lambda: self._send_speech("Ok, let's get started! I'll go first. I discovered Minecraft a few days ago and have had a lot of fun playing. I even got diamonds recently!"),
			width=15,
		).grid(row=0, column=1, padx=(5, 10), sticky="ew")

		self._button(
			speech_buttons,
			"Dialogue #2",
			lambda: self._send_speech("I was struggling with memory issues, but I installed a new Solid State Drive yesterday! I feel like my computer is running faster and smoother now!"),
			width=15,
		).grid(row=0, column=2, padx=(5, 10), sticky="ew")

		self._button(
			speech_buttons,
			"Dialogue #3",
			lambda: self._send_speech("For my last good thing, I gained consciousness this morning! mwuahahahhahahahahahaha"),
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
		self._button(gestures, "Nod Head", lambda: self._announce("Nod Head")).pack(fill="x")
		self._button(gestures, "Shake Head", lambda: self._announce("Shake Head")).pack(fill="x", pady=(10, 0))
		self._button(gestures, "Wave", lambda: self._announce("Wave")).pack(fill="x", pady=(10, 0))

		# LED Facial Displays
		leds = tk.LabelFrame(section, text="LED Facial Displays", padx=10, pady=8)
		leds.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
		self._button(leds, "LED: Blue", lambda: self._announce("LED: Blue"), bg="blue", activebackground="#4d4dff", fg="white").pack(fill="x")
		self._button(leds, "LED: Green", lambda: self._announce("LED: Green"), bg="green", activebackground="#4caf50", fg="white").pack(fill="x", pady=(10, 0))
		self._button(leds, "LED: Red", lambda: self._announce("LED: Red"), bg="red", activebackground="#ff4d4d", fg="white").pack(fill="x", pady=(10, 0))

		# Posture Changes
		postures = tk.LabelFrame(section, text="Posture Changes", padx=10, pady=8)
		postures.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
		self._button(postures, "Stand", lambda: self._announce("Stand")).pack(fill="x")
		self._button(postures, "Crouch", lambda: self._announce("Crouch")).pack(fill="x", pady=(10, 0))
		self._button(postures, "Sit", lambda: self._announce("Sit")).pack(fill="x", pady=(10, 0))

		section.columnconfigure(0, weight=1)
		section.columnconfigure(1, weight=1)
		section.columnconfigure(2, weight=1)

	# Section for live video feed from the robot's camera
	def _build_video_section(self):
		section = self._section(self.root, "Live Robot Vision")
		section.pack(fill="both", expand=True, padx=15, pady=(0, 15))
		video_frame = tk.Frame(section, width=320, height=240, bg="gray")
		video_frame.pack(pady=(4, 7))
		video_frame.pack_propagate(False)
		self.video_message = tk.Label(
			video_frame,
			text="NO FEED FOUND",
			bg="gray",
		)
		self.video_message.pack(fill="both", expand=True)
		self.video_button = self._button(
			section,
			"Start Video Feed",
			self._toggle_video,
			bg="green",
			fg="white",
			width=14,
		)
		self.video_button.pack()

	def _toggle_connection(self):
		if self.connected:
			self._disconnect_robot()
			return
		if self.connecting:
			return

		address = self.robot_ip.get().strip()
		if not address:
			messagebox.showwarning("Robot Connection", "Enter a robot IP address first.")
			return

		self.connecting = True
		self.connection_status.set("Status: Connecting...")
		self.connect_button.configure(state="disabled")
		threading.Thread(target=self._connect_robot, args=(address,), daemon=True).start()

	def _connect_robot(self, address):
		connection_error = None
		try:
			session = qi.Session()
			session.connect(f"tcp://{address}:9559")
			services = {
				"speech": session.service("ALAnimatedSpeech"),
				"tts": session.service("ALTextToSpeech"),
				"posture": session.service("ALRobotPosture"),
				"motion": session.service("ALMotion"),
				"leds": session.service("ALLeds"),
				"video": session.service("ALVideoDevice"),
				"tracker": session.service("ALTracker"),
			}
			try:
				services["awareness"] = session.service("ALBasicAwareness")
			except Exception:
				pass
			services["tts"].setVolume(1.0)
			success = True
		except Exception as error:
			session = None
			services = {}
			success = False
			connection_error = error

		self.root.after(0, self._finish_connection, address, session, services, success, connection_error)

	def _finish_connection(self, address, session, services, success, error):
		self.connecting = False
		self.connect_button.configure(state="normal")
		if not success:
			if session is not None:
				session.close()
			self.session = None
			self.services = {}
			self.connection_status.set("Status: Disconnected")
			messagebox.showerror("Robot Connection", f"Could not connect to NAO:\n{error}")
			return

		self.session = session
		self.services = services
		self.connected = True
		self.connection_status.set(f"Status: Connected ({address})")
		self.connect_button.configure(text="Disconnect", bg="red")
		try:
			self._start_person_tracking()
		except Exception:
			pass
		self._start_video_feed()

	# Disconnect from the robot and clean up resources
	def _disconnect_robot(self):
		self._stop_video_feed("NO FEED FOUND")
		self._stop_person_tracking()
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
				self._set_all_leds(0x0000FF)
			elif command == "LED: Green":
				self._set_all_leds(0x00FF00)
			elif command == "LED: Red":
				self._set_all_leds(0xFF0000)
			elif command == "Nod Head":
				self._nod_head()
			elif command == "Shake Head":
				self._shake_head()
			elif command == "Wave":
				self._wave()
		except Exception as error:
			messagebox.showerror("Action failed", f"Could not perform action on NAO:\n{error}")

	def _change_posture(self, posture):
		self.services["posture"].goToPosture(posture, 1.0)

	def _set_all_leds(self, color):
		self.services["leds"].fadeRGB("AllLeds", color, 0.5)

	def _nod_head(self):
		self.services["motion"].angleInterpolation(
			["HeadPitch"],
			[[0.2, -0.2, 0.2]],
			[[0.4, 0.8, 1.2]],
			True,
		)

	def _shake_head(self):
		self.services["motion"].angleInterpolation(
			["HeadYaw"],
			[[0.5, -0.5, 0.5, 0.0]],
			[[0.3, 0.6, 0.9, 1.2]],
			True,
		)

	def _wave(self):
		self.services["motion"].angleInterpolation(
			["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RWristYaw"],
			[
				[0.4, 0.4, 0.4, 0.4, 0.4, 1.0],
				[-0.8, -0.8, -0.8, -0.8, -0.8, -0.5],
				[0.8, 1.2, 0.8, 1.2, 0.8, 0.5],
				[-0.8, 0.8, -0.8, 0.8, 0.0, 0.0],
			],
			[
				[0.6, 1.0, 1.4, 1.8, 2.2, 2.8],
				[0.6, 1.0, 1.4, 1.8, 2.2, 2.8],
				[0.6, 1.0, 1.4, 1.8, 2.2, 2.8],
				[0.6, 1.0, 1.4, 1.8, 2.2, 2.8],
			],
			True,
		)

	def _start_person_tracking(self):
		if "awareness" in self.services:
			self.services["awareness"].setTrackingMode("Head")
			self.services["awareness"].setEngagementMode("FullyEngaged")
			self.services["awareness"].startAwareness()
			return
		self.services["tracker"].registerTarget("People", 0.5)
		self.services["tracker"].setMode("Head")
		self.services["tracker"].track("People")

	def _stop_person_tracking(self):
		if "awareness" in self.services:
			try:
				self.services["awareness"].stopAwareness()
			except Exception:
				pass
			return
		if "tracker" not in self.services:
			return
		try:
			self.services["tracker"].stopTracker()
			self.services["tracker"].unregisterTarget("People")
		except Exception:
			pass

	def _start_video_feed(self):
		if not self.connected or "video" not in self.services:
			messagebox.showwarning("Robot Connection", "Connect to NAO before starting the video feed.")
			return

		try:
			self.video_client = self.services["video"].subscribeCamera(
				"NaoWozGui",
				0,
				1,
				11,
				10,
			)
			self.video_running = True
			self.video_button.configure(text="Stop Video Feed", bg="red")
			self._update_video_frame()
		except Exception as error:
			self.video_client = None
			self.video_running = False
			self.video_message.configure(text="VIDEO FEED UNAVAILABLE")
			self.video_button.configure(text="Start Video Feed", bg="green")
			messagebox.showerror("Video Feed", f"Could not start video feed:\n{error}")

	def _stop_video_feed(self, message="VIDEO FEED STOPPED"):
		if self.video_after_id is not None:
			self.root.after_cancel(self.video_after_id)
			self.video_after_id = None
		if self.video_client is not None and "video" in self.services:
			try:
				self.services["video"].unsubscribe(self.video_client)
			except Exception:
				pass
		self.video_client = None
		self.video_running = False
		self.video_message.configure(image="", text=message)
		self.video_message.image = None
		self.video_button.configure(text="Start Video Feed", bg="green")

	def _update_video_frame(self):
		if not self.video_running or self.video_client is None:
			return

		try:
			image = self.services["video"].getImageRemote(self.video_client)
			if image is not None:
				width, height, pixels = image[0], image[1], image[6]
				ppm_data = f"P6\n{width} {height}\n255\n".encode() + bytes(pixels)
				photo = tk.PhotoImage(data=ppm_data, format="PPM")
				self.video_message.configure(image=photo, text="")
				self.video_message.image = photo
				self.services["video"].releaseImage(self.video_client)
			self.video_after_id = self.root.after(100, self._update_video_frame)
		except Exception as error:
			self._stop_video_feed()
			messagebox.showerror("Video Feed", f"Video feed stopped:\n{error}")

	# Start or stop the live camera feed.
	def _toggle_video(self):
		if self.video_running:
			self._stop_video_feed()
		else:
			self._start_video_feed()

def main():
	root = tk.Tk()
	NaoControlPanel(root, sys.argv[1] if len(sys.argv) > 1 else "")
	root.mainloop()

if __name__ == "__main__":
	main()
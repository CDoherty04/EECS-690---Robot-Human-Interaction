import os
import time
import paramiko
import qi
from openai import OpenAI
from dotenv import load_dotenv
import json

#your .env file needs to be in the parent directory of this script, and contain your OpenAI API key as OPENAI_API_KEY=your_api_key_here
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

AUDIO_PATH_LOCAL = "recording.wav"
AUDIO_PATH_ROBOT = "/home/nao/recording.wav"

SPEECH_PATH_LOCAL = "response.mp3"
SPEECH_PATH_ROBOT = "/home/nao/response.mp3"

#a class to encapsulate all Qi and Nao interactions, including TTS, LEDs, posture, motion, behavior management, video, audio recording, and audio playback
class NaoProxy:
    def __init__(self, session):
        self.session = session
        try:
            self.tts = session.service("ALTextToSpeech")
        except Exception as e:
            print(f"Failed to load ALTextToSpeech: {e}")
            self.tts = None

        try:
            self.leds = session.service("ALLeds")
        except Exception as e:
            print(f"Failed to load ALLEDs: {e}")
            self.leds = None

        try:
            self.posture = session.service("ALRobotPosture")
            self.motion = session.service("ALMotion")
        except Exception as e:
            print(f"Failed to load ALRobotPosture or Motion: {e}")
            self.posture = None
            self.motion = None

        try:
            self.animate = session.service("ALBehaviorManager")
        except Exception as e:
            print(f"Failed to load ALBehaviorManager: {e}")
            self.animate = None

        try:
            self.video = session.service("ALVideoDevice")
            self.cam_client = None
        except Exception as e:
            print(f"Failed to load ALVideoDevice: {e}")
            self.video = None

        try:
            self.audio_recorder = session.service("ALAudioRecorder")
            # Reset any stuck recording states from previous crashed runs
            try:
                self.audio_recorder.stopMicrophonesRecording()
            except Exception:
                pass
        except Exception as e:
            print(f"Failed to load ALAudioRecorder: {e}")
            self.audio_recorder = None

        try:
            self.audio_player = session.service("ALAudioPlayer")
        except Exception as e:
            print(f"Failed to load ALAudioPlayer: {e}")
            self.audio_player = None

        try:
            self.memory = session.service("ALMemory")
        except Exception as e:
            print(f"Failed to load ALMemory: {e}")
            self.memory = None

        try:
            self.audio_device = session.service("ALAudioDevice")
        except Exception as e:
            print(f"Failed to load ALAudioDevice: {e}")
            self.audio_device = None

    #ensures the robot is standing up and ready for interaction, using posture and motion services if available
    def ensure_standing(self):
        if self.motion and self.posture:
            print("Ensuring robot is standing...")
            self.motion.wakeUp()
            self.posture.goToPosture("Stand", 1.0)
        else:
            print("[Mock Motion]: Standing up")

    #changes the robot's eye LED color to blue, green, or red using the ALLeds service if available
    def set_leds(self, color_name):
        if self.leds:
            if color_name == "Blue":
                self.leds.fadeRGB("FaceLeds", 0.0, 0.0, 1.0, 0.1)
            elif color_name == "Green":
                self.leds.fadeRGB("FaceLeds", 0.0, 1.0, 0.0, 0.1)
            elif color_name == "Red":
                self.leds.fadeRGB("FaceLeds", 1.0, 0.0, 0.0, 0.1)
        else:
            print(f"[Mock LEDs]: Set to {color_name}")

    #changes the robot's expression by executing a predefined behavior using the ALBehaviorManager service if available
    #students should add an additional 5 expressions to this function and the system instruction file, to have the ChatGPT model generate those expressions in its responses
    def change_expression(self, expressionName):
        if self.animate:
            if expressionName =="nod":
                self.animate.startBehavior("animations/Stand/Gestures/Yes_1")
            elif expressionName=="hi":
                self.animate.startBehavior("animations/Stand/Gestures/Hey_1")
            elif expressionName =="listen":
                self.animate.startBehavior("animations/Stand/BodyTalk/Listening/Listening_2")
            elif expressionName=="happy":
                self.animate.startBehavior("animations/Stand/Gestures/Enthusiastic_1")
        else:
            print("[Mock Expression change]: Start")

    #starts recording audio from the robot's front microphone and saves it to the specified path using the ALAudioRecorder service if available
    def start_recording(self, path):
        if self.audio_recorder:
            self.audio_recorder.startMicrophonesRecording(path, "wav", 16000, [0, 0, 1, 0])
        else:
            print("[Mock AudioRecorder]: Start recording")

    #stops recording audio from the robot's microphones using the ALAudioRecorder service if available
    def stop_recording(self):
        if self.audio_recorder:
            self.audio_recorder.stopMicrophonesRecording()
        else:
            print("[Mock AudioRecorder]: Stop recording")

    #plays an audio file on the robot's speakers using the ALAudioPlayer service if available, in a separate thread to allow simultaneous execution of other actions (like changing expressions)
    def play_file(self, path):
        if self.audio_player and self.audio_device:
            self.audio_device.setOutputVolume(75)
            self.audio_player.playFile(path, 1, 0)
            self.audio_device.setOutputVolume(55)
        else:
            print(f"[Mock AudioPlayer]: Playing {path}")

#a class to handle OpenAI API interactions, including Whisper for transcription, GPT-5-nano for text generation, and TTS for speech synthesis
class OpenAIHandler:
    def __init__(self, robot_ip, system_prompt_path="system_prompt.txt", robot_user="nao", robot_pass="nao"):
        self.client = OpenAI()
        self.robot_ip = robot_ip
        self.robot_user = robot_user
        self.robot_pass = robot_pass

        # Load system instructions from file safely
        try:
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                system_instruction = f.read().strip()
        except FileNotFoundError:
            system_instruction = "You are a helpful assistant. Briefly notify the user ASAP that their custom instructions did not get uploaded"

        # Initialize conversation history with the system prompt file contents
        self.conversation_history = [
            {"role": "system", "content": system_instruction}
        ]

    # Transcribe audio using OpenAI Whisper
    def transcribe_audio(self, local_path):
        print("Sending to OpenAI Whisper...")
        with open(local_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text

    # Get a text response from GPT-5-nano, using the conversation history to maintain context across multiple turns
    def get_gpt_response(self, user_speech):
        print("Asking GPT-5-nano...")

        # Append user input to maintain multi-turn history locally
        self.conversation_history.append({"role": "user", "content": user_speech})

        chat_response = self.client.chat.completions.create(
            model="gpt-5-nano",
            response_format={"type": "json_object"},  # Ensures JSON output matching your formatting requirements
            messages=self.conversation_history
        )
        reply = chat_response.choices[0].message.content

        # Append assistant response to history
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    # Generate speech audio using OpenAI TTS and save it to a local file
    def generate_speech_audio(self, reply, local_speech_path):
        print("Generating speech audio via OpenAI TTS...")
        with self.client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="sage", #students should experiment with different voices
            input=reply
        ) as response:
            response.stream_to_file(local_speech_path)

    # Transfer files between the local machine and the robot using Paramiko
    def transfer_files(self, action, local_path, robot_path):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.robot_ip, username=self.robot_user, password=self.robot_pass)
        sftp = ssh.open_sftp()

        if action == "get":
            print("Downloading user audio file...")
            sftp.get(robot_path, local_path)
        elif action == "put":
            print("Uploading response audio to robot...")
            sftp.put(local_path, robot_path)

        sftp.close()
        ssh.close()

#a class to encapsulate the entire pipeline of recording, transcribing, generating a response, and playing it back on the robot
class WhisperNaoApp:
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        self.port = 9559
        self.session = qi.Session()
        self.AUDIO_PATH_ROBOT = AUDIO_PATH_ROBOT
        self.AUDIO_PATH_LOCAL = AUDIO_PATH_LOCAL
        self.SPEECH_PATH_LOCAL = SPEECH_PATH_LOCAL
        self.SPEECH_PATH_ROBOT = SPEECH_PATH_ROBOT
        self.times_run = 0

        try:
            self.session.connect(f"tcp://{self.robot_ip}:{self.port}")
            print(f"Connected to NAO at {self.robot_ip}")
        except RuntimeError as e:
            print(f"Failed to connect to NAO at {self.robot_ip}: {e}")
            self.session = None

        self.nao = NaoProxy(self.session)
        self.openai_handler = OpenAIHandler(self.robot_ip)
        self.nao.ensure_standing()

    #the main pipeline that handles recording user speech, transcribing it, generating a response with GPT, synthesizing speech, and playing it back on the robot
    def run_pipeline(self):
        user_speech = ""
        if not self.session:
            print("Skipping execution because session is not connected.")
            return False
        if self.times_run > 0: #only runs after the robot has introduced
            # 1. Record audio from user (turning eyes green while recording, red when stopped)
            print("Turning eyes green and starting recording...")
            self.nao.set_leds("Green")
            self.nao.start_recording(self.AUDIO_PATH_ROBOT)

            # Poll foot bumpers until pressed (> 0.5)
            while True:
                left_pressed = 0.0
                right_pressed = 0.0
                if self.nao.memory:
                    try:
                        left_pressed = self.nao.memory.getData("LeftBumperPressed")
                        right_pressed = self.nao.memory.getData("RightBumperPressed")
                    except Exception:
                        pass

                if (left_pressed is not None and left_pressed > 0.5) or (right_pressed is not None and right_pressed > 0.5):
                    break

                time.sleep(0.1)

            self.nao.stop_recording()
            self.nao.set_leds("Red")
            print("Recording stopped. Eyes turned red.")

            # 2. Connect via Paramiko and pull the user recording from the robot
            self.openai_handler.transfer_files("get", self.AUDIO_PATH_LOCAL, self.AUDIO_PATH_ROBOT)

            # 3. Transcribe the recording via Whisper
            user_speech = self.openai_handler.transcribe_audio(self.AUDIO_PATH_LOCAL)
            print("\n--- Transcription Result ---")
            print(user_speech)
            print("----------------------------\n")

        # 4. Get a multi-turn response from GPT based on the system instruction file
        reply = self.openai_handler.get_gpt_response(user_speech)
        data = json.loads(reply)
        responseText = data["msg"]
        reaction = data["expression"]

        print("\n--- GPT Response ---")
        print(responseText)
        print("-----------------------------\n")

        # 5. Use OpenAI TTS to generate an mp3 response file locally
        self.openai_handler.generate_speech_audio(responseText, self.SPEECH_PATH_LOCAL)

        # 6. Push the generated response mp3 back to the robot via Paramiko
        self.openai_handler.transfer_files("put", self.SPEECH_PATH_LOCAL, self.SPEECH_PATH_ROBOT)

        # 7. Play the mp3 response file through the NAO's speakers
        #print("Playing response and shifting expression concurrently...")
        self.nao.change_expression(reaction)
        self.nao.play_file(SPEECH_PATH_ROBOT)

        self.times_run = self.times_run + 1
        return True

if __name__ == "__main__": # i nee to change
    import sys
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    app = WhisperNaoApp(robot_ip)
    robotConnected = True
    while robotConnected:
        robotConnected = app.run_pipeline()

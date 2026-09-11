import os
import time
import qi
import json

#a class to encapsulate all Qi and Nao interactions, including TTS, LEDs, posture, motion, behavior management, video, audio recording, and audio playback
class NaoProxy:
    def __init__(self, session):
        self.session = session

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

#a class to encapsulate the entire pipeline
class WhisperNaoApp:
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        self.port = 9559
        self.session = qi.Session()

        try:
            self.session.connect(f"tcp://{self.robot_ip}:{self.port}")
            print(f"Connected to NAO at {self.robot_ip}")
        except RuntimeError as e:
            print(f"Failed to connect to NAO at {self.robot_ip}: {e}")
            self.session = None

        self.nao = NaoProxy(self.session)
        self.nao.ensure_standing()

    #the main pipeline that handles recording user speech, transcribing it, generating a response with GPT, synthesizing speech, and playing it back on the robot
    def run_pipeline(self):
        user_speech = ""
        if not self.session:
            print("Skipping execution because session is not connected.")
            return False

        reactionList = ['hi', 'nod', 'listen', 'happy'] #edit this list to include the reactions you put in the change_expression definition

        for item in reactionList:
            self.nao.change_expression(item)
            time.sleep(5)
            print(item)

        print("Interaction complete!")
        return False


if __name__ == "__main__":
    import sys
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    app = WhisperNaoApp(robot_ip)
    robotConnected = True
    while robotConnected:
        robotConnected = app.run_pipeline()

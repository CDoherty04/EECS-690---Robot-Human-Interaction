import os
import time
import qi
from openai import OpenAI
from dotenv import load_dotenv
import json

#your .env file needs to be in the parent directory of this script, and contain your OpenAI API key as OPENAI_API_KEY=your_api_key_here
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

#a class to handle OpenAI API interactions, including Whisper for transcription, GPT-5-nano for text generation, and TTS for speech synthesis
class OpenAIHandler:
    def __init__(self):
        self.client = OpenAI()
        system_prompt_path="system_prompt.txt"
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

#a class to encapsulate the entire pipeline of recording, transcribing, generating a response, and playing it back on the robot
class WhisperNaoApp:
    def __init__(self):
        self.times_run = 0
        self.openai_handler = OpenAIHandler()

    #the main pipeline that handles recording user speech, transcribing it, generating a response with GPT, synthesizing speech, and playing it back on the robot
    def run_pipeline(self):
        user_speech = ""
        if self.times_run > 0:
            # 1. Record audio from user (turning eyes green while recording, red when stopped)
            print("Turning eyes green and starting recording...")
            user_speech = input("User Response: ")
            print("Recording stopped. Eyes turned red.")

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


        self.times_run = self.times_run + 1
        if "goodbye" in responseText or "Goodbye" in responseText:
            print("Interaction complete!")
            return False
        else:
            return True



if __name__ == "__main__":
    import sys
    app = WhisperNaoApp()
    robotConnected = True
    while robotConnected:
        robotConnected = app.run_pipeline()

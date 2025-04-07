import os
from pydub import AudioSegment
import speech_recognition as sr

def convert_mp3_to_text(mp3_file_path):
    """
    Converts an MP3 file to text.

    Args:
        mp3_file_path (str): Path to the MP3 file.
    """
    try:
        # Convert MP3 to WAV
        print("Converting MP3 to WAV...")
        audio = AudioSegment.from_mp3(mp3_file_path)
        wav_file_path = "temp.wav"
        audio.export(wav_file_path, format="wav")

        # Recognize speech from the WAV file
        print("Processing WAV file...")
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            print("Transcription:\n", text)

        # Clean up temporary file
        os.remove(wav_file_path)

        return text
        
    except FileNotFoundError:
        print("The specified MP3 file was not found.")
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results: {e}")
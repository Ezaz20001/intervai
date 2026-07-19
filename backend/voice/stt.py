import io
from typing import Optional

import speech_recognition as sr


def transcribe_audio_file(audio_path: str, language: str = "en-US") -> Optional[str]:
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language=language)
    except (sr.UnknownValueError, sr.RequestError):
        return None


def transcribe_audio_data(audio_bytes: bytes, language: str = "en-US") -> Optional[str]:
    recognizer = sr.Recognizer()
    with io.BytesIO(audio_bytes) as buf:
        with sr.AudioFile(buf) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language=language)
    except (sr.UnknownValueError, sr.RequestError):
        return None

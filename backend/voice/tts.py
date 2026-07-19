import io
from typing import Optional

from gtts import gTTS


def text_to_speech(text: str, lang: str = "en", slow: bool = False) -> bytes:
    tts = gTTS(text=text, lang=lang, slow=slow)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


def save_speech_file(text: str, output_path: str, lang: str = "en") -> str:
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)
    return output_path

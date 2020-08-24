import speech_recognition as sr


def recognize(audio_filepath, durations):
    texts = []
    r = sr.Recognizer()
    with sr.AudioFile('audio.wav') as source:
        for duration in durations:
            try:
                audio = r.record(source, duration=duration)
                texts.append(r.recognize_google(audio))
            except Exception:
                texts.append('')
    return texts

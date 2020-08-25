import speech_recognition as sr


def recognize(audio_filenames, durations):
    texts = []
    r = sr.Recognizer()
    for audio_filename, duration in zip(audio_filenames, durations):
        with sr.AudioFile(audio_filename) as source:
            try:
                audio = r.record(source)
                texts.append(r.recognize_google(audio))
            except sr.UnknownValueError:
                texts.append('')
    return texts

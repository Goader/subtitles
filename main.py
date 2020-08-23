import speech_recognition as sr

r = sr.Recognizer()
with sr.AudioFile('samples/harvard.wav') as source:
    audio = r.record(source)

text = r.recognize_google(audio)

print(text)

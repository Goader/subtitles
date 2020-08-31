from scipy.io import wavfile
import webrtcvad
import speech_recognition as sr
import numpy as np


class Frame(object):
    def __init__(self, record, timestamp):
        self.record = record
        self.timestamp = timestamp


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


def stereo_to_mono(audiodata):
    newaudiodata = np.zeros(len(audiodata), dtype='int16')

    for i, record in enumerate(audiodata):
        new = (record[0] + record[1]) / 2
        newaudiodata[i] = new

    return newaudiodata


def frame_generator(audio, sample_rate, frame_duration):
    n = int(sample_rate * (frame_duration / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate)
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp)
        timestamp += duration
        offset += n


def no_voice_intervals(vad, audio, rate, frame_duration):
    no_voice = []
    t_start = None
    for frame in frame_generator(audio, rate, frame_duration):
        if vad.is_speech(frame.record, rate):
            if t_start is not None:
                no_voice.append((t_start, frame.timestamp))
                t_start = None
        else:
            if t_start is None:
                t_start = frame.timestamp

    return np.array(no_voice)


def _get_durations(no_voice, end, duration):
    assert duration > 2.0
    durations = []
    last_start = 0.0
    closest_left = closest_right = None
    previous_interval = None
    for interval in no_voice:
        if previous_interval is not None:
            closest_left = previous = (previous_interval[0] + previous_interval[1]) / 2
        middle = (interval[0] + interval[1]) / 2
        if interval[1] <= last_start + duration:
            closest_left = middle
        elif interval[0] <= last_start + duration:
            closest_left = closest_right = None
            durations.append(middle - last_start)
            last_start = middle
            continue
        else:
            closest_right = middle

        if closest_right is not None:
            if closest_left is None or \
                    (closest_right + closest_left) / 2 > last_start + duration or \
                    closest_left - last_start < 1.5:

                durations.append(closest_right - last_start)
                last_start = closest_right
                previous_interval = None
            else:
                durations.append(closest_left - last_start)
                last_start = closest_left
                previous_interval = interval
            closest_left = closest_right = None

    durations.append(end - last_start)

    return durations


def get_durations(clip, agrs=1, duration=4, frame_duration=10):
    audio = clip.audio
    audio.write_audiofile('temp/audio.wav', fps=48000, nbytes=2, codec='pcm_s16le')

    sample_rate, audiodata = wavfile.read('temp/audio.wav')
    from video_proc import cleanup
    cleanup('temp/audio.wav')
    audiodata = stereo_to_mono(audiodata)

    vad = webrtcvad.Vad(agrs)

    no_voice = no_voice_intervals(vad, audiodata, sample_rate, frame_duration)
    durations = _get_durations(no_voice, clip.duration, duration)
    return durations

from scipy.io import wavfile
import webrtcvad
import speech_recognition as sr
import numpy as np


class Frame(object):
    """
    Data structure for holding audio bytes and time
    at which this interval is played in the original audio
    """
    def __init__(self, record, timestamp):
        self.record = record
        self.timestamp = timestamp


def recognize(audio_filenames):
    """
    Uses speech_recognition package to process
    the passed list of WAV files
    :param audio_filenames: List of audio filenames
    :return: List containing subtitles in corresponding order
    """
    texts = []
    r = sr.Recognizer()
    for audio_filename in audio_filenames:
        with sr.AudioFile(audio_filename) as source:
            try:
                audio = r.record(source)
                texts.append(r.recognize_google(audio))
            # sr.UnknownValueError is raised if the neural net couldn't
            # recognize the provided speech, so then we add empty string
            except sr.UnknownValueError:
                texts.append('')
    return texts


def stereo_to_mono(audiodata):
    """
    Converts scipy's stereo data to mono
    by finding the mean of 2 channels
    :param audiodata: n x 2 scipy's audio data array
    :return: Mono audio data array
    """
    newaudiodata = np.zeros(len(audiodata), dtype='int16')

    for i, record in enumerate(audiodata):
        new = (record[0] + record[1]) / 2
        newaudiodata[i] = new

    return newaudiodata


def frame_generator(audio, sample_rate, frame_duration):
    """
    Generates frames of given durations for VAD
    detection algorithm
    :param audio: Mono WAV audio
    :param sample_rate: Bitrate of the sample
    :param frame_duration: Duration of one frame
    :return: Yields Frame instances
    """
    n = int(sample_rate * (frame_duration / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate)
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp)
        timestamp += duration
        offset += n


def no_voice_intervals(vad, audio, rate, frame_duration):
    """
    Processes the passed audio using Voice Activity Detection
    Creates the no_voice list containing 'quiet' intervals:
    the interval of audio which algorithm classifies as
    'silence/noise'
    :param vad: webrtcvad.Vad() instance
    :param audio: Mono WAV audio
    :param rate: Bitrate of the audio
    :param frame_duration: Duration of one frame
    :return: Array of 'quiet' intervals
    """
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
    """
    Processes 'quiet' intervals, generates close to optimal 'duration'
    intervals with speech. At default duration is set to 4, so
    function tries to stay as close to 4 seconds as it can,
    but it has bottom constraint of 1.5 seconds, so
    the 'duration' parameter cannot be set to 2.0 and less
    :param no_voice: 'Quiet' intervals returned by no_voice_intervals function
    :param end: The end of video timestamp
    :param duration: Optimal duration of the interval containing speech
    :return: Durations of the pieces containing speech in order
    """
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


def divide_by_speech(audio):
    """
    Tries do divide one particular audio interval into
    more by checking for speech via speech_recognition tool
    :param audio: AudioClip of duration > 2.5 * opt_duration
    :return: List of new durations after dividing this one
    """
    margin = 2
    offset = margin
    last_start = 0
    durations = []
    while offset + margin <= audio.duration:
        filename = f'temp/d{offset}.wav'
        audio.subclip(offset, offset+2).\
            write_audiofile(filename, codec='pcm_s16le')
        if not recognize([filename])[0]:  # returns list, passing single filename -> single string
            durations.append(offset+1 - last_start)
            last_start = offset+1
            offset = last_start + margin
        else:
            offset += 1
    if last_start < audio.duration:
        durations.append(audio.duration - last_start)
    return durations


def extra_division(audio, durations, opt_duration):
    """
    Creates new list of durations by checking if long
    intervals contain speech using speech_recognition tool
    :param audio: AudioClip extracted from the original video
    :param durations: Current list of durations based on VAD
    :param opt_duration: Optimal duration of the interval containing speech
    :return: Edited list of durations
    """
    offset = 0
    new_durations = []
    for duration in durations:
        if duration > 2.5 * opt_duration:
            extra_durations = divide_by_speech(audio.subclip(offset, offset+duration))
            new_durations.extend(extra_durations)
        else:
            new_durations.append(duration)
        offset += duration
    return new_durations


def get_durations(clip, agrs=1, opt_duration=4, frame_duration=10):
    """
    Extracts audio from clip, writes it using needed parameters
    to satisfy Vad() functions, then generates list of durations
    :param clip: The initial VideoClip instance
    :param agrs: The aggressiveness of the Vad() instance
    :param opt_duration: Optimal duration of the interval containing speech
    :param frame_duration: Duration of one frame
    :return: List of durations (intervals) containing speech
    """
    audio = clip.audio
    audio.write_audiofile('temp/audio.wav', fps=48000, nbytes=2, codec='pcm_s16le')

    sample_rate, audiodata = wavfile.read('temp/audio.wav')
    # Used only twice, no need to foul the namespace
    from video_proc import cleanup
    cleanup('temp/audio.wav')
    audiodata = stereo_to_mono(audiodata)

    vad = webrtcvad.Vad(agrs)

    no_voice = no_voice_intervals(vad, audiodata, sample_rate, frame_duration)
    durations = _get_durations(no_voice, clip.duration, opt_duration)
    durations = extra_division(clip.audio, durations, opt_duration)
    cleanup()
    return durations

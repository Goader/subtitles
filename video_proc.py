from recognizer import recognize
from PIL import Image, ImageDraw, ImageFont
from math import ceil
import moviepy.editor as mp
import numpy as np


# returns filepath to .wav file
def extract_audio(clip):
    audio = clip.audio
    audio.write_audiofile('audio.wav', codec='pcm_s16le')  # this codec stands for 32-bit WAV
    return 'audio.wav'


# returns ImageClip instance
def draw_overlay(text, size, font, duration):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay = ImageDraw.Draw(img)

    text_w, text_h = overlay.textsize(text, font)
    w, h = size
    coords = ((w-text_w) // 2, (h//30) * 27)

    overlay.rectangle((coords, (coords[0]+text_w, coords[1]+text_h)), fill=(0, 0, 0, 230))
    overlay.text(coords, text, fill=(255, 255, 255, 255), font=font)
    img.save('tmp.png')
    # img = np.array(img.getdata())
    # img = np.reshape(img, (size[0], size[1], 4))

    return mp.ImageClip('tmp.png', duration=duration)


# returns VideoClip that holds the same text frame
def add_overlay(clip, text, font):
    img_clip = draw_overlay(text, clip.size, font, clip.duration)

    clip = mp.CompositeVideoClip([clip, img_clip])
    return clip


# return the final version of VideoClip
def draw_subtitles(clip, audio_filepath, duration=4):
    font = ImageFont.truetype(r'..\fonts\arial.ttf', size=clip.size[1]//30)

    durations = []
    for start in range(0, ceil(clip.duration), duration):
        end = start + duration if start + duration < clip.duration else clip.duration

        durations.append(end - start)

    subtitles = recognize(audio_filepath, durations)

    clips = []
    for start, text in zip(range(0, ceil(clip.duration), duration), subtitles):
        end = start + duration if start + duration < clip.duration else clip.duration

        subclip = clip.subclip(start, end)
        clips.append(add_overlay(subclip, text, font))

    clip = mp.concatenate_videoclips(clips)
    return clip

from recognizer import recognize, get_durations
from PIL import Image, ImageDraw, ImageFont
from math import ceil
import moviepy.editor as mp
import os


# returns filepath to .wav file
def extract_audio(clip, durations):
    audio = clip.audio
    audio_filenames = []
    start = 0
    for duration in durations:
        # 'pdm_s16le' codec stands for 16-bit WAV
        audio.subclip(start, start + duration).write_audiofile(f'temp/{start}.wav', codec='pcm_s16le')
        audio_filenames.append(f'temp/{start}.wav')
        start += duration

    return audio_filenames


def divide_text(text, w, text_w):
    coef = int(text_w // (0.8 * w)) + 1

    # despite possibility, expected no more than 3 lines
    for i in range(1, coef):
        idx = text[i * (len(text)//coef):].find(' ') + i * (len(text)//coef)
        text = text[:idx] + '\n' + text[idx+1:]
    return text


# returns transparent ImageClip instance with subtitles added
def draw_overlay(text, size, font, duration):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay = ImageDraw.Draw(img)

    w, h = size
    text_w, text_h = overlay.textsize(text, font)
    too_high = False
    if text_w > 0.8 * w:
        text = divide_text(text, w, text_w)
        if text_w > 1.6 * w:
            too_high = True
    text_w, text_h = overlay.multiline_textsize(text, font)
    if not too_high:
        coords = ((w-text_w) // 2, (h//30) * 27)
    else:
        coords = ((w-text_w) // 2, ((h - text_h)//30) * 29)

    overlay.rectangle((coords, (coords[0]+text_w, coords[1]+text_h)), fill=(0, 0, 0, 230))
    overlay.multiline_text(coords, text, fill=(255, 255, 255, 255), font=font, align='center')

    img.save('temp/text.png')
    return mp.ImageClip('temp/text.png', duration=duration)


# returns VideoClip that holds the same text frame
def add_overlay(clip, text, font):
    if not text:  # clips with empty subtitles don't need any changes
        return clip
    img_clip = draw_overlay(text, clip.size, font, clip.duration)

    return mp.CompositeVideoClip([clip, img_clip]).set_duration(clip.duration)


# returns the final version of VideoClip
def draw_subtitles(clip):
    # Creates temp directory for storing temporary files
    if not os.path.exists('temp'):
        os.mkdir('temp')
    else:
        cleanup()
    font = ImageFont.truetype('fonts/arial.ttf', size=clip.size[1]//30)

    durations = get_durations(clip)

    audio_filenames = extract_audio(clip, durations)
    subtitles = recognize(audio_filenames, durations)
    cleanup()

    clips = []
    start = 0
    for duration, text in zip(durations, subtitles):
        end = start + duration if start + duration < clip.duration else clip.duration

        subclip = clip.subclip(start, end)
        clips.append(add_overlay(subclip, text, font))

        start += duration

    clip = mp.concatenate_videoclips(clips)
    cleanup('text.png')
    if os.path.exists('temp'):
        os.rmdir('temp')
    return clip


def cleanup(*args):
    if not os.path.exists('temp'):
        return

    if args:
        files = args
    else:
        files = os.listdir('temp')  # all temporary files created in temp/ directory

    for filename in files:
        if os.path.exists(f'temp/{filename}'):
            os.remove(f'temp/{filename}')

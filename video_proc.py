from recognizer import recognize, get_durations
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp
import os


def extract_audio(clip, durations):
    """
    Given durations list extracts the clip's audio and
    divides it into pieces of given durations
    All the pieces are then written as 16-bit WAV files
    :param clip: The initial VideoClip instance
    :param durations: Durations for audios
    :return: A list of generated audio_filenames
    """
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
    """
    Divides text to follow the described below '4/5 of width' criteria
    :param text: Text to be divided
    :param w: Width of the video
    :param text_w: Expected width of the text in the 1-line form
    :return: Divided text by replacing empty spaces with '\n'
    """
    coef = int(text_w // (0.8 * w)) + 1  # how many lines will be created

    # despite possibility, expected no more than 3 lines
    for i in range(1, coef):
        idx = text[i * (len(text)//coef):].find(' ') + i * (len(text)//coef)
        text = text[:idx] + '\n' + text[idx+1:]
    return text


def draw_overlay(text, size, font, duration):
    """
    For given text and video size generates ImageClip
    containing the passed text
    :param text: Text to be drawn
    :param size: Size of the VideoClip
    :param font: Font for the text
    :param duration: Duration of the VideoClip
    :return: Transparent ImageClip instance with subtitles added
    """
    # Fully transparent RGBA image
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay = ImageDraw.Draw(img)

    w, h = size
    text_w, text_h = overlay.textsize(text, font)
    too_high = False
    """
    If the text frame is expected to take over 4/5 of the video's width,
    it is then divided in 2 lines, if it takes more than 4/5 even being
    divided, it creates more lines until it satisfies '4/5 of width' criteria
    
    1/2-liners are placed at the 27/30 of the video height, more lines 
    get out of bounds, so their position is calculated taking their 
    expected height into consideration
    """
    if text_w > 0.8 * w:
        text = divide_text(text, w, text_w)
        if text_w > 1.6 * w:
            too_high = True
    text_w, text_h = overlay.multiline_textsize(text, font)
    if not too_high:
        coords = ((w-text_w) // 2, (h//30) * 27)
    else:
        coords = ((w-text_w) // 2, ((h - text_h)//30) * 29)

    # The black rectangle behind the text to provide contrast and visibility at any background
    overlay.rectangle((coords, (coords[0]+text_w, coords[1]+text_h+5)), fill=(0, 0, 0, 230))
    overlay.multiline_text(coords, text, fill=(255, 255, 255, 255), font=font, align='center')

    img.save('temp/text.png')
    return mp.ImageClip('temp/text.png', duration=duration)


def add_overlay(clip, text, font):
    """
    Adds overlay with text frame over initial clip passed
    :param clip: VideoFile instance that has the same text for its duration
    :param text: The text defined for this clip
    :param font: Font for the text
    :return: VideoClip that holds the same text frame
    """
    if not text:  # clips with empty subtitles don't need any changes
        return clip
    img_clip = draw_overlay(text, clip.size, font, clip.duration)

    return mp.CompositeVideoClip([clip, img_clip]).set_duration(clip.duration)


def draw_subtitles(clip):
    """
    Main subtitles drawing function
    Responds for sound division, recognizing and drawing
    :param clip: VideoFile instance containing initial video
    :return: the final version of VideoClip
    """
    # Creates temp directory for storing temporary files
    if not os.path.exists('temp'):
        os.mkdir('temp')
    else:
        cleanup()
    # This program uses Arial font for drawing subtitles, can be used anything else
    font = ImageFont.truetype('fonts/arial.ttf', size=clip.size[1]//30)

    # Gets a sequence of durations after finding close to optimal sound division
    durations = get_durations(clip)

    # Writes audio files for previously specified durations to be then
    # processed via speech_recognition package
    audio_filenames = extract_audio(clip, durations)
    subtitles = recognize(audio_filenames)  # text for corresponding duration
    cleanup()

    clips = []
    start = 0
    # Creates distinct clips for each duration and concatenates them
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
    """
    Removes all the temporary files in previously created temp/ directory
    If no parameters are passed: all the files
    Else all the filenames passed are removed
    :param args:
    :return:
    """
    if not os.path.exists('temp'):
        return

    if args:
        files = args
    else:
        files = os.listdir('temp')  # all temporary files created in temp/ directory

    for filename in files:
        if os.path.exists(f'temp/{filename}'):
            os.remove(f'temp/{filename}')

from video_proc import extract_audio, draw_subtitles
from moviepy.editor import VideoFileClip
import os


if __name__ == '__main__':
    audio_filepath = None
    try:
        filename = input('Enter filepath:\t\t')
        output_filename = input('Enter final name:\t')
        clip = VideoFileClip(filename)
        if clip.size[0] < 256 or clip.size[1] < 144:
            raise ValueError('Too small resolution. Must be: height >= 144, width >= 256')

        audio_filepath = extract_audio(clip)

        clip = draw_subtitles(clip, audio_filepath)
        # clip = draw_subtitles(clip, None, r)

        clip.write_videofile(output_filename, codec='png', threads=6)

        os.remove(audio_filepath)
    except KeyboardInterrupt:
        if audio_filepath is not None and os.path.exists(audio_filepath):
            os.remove(audio_filepath)

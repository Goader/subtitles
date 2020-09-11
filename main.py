from video_proc import draw_subtitles, cleanup
from moviepy.editor import VideoFileClip
import os

"""
Python console program to draw subtitles for a video
based on its audio. Mainly uses MoviePy for video editing,
speech_recognition package for extracting text from audio
and WebRTC's VAD (Voice Activity Detection) to define the
close to optimal division for audio to be processed.

Input video should be at least 256x144, output video is in
.avi format. Threads parameter is set due to author's laptop.
"""

if __name__ == '__main__':
    try:
        filename = input('Enter filepath:\t\t')
        output_filename = input('Enter final name:\t')
        if not os.path.exists(filename):
            raise ValueError('Given path does not exist')
        clip = VideoFileClip(filename)
        if clip.size[0] < 256 or clip.size[1] < 144:
            raise ValueError('Too small resolution. Must be: height >= 144, width >= 256')

        clip = draw_subtitles(clip)

        clip.write_videofile(output_filename, codec='png', threads=12)  # this codec stands for .avi files
    except KeyboardInterrupt:
        cleanup()
        if os.path.exists('temp'):
            os.rmdir('temp')

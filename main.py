from video_proc import draw_subtitles, cleanup
from moviepy.editor import VideoFileClip
import os


if __name__ == '__main__':
    try:
        filename = input('Enter filepath:\t\t')
        output_filename = input('Enter final name:\t')
        clip = VideoFileClip(filename)
        if clip.size[0] < 256 or clip.size[1] < 144:
            raise ValueError('Too small resolution. Must be: height >= 144, width >= 256')

        clip = draw_subtitles(clip)

        clip.write_videofile(output_filename, codec='png', threads=12)  # this codec stands for .avi files
    except KeyboardInterrupt:
        cleanup()
        if os.path.exists('temp'):
            os.rmdir('temp')

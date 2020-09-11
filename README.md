# Subtitles Drawing
Python console program to draw subtitles for a video
based on its audio. Mainly uses MoviePy for video editing,
speech_recognition package for extracting text from audio
and WebRTC's VAD (Voice Activity Detection) to define the
close to optimal division for audio to be processed.

Input video should be at least 256x144, output video is in
.avi format. Threads parameter is set as for author's laptop.

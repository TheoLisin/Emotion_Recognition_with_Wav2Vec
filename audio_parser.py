import os
import librosa
import subprocess


def ogg_to_wav(name, new_sr=16000, temp_path=None):
    ogg_name = name + ".ogg"
    wav_name = name + ".wav"
    subprocess.run(['ffmpeg', "-i", ogg_name, wav_name])
    file, sr = librosa.load(wav_name, new_sr)

    os.remove(ogg_name)
    os.remove(wav_name)

    return file, sr

# ogg_file = AudioSegment.from_ogg("voice.ogg")
# ogg_file = ffmpeg.
# wav_file = ffmpeg.output()

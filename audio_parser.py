import os
import subprocess


def save_wav(name, new_sr=16000):
    ogg_name = name + ".ogg"
    wav_name = name + ".wav"
    subprocess.run(['ffmpeg', "-i", ogg_name, wav_name])
    dsac
    os.remove(ogg_name)


if __name__ == "__main__":
    pass

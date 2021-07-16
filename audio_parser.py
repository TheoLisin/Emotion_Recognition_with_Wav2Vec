import os
import subprocess
import librosa
import noisereduce as nr
import numpy as np


def save_wav(name, new_sr=16000):
    ogg_name = name + ".ogg"
    wav_name = name + ".wav"
    subprocess.run(['ffmpeg', "-i", ogg_name, wav_name])
    os.remove(ogg_name)


def ogg_to_wav(name, new_sr=16000):
    ogg_name = name + ".ogg"
    wav_name = name + ".wav"
    subprocess.run(['ffmpeg', "-i", ogg_name, wav_name])
    audio, sr = librosa.load(wav_name, new_sr)

    os.remove(ogg_name)
    os.remove(wav_name)

    return audio, sr


def denoise_transformer(audio):
    return nr.reduce_noise(audio, audio)


def splitter(audio, sr=16000):
    disc_len = len(audio)
    length_sec = disc_len / sr
    split_len = int(length_sec / max(int(length_sec / 4), 1) * 16000)
    batches = [audio[i:i+split_len]
               for i in range(0, disc_len, split_len)]
    return np.array(batches)


if __name__ == "__main__":
    pass

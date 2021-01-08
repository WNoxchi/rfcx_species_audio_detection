# AUTOGENERATED! DO NOT EDIT! File to edit: 01_spectrogram_processor.ipynb (unless otherwise specified).

__all__ = ['parser', 'args', 'fpath', 'num_cpus', 'serial', 'n_fft', 'hop_length', 'n_mels', 'mel_n_fft',
           'mel_hop_length', 'frq', 'mel', 'compute_spectrogram', 'compute_mel_spectrogram', 'write_spectrogram',
           'load_compute_write', 'spgmtext', 'cputext', 't', 'path', 'path_spgm_frq', 'path_spgm_mel', 'audio_files']

# Cell
import argparse
from pathlib import Path
import json
import librosa
import numpy as np
from PIL import Image
import time
from fastprogress import progress_bar
from os import uname
from fastcore.parallel import parallel
from fastcore.parallel import num_cpus

# Cell
# ignore librosa pysoundfile load warning
import warnings
warnings.filterwarnings(
    action='ignore',
    category=UserWarning,
    module=r'librosa'
)

# Cell
parser = argparse.ArgumentParser()
parser.add_argument("--path", help="parameter filepath", nargs=1)
args = parser.parse_args()
# args = parser.parse_args(["--path", "sample parameters.json"]) # ← for testing

# Cell
fpath = Path(args.path[0])
assert fpath.exists(), (f"Filepath '{fpath}' not found.")
assert fpath.is_file(), (f"'{fpath}' is not a valid file.")

# Cell
with open(fpath, 'r') as file:
    parameters = json.load(file)
    print(f"Parameters file \"{fpath}\" loaded.")

# Cell
num_cpus = num_cpus() # func → int
serial = True if uname().sysname.lower() != 'linux' else parameters['serial'] # no parallelization support on MacOS or Windows

n_fft = parameters['n_fft']
hop_length = parameters['hop_length']
n_mels = parameters['n_mels']

mel_n_fft = parameters['mel_n_fft_override']
if mel_n_fft == None: mel_n_fft = n_fft

mel_hop_length = parameters['mel_hop_length_override']
if mel_hop_length == None: mel_hop_length = hop_length

if n_fft / n_mels < 2**3:
    print(f"Warning: N FFT ({n_fft}) is fewer than 3 powers of 2 greater than N Mels ({n_mels})."
          f" This may result in null values at lower mels in spectrograms.")

frq = parameters['frq']
mel = parameters['mel']

# Cell
def compute_spectrogram(wf, n_fft=1024, hop_length=512):
    return librosa.power_to_db(np.abs(librosa.stft(wf, n_fft=n_fft, hop_length=hop_length))**2)

def compute_mel_spectrogram(wf, sr=None, n_fft=1024, hop_length=512, n_mels=128):
    return librosa.power_to_db(librosa.feature.melspectrogram(wf, sr=sr, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels))

def write_spectrogram(spgm, filepath):
    # convert fp32 array to 0-255 UInt8.
    shift = abs(spgm.min()) if spgm.min() < 0 else 0.0
    x = ((spgm + shift) * (255/(shift + spgm.max())))
    img = Image.fromarray(x.round().astype(np.uint8)[::-1]) # vertical flip
    img.save(filepath)

# Cell
def load_compute_write(audio_file, diagnostic_suffix="", frq=True, mel=True, **kwargs):
    """
    For parallelization.
    """
    wf,sr = librosa.load(audio_file, sr=None)
    spgm_frq = compute_spectrogram(wf, n_fft=n_fft, hop_length=hop_length)
    spgm_mel = compute_mel_spectrogram(wf, sr=sr, n_fft=mel_n_fft, hop_length=mel_hop_length, n_mels=n_mels)
    if frq: write_spectrogram(spgm_frq, path_spgm_frq/f"{audio_file.stem}{diagnostic_suffix}.png")
    if mel: write_spectrogram(spgm_mel, path_spgm_mel/f"{audio_file.stem}{diagnostic_suffix}.png")
#     return {'audio_file':audio_file.stem,'spgm_frq':spgm_frq,'spgm_mel':spgm_mel}

# Cell
spgmtext = f"Spectrograms: {['','FRQ'][frq]}{['',', '][frq and mel]}{['','MEL'][mel]}"
cputext = [f" with {num_cpus} core{['','s'][num_cpus>1]}",""][serial]
print(f"Parallelization {['ON','OFF'][serial]}{cputext}. {spgmtext}")

# Cell
t = time.time()

# Cell
path = Path(parameters['path'])
path_spgm_frq = path/'spectrogram_frq'
path_spgm_frq.mkdir(parents=True, exist_ok=True)
path_spgm_mel = path/'spectrogram_mel'
path_spgm_mel.mkdir(parents=True, exist_ok=True)

# get list of audio files
audio_files = []
for audio_folder in parameters['audio_folders']:
    audio_path = path/audio_folder
    audio_files += [file for file in audio_path.iterdir() if file.suffix in parameters['codecs']]

# load waveform
if serial:
    pb = progress_bar(audio_files)
    for audio_file in pb:
        pb.comment = f"processing: {audio_file.parent.name}/{audio_file.name}"
        wf,sr = librosa.load(audio_file, sr=None)
        # compute freq & mel spectrograms
        spgm_frq = compute_spectrogram(wf, n_fft=n_fft, hop_length=hop_length)
        spgm_mel = compute_mel_spectrogram(wf, sr=sr, n_fft=mel_n_fft, hop_length=mel_hop_length, n_mels=n_mels)
        # write spectrograms
        if frq: write_spectrogram(spgm_frq, path_spgm_frq/f"{audio_file.stem}.png")
        if mel: write_spectrogram(spgm_mel, path_spgm_mel/f"{audio_file.stem}.png")
else:
    _ = parallel(load_compute_write, audio_files, frq, mel,
            **{'n_fft':n_fft,'hop_length':hop_length,'n_mels':n_mels}, threadpool=True, n_workers = num_cpus)

# Cell
print(f"\n{len(audio_files)} files processed in {time.strftime('%H:%M:%S', time.gmtime(time.time() - t))}")
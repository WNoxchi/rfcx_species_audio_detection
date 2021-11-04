# [Species Audio Detection](https://www.kaggle.com/c/rfcx-species-audio-detection/overview)

This repository reimplements the [2nd place solution](https://www.kaggle.com/c/rfcx-species-audio-detection/discussion/220760) to the [Kaggle Species Audio Detection competition](https://www.kaggle.com/c/rfcx-species-audio-detection/overview) which ran in 2021.

The task is to detect the presence of any of 24 animal species in audio files recorded by remote microphones in a rainforest. This is a multilabel classification problem on audio data. The data itself consists of 1D amplitude waveforms and a CSV file of labels with timestamps.

## How this repository works

This repository currently doesn't do batch spectrogram processing. Instead it precomputes all spectrograms in the dataset. `01_spectrogram_processor.ipynb` builds the `spectrogram_processor.py` command-line script which takes a path to a `parameters.json` config file.

## Repository Status

Solution is under development.

**Spectrogram processing**
* serial: OK
* parallel: TODO

There are currently system errors when loading audio files in parallel on some systems.


## Reference Solution

The 2nd place solution uses an ensemble of two architectures, [EfficientNet](https://www.youtube.com/watch?v=3svIm5UC94I) and [ReXNet](https://arxiv.org/abs/2007.00992), and relatively straight-forward tuning parameters. A frequency convolution channel, pseudolabeling, and ensemble lead to observed performance.

### MelSpectrogram
* 256 melody bins
* 512 hop length
* unaltered sample rate (48 kHz)
* 4096 NFFT

### Frequency Convolution

FreqConv is a [Coordinate Convolution](https://paperswithcode.com/method/coordconv) ([talk](https://www.youtube.com/watch?v=gMGL-shl3P8)/[code](https://github.com/uber-research/CoordConv/blob/27fab8b86efac87c262c7c596a0c384b83c9d806/CoordConv.py#L87)) applied to frequency. It adds an input channel containing the number of melody bins scaled to [0..1].

### First Stage

#### Augmentations
* time warping
* random frequency masking below [TP/FP](https://developers.google.com/machine-learning/crash-course/classification/true-false-positive-negative) signal
* random frequency masking above TP/FP signal
* gaussian noise
* volme gain
* mixup on spectrograms
    * constant α (0.5) and hard labels with clipping (0, 1).
    * masks

### Pseudolabeling Stages

Sample TP/FP with p=05, otherwise make a random crop from the full spectrogram.

#### Augmentations

* gaussian nose
* volume gain
* mixup
* time warping
* [spec augment](https://ai.googleblog.com/2019/04/specaugment-new-data-augmentation.html)
* mixup on spectrograms

#### Mixup

Constant α (0.5) with soft labels from two samples. Slightly diminishes FP logloss, but significantly increases TP recall.

### Validation

The 2nd place solution didn't find a strong link between validation and public leaderboard score. He opted not to use checkpoints and instead tuned 60 epochs (at 200 batches/epoch) with [CosineLR](https://pytorch.org/docs/stable/generated/torch.optim.lr_scheduler.CosineAnnealingLR.html) and the [AdamW optimizer](https://pytorch.org/docs/stable/generated/torch.optim.AdamW.html).

### Ensemble

4 models with 4 folds. EfficientNet and ReXNet chosen for performance/resource.

* ReXNet-200, EffNetB3
* ReXNet-150, EffNetB1

Output predictions use a 0.5 sec sliding window and max probabilities for an audio clip. Predictions are averaged across models.

### Misc: Architectures

[According to the 2nd place solution](https://github.com/uber-research/CoordConv/blob/27fab8b86efac87c262c7c596a0c384b83c9d806/CoordConv.py#L87) ReXNet is a modification of MobileNet with similar performance to EfficientNet. I.e. it's a low-resource architecture.

import numpy as np
import librosa
from typing import Dict
from ..datatypes import AcousticFeatures

class PRISMAudioFeatureExtractor:
    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate

    def extract_features(self, audio: np.ndarray) -> AcousticFeatures:
        if len(audio) == 0:
            return self._empty_features()
            
        # 1. Mel Spectrogram
        mel = librosa.feature.melspectrogram(y=audio, sr=self.sr, n_mels=128)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        
        # 2. MFCCs
        mfcc = librosa.feature.mfcc(y=audio, sr=self.sr, n_mfcc=40)
        mfcc_delta = librosa.feature.delta(mfcc)
        mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
        mfccs_combined = np.vstack([mfcc, mfcc_delta, mfcc_delta2])
        
        # 3. Chroma
        chroma = librosa.feature.chroma_stft(y=audio, sr=self.sr)
        
        # 4. Spectral Features
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=self.sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=self.sr)
        zcr = librosa.feature.zero_crossing_rate(y=audio)
        spectral_flux = np.mean(librosa.onset.onset_strength(y=audio, sr=self.sr))
        
        # 5. Temporal Features
        duration = len(audio) / self.sr
        peak_amp = float(np.max(np.abs(audio)))
        
        return AcousticFeatures(
            mel_spectrogram=mel_db,
            mfcc_features=mfccs_combined,
            chroma_stft=chroma,
            spectral_features=np.vstack([spectral_centroid, spectral_rolloff, spectral_bandwidth, zcr]),
            temporal_features={
                "duration": duration,
                "peak_amplitude": peak_amp,
                "spectral_flux": float(spectral_flux)
            }
        )

    def _empty_features(self) -> AcousticFeatures:
        return AcousticFeatures(
            mel_spectrogram=np.array([]),
            mfcc_features=np.array([]),
            chroma_stft=np.array([]),
            spectral_features=np.array([]),
            temporal_features={}
        )

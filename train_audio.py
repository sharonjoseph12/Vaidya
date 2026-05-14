import os
import glob
import numpy as np
import librosa
import xgboost as xgb
import joblib
import warnings

# Suppress annoying warnings from audio processing
warnings.filterwarnings('ignore')

print("🇮🇳 PRISM AI Initialization: Scanning Coswara Dataset...")

# --- CONFIGURATION ---
DATASET_FOLDER = "./Coswara_Data" 

def get_fingerprint(file_path):
    """Turns audio into 14 mathematical numbers (13 MFCCs + 1 ZCR)"""
    try:
        # Load audio (downsample to 16kHz, max 4 seconds to save RAM)
        y, sr = librosa.load(file_path, sr=16000, duration=4.0) 
        
        # Extract features
        mfccs_mean = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T, axis=0)
        zcr_mean = np.mean(librosa.feature.zero_crossing_rate(y).T, axis=0)
        
        return np.hstack([mfccs_mean, zcr_mean])
    except Exception as e:
        # If an audio file is corrupted, skip it safely
        return None 

# 1. FIND ALL COUGH FILES (Recursive Search)
print("🔍 Digging through nested folders for audio files...")

# Search every single folder inside Coswara_Data
search_pattern = os.path.join(DATASET_FOLDER, "**", "*.wav")
audio_files = glob.glob(search_pattern, recursive=True)

if len(audio_files) == 0:
    print("❌ ERROR: Could not find audio files. Check your folder name!")
    exit()

print(f"✅ Found {len(audio_files)} audio files!")

# 2. EXTRACT FEATURES
features = []
labels = []

# HACKATHON SPEED TRICK: We process exactly 300 files to train fast.
limit = min(300, len(audio_files))
print(f"⚙️ Extracting Acoustic Fingerprints for {limit} files (This will take ~60 seconds)...")

for i, file_path in enumerate(audio_files[:limit]): 
    feat = get_fingerprint(file_path)
    if feat is not None:
        features.append(feat)
        # Hackathon dummy labeling: Alternate Sick (1) and Healthy (0)
        labels.append(1 if i % 2 == 0 else 0) 
        
    # Print progress so you know it hasn't frozen
    if (i + 1) % 50 == 0:
        print(f"   ...Processed {i + 1}/{limit}")

X = np.array(features)
y = np.array(labels)

# 3. TRAIN THE MODEL
print(f" Training XGBoost AI Brain on {len(X)} valid coughs...")
model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)
model.fit(X, y)

# 4. SAVE THE MODEL
joblib.dump(model, "cough_xgboost_model.pkl")
print("====================================================")
print(" SUCCESS! AI Brain saved as 'cough_xgboost_model.pkl'")
print(" AUDIO PHASE COMPLETE. Hand this file to Person 3!")
print("=====================================================")
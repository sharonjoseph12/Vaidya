import os
import glob
import numpy as np
import pandas as pd
import librosa
import xgboost as xgb
import joblib
import warnings
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Suppress annoying warnings from audio processing
warnings.filterwarnings('ignore')

print("🇮🇳 PRISM AI Training: Professional Dataset Processing...")

# --- CONFIGURATION ---
DATASET_FOLDER = os.path.join("prism", "PRISM_Audio_ML", "public_dataset")
MODEL_SAVE_PATH = os.path.join("layer1_sense", "audio", "models", "cough_xgboost_model.pkl")

def get_fingerprint(file_path):
    """Turns audio into 14 mathematical numbers (13 MFCCs + 1 ZCR)"""
    try:
        # Load audio (downsample to 16kHz, max 4 seconds)
        y, sr = librosa.load(file_path, sr=16000, duration=4.0) 
        
        # Skip silent or near-silent files
        if len(y) < 1600 or np.max(np.abs(y)) < 0.01:
            return None
        
        # Extract features
        mfccs_mean = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T, axis=0)
        zcr_mean = np.mean(librosa.feature.zero_crossing_rate(y).T, axis=0)
        
        return np.hstack([mfccs_mean, zcr_mean])
    except Exception:
        return None 

# 1. LOAD METADATA
metadata_path = os.path.join(DATASET_FOLDER, "metadata_compiled.csv")
if not os.path.exists(metadata_path):
    print("❌ ERROR: metadata_compiled.csv not found!")
    exit()

print("📋 Loading metadata...")
meta_df = pd.read_csv(metadata_path)
label_map = {}
for _, row in meta_df.iterrows():
    uuid = str(row.get("uuid", ""))
    status = str(row.get("status", "")).lower().strip()
    if status in ("healthy", "health"):
        label_map[uuid] = 0
    elif status in ("symptomatic", "covid-19", "covid_positive"):
        label_map[uuid] = 1

# 2. SCAN FILES
print("🔍 Scanning for audio files...")
audio_files = glob.glob(os.path.join(DATASET_FOLDER, "**", "*.wav"), recursive=True)
if not audio_files:
    print("❌ ERROR: No .wav files found!")
    exit()

# 3. FEATURE EXTRACTION
# Let's increase to 2000 for a more robust model during this phase
limit = min(2000, len(audio_files)) 
print(f"⚙️ Extracting features for {limit} files (may take a few minutes)...")

features = []
labels = []
processed = 0

for i, file_path in enumerate(audio_files[:limit]): 
    basename = os.path.splitext(os.path.basename(file_path))[0]
    label = label_map.get(basename)
    
    if label is not None:
        feat = get_fingerprint(file_path)
        if feat is not None:
            features.append(feat)
            labels.append(label)
            processed += 1
            
    if (i + 1) % 100 == 0:
        print(f"   ...Checked {i + 1}/{limit} (valid: {processed})")

X = np.array(features)
y = np.array(labels)

print(f"\n📊 Final Dataset: {len(X)} samples (Healthy: {np.sum(y == 0)}, Sick: {np.sum(y == 1)})")

# 4. TRAIN/TEST SPLIT
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. TRAIN MODEL WITH CLASS WEIGHTING
print("🧠 Training XGBoost (High Sensitivity Mode)...")
# Calculate scale_pos_weight to handle imbalance (Healthy:Sick ratio)
ratio = np.sum(y == 0) / np.sum(y == 1)
print(f"   Using scale_pos_weight={ratio:.2f} to prioritize Sick detection")

model = xgb.XGBClassifier(
    n_estimators=100, 
    max_depth=5, 
    learning_rate=0.1, 
    eval_metric='logloss',
    scale_pos_weight=ratio # Increases penalty for missing 'Sick' samples
)
model.fit(X_train, y_train)

# 6. EVALUATE
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"✅ Training Complete. Validation Accuracy: {acc:.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# 7. SAVE
os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
joblib.dump(model, MODEL_SAVE_PATH)
# Also save a copy in the root as requested by previous steps
joblib.dump(model, "cough_xgboost_model.pkl")

print(f"\n💾 Model saved to: {MODEL_SAVE_PATH}")
print("🚀 Ready for integration into PRISMCoughClassifier!")
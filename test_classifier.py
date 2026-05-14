import os
import sys
import librosa
import numpy as np

# Add the current directory to path so we can import layer1_sense
sys.path.append(os.getcwd())

from layer1_sense.audio.cough_classifier import PRISMCoughClassifier

def run_test():
    print("🧪 PRISM Classifier Verification Test")
    print("======================================")
    
    # 1. Initialize Classifier
    # It will automatically find the model in layer1_sense/audio/models/
    classifier = PRISMCoughClassifier()
    
    # 2. Test Files
    test_files = [
        r"prism\PRISM_Audio_ML\public_dataset\00014dcc-0f06-4c27-8c7b-737b18a2cf4c.wav",
        r"prism\PRISM_Audio_ML\public_dataset\00039425-7f3a-42aa-ac13-834aaa2b6b92.wav",
        r"prism\PRISM_Audio_ML\public_dataset\0007c6f1-5441-40e6-9aaf-a761d8f2da3b.wav"
    ]
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  Skipping missing file: {file_path}")
            continue
            
        print(f"\n🎧 Testing: {os.path.basename(file_path)}")
        
        try:
            # Load audio
            waveform, sr = librosa.load(file_path, sr=16000)
            
            # Predict
            # Classifier expects a list of segments
            results = classifier.predict([waveform])
            
            # Print results
            print(f"   Healthy Prob: {results['healthy_prob']:.4f}")
            print(f"   Sick Prob:    {results['sick_prob']:.4f}")
            
            if results['sick_prob'] > 0.5:
                print("   🚩 Result: SYMPTOMATIC DETECTED")
            else:
                print("   ✅ Result: HEALTHY")
                
        except Exception as e:
            print(f"   ❌ Error processing file: {e}")

if __name__ == "__main__":
    run_test()

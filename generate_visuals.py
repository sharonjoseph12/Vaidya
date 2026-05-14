import joblib
import xgboost as xgb
import matplotlib.pyplot as plt

print("📊 Generating Clinical Biomarker Importance Chart...")

# Load your trained AI brain
model = joblib.load("cough_xgboost_model.pkl")

# Plot which audio features the AI thinks are most important
fig, ax = plt.subplots(figsize=(10, 6))
xgb.plot_importance(model, ax=ax, importance_type='weight', max_num_features=10, color='#00F0FF')

# Make it look "Cyber-Medical" for the presentation
plt.style.use('dark_background')
fig.patch.set_facecolor('#0B0E14')
ax.set_facecolor('#0B0E14')
plt.title("Acoustic Biomarker Importance (MFCC & ZCR)", color='white', fontsize=16)
plt.ylabel("Acoustic Feature (MFCC bins)", color='white')
plt.xlabel("F-Score (Clinical Weight)", color='white')

# Save the chart as an image
plt.savefig("biomarker_importance.png", bbox_inches='tight', dpi=300)
print("✅ SUCCESS! Saved 'biomarker_importance.png'")
print("📸 Put this image directly into Slide 4 of your Pitch Deck!")
import streamlit as st
import shap
import matplotlib.pyplot as plt
import datetime
import os
import numpy as np
import xgboost as xgb
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Configuration
st.set_page_config(page_title="PRISM Diagnostic Platform", layout="wide")

# T004: show_shap function
def show_shap(xgb_model, features, feature_names):
    """
    Renders a SHAP waterfall plot for clinical explainability.
    """
    try:
        explainer = shap.TreeExplainer(xgb_model)
        shap_vals = explainer.shap_values(features)
        
        # In multi-class, shap_values returns a list. Use index 1 (COVID) for demo.
        if isinstance(shap_vals, list):
            vals = shap_vals[1]
            base = explainer.expected_value[1] if explainer.expected_value is not None else 0
        else:
            vals = shap_vals[0]
            base = explainer.expected_value if explainer.expected_value is not None else 0
            
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('#0a0f1e')
        ax.set_facecolor('#111827')
        
        shap.plots.waterfall(
            shap.Explanation(
                values=vals,
                base_values=base,
                data=features[0],
                feature_names=feature_names
            ), show=False
        )
        
        # Apply dark theme styling to text
        for text in plt.gca().get_children():
            if isinstance(text, plt.Text):
                text.set_color('white')
                
        st.pyplot(fig)
        plt.close()
    except Exception as e:
        st.error(f"Error generating SHAP plot: {e}")

# T005: generate_pdf_report function
def generate_pdf_report(results, patient_id="DEMO-001"):
    """
    Generates a professional medical PDF report.
    """
    path = f"PRISM_Report_{patient_id}.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    
    # Header
    c.setFillColorRGB(0.04, 0.06, 0.12)
    c.rect(0, h-80, w, 80, fill=1)
    c.setFillColorRGB(0.13, 0.77, 0.37)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, h-50, "PRISM Diagnostic Report")
    c.setFillColorRGB(0.88, 0.91, 0.94)
    c.setFont("Helvetica", 11)
    c.drawString(40, h-68, f"Generated: {datetime.datetime.now().strftime('%d %b %Y %H:%M')}")
    
    # Primary diagnosis box
    disease_probs = results['sense']['disease_probabilities']
    top_d = max(disease_probs, key=disease_probs.get)
    top_p = disease_probs[top_d]
    
    c.setFillColorRGB(0.94, 0.27, 0.27)
    c.roundRect(40, h-160, w-80, 60, 8, fill=1)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(55, h-125, f"Primary: {top_d} — {top_p:.0%} probability")
    
    # Causal narrative
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 11)
    narrative = results['causal'].get('narrative', 'No narrative available.')
    # Simple text wrapping for PDF
    text_object = c.beginText(40, h-190)
    text_object.setFont("Helvetica", 11)
    text_object.textLines(narrative)
    c.drawText(text_object)
    
    # All disease probabilities
    c.setFont("Helvetica-Bold", 13)
    c.setFillColorRGB(0,0,0)
    c.drawString(40, h-280, "Disease Probability Summary")
    y = h-300
    for disease, prob in sorted(disease_probs.items(), key=lambda x: x[1], reverse=True):
        bar_w = int(prob * 300)
        color = (0.94, 0.27, 0.27) if prob > 0.6 else \
                (0.98, 0.62, 0.0) if prob > 0.3 else (0.13, 0.77, 0.37)
        c.setFillColorRGB(*color)
        c.rect(150, y-4, bar_w, 14, fill=1)
        c.setFillColorRGB(0,0,0)
        c.setFont("Helvetica", 10)
        c.drawString(40, y, disease)
        c.drawString(460, y, f"{prob:.0%}")
        y -= 22
    
    # Intervention plan
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, y-10, "Recommended Interventions")
    y -= 30
    for i, inv in enumerate(results['interventions'][:3], 1):
        cost = inv.get('cost', 0)
        cost_str = "FREE (Govt. Scheme)" if cost == 0 else f"₹{cost}/month"
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"{i}. {inv['name'].replace('_', ' ').title()} — {cost_str}")
        y -= 18
    
    # Footer
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.setFont("Helvetica", 8)
    c.drawString(40, 30, "PRISM AI Diagnostic Platform | Not a substitute for clinical judgment")
    
    c.save()
    return path

# Streamlit App
def main():
    st.title("PRISM: Intelligent Diagnostics")
    
    tab1, tab2 = st.tabs(["Patient Scan", "Population Health"])

    with tab2:
        st.header("Population Health Dashboard")
        st.info("Population-level analytics coming soon. This tab will display aggregated disease trends, regional risk maps, and intervention effectiveness metrics.")
    
    with tab1:
        st.header("New Patient Assessment")
        
        # Mocking data for UI demo
        feature_names = ["Spectral Flux", "MFCC 1", "ZCR", "Chroma 4", "Mel 12"]
        X_sample = np.random.normal(0, 1, (1, 5))
        
        # Placeholder for Model
        # In production: xgb_model = joblib.load("models/sense/cough_xgboost.pkl")
        xgb_model = xgb.XGBClassifier()
        # Train on dummy data to have a valid explainer
        xgb_model.fit(np.random.normal(0, 1, (10, 5)), [0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.button("Record 30s Audio")
            st.button("Capture Facial Video")
            
        with col2:
            st.subheader("Diagnostic Results")
            results = {
                "sense": {
                    "disease_probabilities": {"TB": 0.65, "COVID": 0.15, "Healthy": 0.20}
                },
                "causal": {
                    "narrative": "Primary driver: Crowding Index (76% contribution). Addressing this factor reduces estimated probability to 15%."
                },
                "interventions": [
                    {"name": "nutritional_support", "cost": 0},
                    {"name": "dots_treatment", "cost": 0}
                ]
            }
            
            top_d = "TB"
            top_p = 0.65
            st.metric(label="Primary Diagnosis", value=top_d, delta=f"{top_p:.0%}")
            
            # T006: Integration of SHAP
            st.subheader("Why this prediction?")
            show_shap(xgb_model, X_sample, feature_names)
            
            # T007: PDF Export
            if st.button("Generate Diagnostic Report"):
                pdf_path = generate_pdf_report(results)
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", f, file_name=pdf_path)

if __name__ == "__main__":
    main()

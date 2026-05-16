import os
import pytest
from app import generate_pdf_report

def test_pdf_generation():
    """
    Tests that the PDF report is generated successfully and exists on disk.
    """
    results = {
        "sense": {
            "disease_probabilities": {"TB": 0.8, "COVID": 0.1, "Healthy": 0.1}
        },
        "causal": {
            "narrative": "Test narrative for PRISM report."
        },
        "interventions": [
            {"name": "test_intervention", "cost": 100}
        ]
    }
    patient_id = "TEST-REPORT-001"
    expected_path = f"PRISM_Report_{patient_id}.pdf"
    
    # Cleanup if file exists
    if os.path.exists(expected_path):
        os.remove(expected_path)
        
    path = generate_pdf_report(results, patient_id)
    
    assert path == expected_path
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
    
    # Final cleanup
    os.remove(path)

if __name__ == "__main__":
    test_pdf_generation()
    print("PDF Generation Test: PASSED")

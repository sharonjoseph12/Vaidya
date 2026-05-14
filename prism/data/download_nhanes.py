"""
Script to download and preprocess NHANES data for the Metabolic Twin.
"""
import os
import pandas as pd
import argparse

def download_nhanes(output_dir):
    """
    Mock function to represent downloading NHANES dataset.
    In a real scenario, this would use pandas.read_sas or an API to fetch CDC data.
    """
    print(f"Downloading NHANES dataset to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create dummy data for testing the twin
    data = {
        'SEQN': [10001, 10001, 10002, 10002], # Respondent sequence number
        'TIME_HOURS': [0.0, 24.0, 0.0, 48.0], # Irregular timestamps
        'LBXGH': [5.6, 5.7, 8.2, 8.0],        # Glycohemoglobin (%)
        'LBXGLU': [95.0, 98.0, 150.0, 145.0], # Fasting Glucose (mg/dL)
        'BMXBMI': [24.5, 24.5, 31.2, 31.0]    # Body Mass Index
    }
    
    df = pd.DataFrame(data)
    output_path = os.path.join(output_dir, 'nhanes_mock.csv')
    df.to_csv(output_path, index=False)
    print(f"Mock NHANES data saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download NHANES data")
    parser.add_argument("--output-dir", type=str, default="prism/data/nhanes", help="Output directory")
    args = parser.parse_args()
    
    download_nhanes(args.output_dir)

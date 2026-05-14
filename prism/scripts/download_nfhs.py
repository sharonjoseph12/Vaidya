"""T006 - Download and extract NFHS-5 data from DHS Program."""
import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DHS API or manual download instructions
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw/nfhs5")
    args = parser.parse_args()
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("DHS data requires manual registration and download.")
    logger.info("1. Register at https://dhsprogram.com/data/new-user-registration.cfm")
    logger.info("2. Request access to India NFHS-5 (2019-21) data")
    logger.info("3. Download the 'IAHR7EFL.ZIP' or similar Household Recode dataset")
    logger.info("4. Extract the CSV or DTA files to: %s", out_dir.absolute())
    logger.info("\nOnce downloaded, run the preprocessor:")
    logger.info("python -m layer2_reason.data.nfhs_preprocessor --input %s --output data/processed/nfhs_india.pkl", out_dir)

if __name__ == "__main__":
    main()


import os
import re
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/tomato_leaf")
OUT_DIR = Path("data_proc")

def parse_inventory():
    """
    Parses the hyperspectral data inventory, extracts metadata from filenames,
    and saves it to a CSV file.
    """
    OUT_DIR.mkdir(exist_ok=True)
    
    hdr_files = sorted(DATA_DIR.rglob("*.hdr"))
    
    metadata = []
    for hdr_path in hdr_files:
        filename = hdr_path.name
        
        sensor = "VISNIR" if "VISNIR" in filename else "SWIR"
        is_ref = "cloth" in filename
        
        timepoint = "before"
        if "2h" in filename:
            timepoint = "2h"
        else:
            match = re.search(r"D(\d+)", filename)
            if match:
                timepoint = f"D{match.group(1)}"

        metadata.append({
            "hdr_path": str(hdr_path),
            "sensor": sensor,
            "is_ref": is_ref,
            "timepoint": timepoint,
        })
        
    df = pd.DataFrame(metadata)
    df.to_csv(OUT_DIR / "hsi_meta.csv", index=False)
    print(f"Successfully generated {OUT_DIR / 'hsi_meta.csv'}")

if __name__ == "__main__":
    parse_inventory()

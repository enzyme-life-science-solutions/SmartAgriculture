
import logging
import pandas as pd
import numpy as np
import spectral
from pathlib import Path

# Configure logging
LOG_DIR = Path("reports")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "trace_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

DATA_PROC_DIR = Path("data_proc")

def export_spectra():
    """
    Reads metadata, normalizes spectra using cloth references, and saves them.
    """
    logging.info("Starting spectra export process.")
    
    try:
        meta_df = pd.read_csv(DATA_PROC_DIR / "hsi_meta.csv")
    except FileNotFoundError:
        logging.error(f"Metadata file not found at {DATA_PROC_DIR / 'hsi_meta.csv'}. Please run parse_inventory.py first.")
        print(f"Error: Metadata file not found at {DATA_PROC_DIR / 'hsi_meta.csv'}. Please run parse_inventory.py first.")
        return

    cloth_refs = meta_df[meta_df["is_ref"] == True]
    samples = meta_df[meta_df["is_ref"] == False]

    for _, sample in samples.iterrows():
        try:
            # Find the corresponding cloth reference
            ref = cloth_refs[
                (cloth_refs["sensor"] == sample["sensor"]) &
                (cloth_refs["timepoint"] == sample["timepoint"])
            ]
            
            if ref.empty:
                logging.warning(f"No cloth reference found for sample {sample['hdr_path']}")
                continue

            ref_path = ref.iloc[0]["hdr_path"]
            sample_path = sample["hdr_path"]

            # Load images
            sample_img = spectral.open_image(sample_path).load()
            ref_img = spectral.open_image(ref_path).load()

            # Calculate mean spectra
            sample_mean_spectrum = np.mean(sample_img.reshape(-1, sample_img.shape[2]), axis=0)
            ref_mean_spectrum = np.mean(ref_img.reshape(-1, ref_img.shape[2]), axis=0)

            # Normalize
            normalized_spectrum = sample_mean_spectrum / ref_mean_spectrum

            # Save the spectrum
            sample_name = Path(sample_path).stem
            output_path = DATA_PROC_DIR / f"{sample_name}_spectrum.csv"
            pd.DataFrame({
                'wavelength': sample_img.bands.centers,
                'reflectance': normalized_spectrum
            }).to_csv(output_path, index=False)
            
            logging.info(f"Successfully processed and saved {output_path}")

        except Exception as e:
            logging.error(f"Error processing sample {sample['hdr_path']}: {e}")

    logging.info("Finished spectra export process.")
    print("Finished spectra export process. Check reports/trace_log.txt for details.")

if __name__ == "__main__":
    export_spectra()

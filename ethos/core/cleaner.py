import os
import pandas as pd
from ethos import config

class DataCleaner:
    """
    A class to handle cleaning and standardization of security system data.
    """
    def __init__(self, source_dir=config.SOURCE_DATA_DIR, output_dir=config.CLEAN_DATA_DIR, date_format="%Y-%m-%d %H:%M:%S"):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.date_format = date_format
        self.CLEANING_CONFIG = {
            "student or staff profiles.csv": {
                "ts_columns": [],
                "special_clean": self._clean_profiles,
                "output_filename": "profiles_cleaned.csv"
            },
            "campus card_swipes.csv": {"ts_columns": ["timestamp"]},
            "cctv_frames.csv": {"ts_columns": ["timestamp"]},
            "free_text_notes (helpdesk or RSVPs).csv": {"ts_columns": ["timestamp"]},
            "lab_bookings.csv": {"ts_columns": ["start_time", "end_time"]},
            "library_checkouts.csv": {"ts_columns": ["timestamp"]},
            "wifi_associations_logs.csv": {"ts_columns": ["timestamp"]},
            "face_embeddings.csv": {"ts_columns": []}
        }

    def run_cleaning_pipeline(self):
        """Orchestrates the full data cleaning and processing pipeline."""
        print("\n--- Starting Data Cleaning Process ---")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: '{self.output_dir}'")

        for filename, config in self.CLEANING_CONFIG.items():
            input_path = os.path.join(self.source_dir, filename)
            output_filename = config.get("output_filename", filename)
            output_path = os.path.join(self.output_dir, output_filename)

            try:
                df = pd.read_csv(input_path)
                print(f"Processing '{filename}'...")

                if "special_clean" in config:
                    df = config["special_clean"](df)

                if config["ts_columns"]:
                    self._standardize_timestamps(df, config["ts_columns"])

                df.to_csv(output_path, index=False)
                print(f"  -> Saved cleaned file to '{output_path}'")

            except FileNotFoundError:
                print(f"  -> WARNING: File '{filename}' not found. Skipping.")
            except Exception as e:
                print(f"  -> ERROR: Could not process '{filename}'. Reason: {e}")

        print("\n--- Data Cleaning Process Finished! ---")
        print(f"All cleaned files are now in the '{self.output_dir}' folder.")

    def _standardize_timestamps(self, df, ts_columns):
        """Standardizes datetime columns to a consistent format."""
        for col in ts_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[col] = df[col].dt.strftime(self.date_format)
        return df

    def _clean_profiles(self, df):
        """Handles special cleaning for the profiles DataFrame."""
        df = self._correct_duplicate_ids(df, 'student_id', 'S')
        df = self._correct_duplicate_ids(df, 'staff_id', 'T')
        return df

    @staticmethod
    def _correct_duplicate_ids(df, id_column, prefix):
        """Corrects duplicate IDs by assigning new, unique IDs."""
        duplicated_mask = df.duplicated(subset=[id_column], keep=False)
        non_null_mask = df[id_column].notna()
        ids_to_process = df[duplicated_mask & non_null_mask][id_column].unique()

        if len(ids_to_process) == 0:
            return df

        max_id_num_series = df[id_column].dropna().str.extract(r'^' + prefix + r'(\d+)', expand=False).astype(float)
        max_id_num = max_id_num_series.max()
        new_id_counter = int(max_id_num) + 1 if pd.notna(max_id_num) else 1

        for dup_id in ids_to_process:
            duplicate_indices = df[df[id_column] == dup_id].index
            for i in range(1, len(duplicate_indices)):
                row_index = duplicate_indices[i]
                new_id = f"{prefix}{new_id_counter}"
                df.loc[row_index, id_column] = new_id
                new_id_counter += 1
        return df

if __name__ == "__main__":
    # Example of how to run the cleaner
    # Assumes the script is run from the project root
    cleaner = DataCleaner()
    cleaner.run_cleaning_pipeline()

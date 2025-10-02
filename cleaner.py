import pandas as pd
import os

def clean_all_data():
    """
    Main function to orchestrate the cleaning of all dataset files.
    - Creates a 'clean_data' directory.
    - Cleans duplicate IDs in the profiles file.
    - Standardizes timestamps in all relevant files.
    - Saves all cleaned files into the 'clean_data' directory.
    """
    # --- 1. Setup ---
    source_directory = ".\data" # Assumes script is in the same folder as the data
    output_directory = "clean_data"
    standard_datetime_format = "%Y-%m-%d %H:%M:%S"

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created output directory: '{output_directory}'")

    # --- 2. Function to clean Profile IDs (from previous step) ---
    def correct_duplicate_ids(df, id_column, prefix):
        duplicated_mask = df.duplicated(subset=[id_column], keep=False)
        non_null_mask = df[id_column].notna()
        ids_to_process = df[duplicated_mask & non_null_mask][id_column].unique()
        if len(ids_to_process) == 0:
            return df
        max_id_num = df[id_column].dropna().str.extract(r'^' + prefix + r'(\d+)')[0].astype(float).max()
        new_id_counter = int(max_id_num) + 1
        for dup_id in ids_to_process:
            duplicate_indices = df[df[id_column] == dup_id].index
            for i in range(1, len(duplicate_indices)):
                row_index = duplicate_indices[i]
                new_id = f"{prefix}{new_id_counter}"
                df.loc[row_index, id_column] = new_id
                new_id_counter += 1
        return df

    # --- 3. Dictionary mapping filenames to their timestamp columns ---
    files_to_process = {
        "student or staff profiles.csv": [], # No timestamps, but needs ID cleaning
        "campus card_swipes.csv": ["timestamp"],
        "cctv_frames.csv": ["timestamp"],
        "free_text_notes (helpdesk or RSVPs).csv": ["timestamp"],
        "lab_bookings.csv": ["start_time", "end_time"],
        "library_checkouts.csv": ["timestamp"],
        "wifi_associations_logs.csv": ["timestamp"],
        # face_embeddings.csv has no timestamps, so we can just copy it
        "face_embeddings.csv": [] 
    }

    print("\n--- Starting Data Cleaning Process ---")

    # --- 4. Loop through files, clean, and save ---
    for filename, ts_columns in files_to_process.items():
        input_path = os.path.join(source_directory, filename)
        output_path = os.path.join(output_directory, filename)

        try:
            df = pd.read_csv(input_path)
            print(f"Processing '{filename}'...")

            # Special handling for profiles file
            if filename == "student or staff profiles.csv":
                df = correct_duplicate_ids(df, 'student_id', 'S')
                df = correct_duplicate_ids(df, 'staff_id', 'T')
                # The cleaned profiles file should have a new name
                output_path = os.path.join(output_directory, "profiles_cleaned.csv")

            # Handling for all other files
            if ts_columns:
                for col in ts_columns:
                    # pd.to_datetime is powerful and can infer many formats.
                    # errors='coerce' will turn any unparseable dates into NaT (Not a Time)
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    # Now format it back to our standard string format
                    df[col] = df[col].dt.strftime(standard_datetime_format)
            
            # Save the cleaned dataframe
            df.to_csv(output_path, index=False)
            print(f"  -> Saved cleaned file to '{output_path}'")

        except FileNotFoundError:
            print(f"  -> WARNING: File '{filename}' not found. Skipping.")
        except Exception as e:
            print(f"  -> ERROR: Could not process '{filename}'. Reason: {e}")

    print("\n--- Data Cleaning Process Finished! ---")
    print(f"All cleaned files are now in the '{output_directory}' folder.")


# --- Run the main function ---
if __name__ == "__main__":
    clean_all_data()
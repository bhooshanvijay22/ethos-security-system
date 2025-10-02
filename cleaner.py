import pandas as pd
import numpy as np

def clean_campus_profiles():
    """
    Loads the profiles CSV, corrects duplicate student and staff IDs,
    and saves a new cleaned CSV file.
    """
    input_filename = "data\student or staff profiles.csv"
    output_filename = "data\profiles_cleaned.csv"

    # --- 1. Load the Data ---
    try:
        profiles_df = pd.read_csv(input_filename)
        print(f"Successfully loaded '{input_filename}'.")
        print(f"Original shape of the dataframe: {profiles_df.shape}")
    except FileNotFoundError:
        print(f"Error: '{input_filename}' not found.")
        print("Please make sure this script is in the same folder as your CSV files.")
        return # Exit the function

    # --- Create a copy to modify ---
    df_cleaned = profiles_df.copy()

    # --- 2. Define a function to fix duplicate IDs ---
    def correct_duplicate_ids(df, id_column, prefix):
        """
        Finds duplicate IDs in a column, keeps the first occurrence,
        and assigns new, unique IDs to the subsequent duplicates.
        """
        # Find all non-null IDs that are duplicated
        duplicated_mask = df.duplicated(subset=[id_column], keep=False)
        non_null_mask = df[id_column].notna()
        ids_to_process = df[duplicated_mask & non_null_mask][id_column].unique()

        if len(ids_to_process) == 0:
            print(f"\nNo duplicates found in '{id_column}'. No changes needed.")
            return df

        print(f"\nFound {len(ids_to_process)} ID values that are duplicated in '{id_column}'. Correcting them now...")
        print("Duplicate ID values are:", list(ids_to_process))

        # Find the maximum numeric part of existing IDs to avoid collisions
        max_id_num = df[id_column].dropna().str.extract(r'^' + prefix + r'(\d+)')[0].astype(float).max()
        new_id_counter = int(max_id_num) + 1

        for dup_id in ids_to_process:
            duplicate_indices = df[df[id_column] == dup_id].index
            for i in range(1, len(duplicate_indices)):
                row_index = duplicate_indices[i]
                new_id = f"{prefix}{new_id_counter}"
                df.loc[row_index, id_column] = new_id
                print(f"  - Changed '{dup_id}' for entity '{df.loc[row_index, 'entity_id']}' to new ID '{new_id}'")
                new_id_counter += 1
        return df

    # --- 3. Run the correction process ---
    # Assuming student IDs start with 'S' and staff IDs start with 'T'
    df_cleaned = correct_duplicate_ids(df_cleaned, 'student_id', 'S')
    df_cleaned = correct_duplicate_ids(df_cleaned, 'staff_id', 'T')

    # --- 4. Verification ---
    print("\n--- Verification after cleaning ---")
    student_duplicates_after = df_cleaned[df_cleaned['student_id'].notna()].duplicated(subset=['student_id']).sum()
    staff_duplicates_after = df_cleaned[df_cleaned['staff_id'].notna()].duplicated(subset=['staff_id']).sum()
    print(f"Number of duplicate student_ids after cleaning: {student_duplicates_after}")
    print(f"Number of duplicate staff_ids after cleaning: {staff_duplicates_after}")

    # --- 5. Save the cleaned DataFrame ---
    df_cleaned.to_csv(output_filename, index=False)
    print(f"\nSuccessfully saved the cleaned data to '{output_filename}'.")
    print("You can now use this file as the main source for profiles.")

# --- Run the main function ---
if __name__ == "__main__":
    clean_campus_profiles()
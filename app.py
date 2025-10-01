import pandas as pd
import os

def load_all_data(data_directory="data"):
    """
    Loads all CSV files from a specified directory into a dictionary of pandas DataFrames.
    
    Args:
        data_directory (str): The path to the folder containing the dataset files.

    Returns:
        dict: A dictionary where keys are filenames and values are the corresponding DataFrames.
              Returns an empty dictionary if the directory is not found.
    """
    if not os.path.exists(data_directory):
        print(f"Error: Data directory '{data_directory}' not found.")
        return {}

    all_dataframes = {}
    print(f"Loading data from '{data_directory}'...")
    
    for filename in os.listdir(data_directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(data_directory, filename)
            try:
                all_dataframes[filename] = pd.read_csv(file_path)
                print(f"  - Loaded '{filename}' successfully.")
            except Exception as e:
                print(f"  - Failed to load '{filename}'. Error: {e}")
                
    return all_dataframes

def find_entities_in_profiles(search_term, profiles_df):
    """
    Searches for a term across multiple identifying columns in the profiles DataFrame.

    Args:
        search_term (str): The value to search for (e.g., a name, ID, email).
        profiles_df (pd.DataFrame): The DataFrame from 'student or staff profiles.csv'.

    Returns:
        list: A list of dictionaries, where each dictionary represents a potential match.
    """
    # Ensure the search term is a string to prevent errors with numeric IDs
    search_term = str(search_term)

    # --- 1. Create a boolean "mask" for each column to search ---
    # Partial, case-insensitive match for 'name'
    name_mask = profiles_df['name'].str.contains(search_term, case=False, na=False)

    # Exact match for various ID columns
    entity_id_mask = profiles_df['entity_id'] == search_term
    card_id_mask = profiles_df['card_id'] == search_term
    device_hash_mask = profiles_df['device_hash'] == search_term
    face_id_mask = profiles_df['face_id'] == search_term
    email_mask = profiles_df['email'] == search_term
    student_id_mask = profiles_df['student_id'] == search_term
    staff_id_mask = profiles_df['staff_id'] == search_term

    # --- 2. Combine all masks into a single filter using the OR '|' operator ---
    combined_mask = (name_mask | entity_id_mask | card_id_mask | 
                     device_hash_mask | face_id_mask | email_mask |
                     student_id_mask | staff_id_mask)

    # --- 3. Apply the combined filter to the DataFrame ---
    matching_df = profiles_df[combined_mask]

    # --- 4. Convert the resulting DataFrame into a list of dictionaries ---
    results = matching_df.to_dict('records')

    return results


# This block runs when you execute the script directly
if __name__ == "__main__":
    
    # Load all datasets from the 'data/' folder
    all_data = load_all_data()

    # Define the filename for the main profiles CSV
    PROFILES_FILENAME = "student or staff profiles.csv"

    # Check if data was loaded and if the profiles file exists
    if all_data and PROFILES_FILENAME in all_data:
        
        profiles_dataframe = all_data[PROFILES_FILENAME]

        # --- Example Search ---
        print("\n" + "="*50)
        print("Running an example search...")
        
        search_query = "Alice"
        matches = find_entities_in_profiles(search_query, profiles_dataframe)

        # --- Print Results ---
        if matches:
            print(f"Found {len(matches)} match(es) for '{search_query}':")
            for i, match in enumerate(matches):
                print(f"  Result {i+1}:")
                # Print some key info for each match
                print(f"    Name: {match.get('name')}")
                print(f"    Entity ID: {match.get('entity_id')}")
                print(f"    Email: {match.get('email')}")
        else:
            print(f"No matches found for '{search_query}'.")

        print("="*50)
        
    else:
        print("\nCould not run example search. Ensure the data is loaded correctly.")
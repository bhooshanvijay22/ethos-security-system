import pandas as pd
import os

# Assuming this helper function is correct and unchanged
def load_all_data(data_directory="data"):
    """
    Loads all CSV files from a specified directory into a dictionary of pandas DataFrames.
    ...
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

# Assuming this helper function is correct and unchanged
def find_entities_in_profiles(search_term, profiles_df):
    """
    Searches for a term across multiple identifying columns in the profiles DataFrame.
    ...
    """
    # Ensure the search term is a string to prevent errors with numeric IDs
    search_term = str(search_term)

    # --- 1. Create a boolean "mask" for each column to search ---
    # Partial, case-insensitive match for 'name'
    name_mask = profiles_df['name'].str.contains(search_term, case=False, na=False)

    # Exact match for various ID columns (assuming these exist in the profiles CSV)
    entity_id_mask = profiles_df['entity_id'] == search_term
    card_id_mask = profiles_df['card_id'] == search_term
    device_hash_mask = profiles_df['device_hash'] == search_term
    face_id_mask = profiles_df['face_id'] == search_term
    email_mask = profiles_df['email'] == search_term
    # Note: Using 'role' in the frontend, but leaving original ID checks here for robustness
    student_id_mask = profiles_df.get('student_id', pd.Series(False)) == search_term
    staff_id_mask = profiles_df.get('staff_id', pd.Series(False)) == search_term


    # --- 2. Combine all masks into a single filter using the OR '|' operator ---
    combined_mask = (name_mask | entity_id_mask | card_id_mask | 
                     device_hash_mask | face_id_mask | email_mask |
                     student_id_mask | staff_id_mask)

    # --- 3. Apply the combined filter to the DataFrame ---
    matching_df = profiles_df[combined_mask]

    # --- 4. Convert the resulting DataFrame into a list of dictionaries ---
    results = matching_df.to_dict('records')

    return results

# --- NEW: COMPLETED generate_timeline FUNCTION ---

def generate_timeline(entity_identifiers: dict, all_data: dict, time_window=None):
    """
    Generates a chronological timeline of events for a single entity based on their identifiers.

    Args:
        entity_identifiers (dict): A dictionary (single profile match) containing identifiers 
                                   (e.g., 'card_id', 'device_hash', 'entity_id', 'name').
        all_data (dict): Dictionary of all loaded DataFrames (log files).
        time_window (tuple, optional): Not implemented in detail, but reserved for future filtering.

    Returns:
        str: A formatted, chronological string representing the timeline.
    """
    timeline_entries = []

    # Get the key identifiers from the profile dictionary
    card_id = entity_identifiers.get('card_id')
    device_hash = entity_identifiers.get('device_hash')
    face_id = entity_identifiers.get('face_id')
    entity_name = entity_identifiers.get('name', 'UNKNOWN ENTITY')

    # Define how to map log files to their search column, timestamp column, and event description
    LOG_CONFIGS = {
        'card_swipe_logs.csv': {
            'search_col': 'card_id', 
            'ts_col': 'timestamp', 
            'desc_cols': ['location_id', 'access_result'],
            'source': 'Card Swipe'
        },
        'wifi_logs.csv': {
            'search_col': 'device_hash', 
            'ts_col': 'timestamp', 
            'desc_cols': ['router_location', 'connection_type'],
            'source': 'WiFi Connection'
        },
        'camera_logs.csv': {
            'search_col': 'face_id', 
            'ts_col': 'timestamp', 
            'desc_cols': ['camera_location', 'activity_type'],
            'source': 'Camera/Facial Rec'
        }
        # Add more log files here as needed
    }

    # 1. Iterate through all relevant log DataFrames
    for filename, config in LOG_CONFIGS.items():
        if filename in all_data:
            df = all_data[filename].copy() # Work on a copy

            search_val = entity_identifiers.get(config['search_col'])

            if search_val is not None and config['search_col'] in df.columns:
                
                # 2. Filter the log data to find all rows matching the entity.
                df_filtered = df[df[config['search_col']] == search_val]

                # 3. Create standardized timeline entry for each matching log row
                for _, row in df_filtered.iterrows():
                    
                    # Create a descriptive string from the configured columns
                    description_parts = [str(row[col]) for col in config['desc_cols'] if col in row]
                    description = f"{config['source']} event: {', '.join(description_parts)}"
                    
                    timeline_entries.append({
                        'Timestamp': row[config['ts_col']],
                        'Source': config['source'],
                        'Activity': description,
                        'Name': entity_name # Include the name for context
                    })


    # 5. Sort all collected entries chronologically.
    # We must ensure the timestamp column is correctly sortable (i.e., strings are consistent or converted)
    try:
        timeline_entries.sort(key=lambda x: x['Timestamp'])
    except Exception as e:
        print(f"Warning: Could not sort timeline entries chronologically. Error: {e}")
        # Proceed without sorting if the timestamp format is inconsistent

    # 6. Format the entries into a clear, human-readable string.
    formatted_timeline_string = f"Timeline for {entity_name} (ID: {entity_identifiers.get('entity_id')})\n"
    formatted_timeline_string += "="*60 + "\n"
    
    if not timeline_entries:
        formatted_timeline_string += "No logged activities found for this entity based on provided identifiers.\n"
        return formatted_timeline_string

    for entry in timeline_entries:
        formatted_timeline_string += (
            f"[{entry['Timestamp']}] | Source: {entry['Source']}\n"
            f"    -> {entry['Activity']}\n"
        )
        formatted_timeline_string += "-"*60 + "\n"
        
    return formatted_timeline_string

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
                
                # --- Example Timeline Generation ---
                print("\n    --- Example Timeline ---")
                timeline = generate_timeline(match, all_data)
                print(timeline)
                print("    ------------------------")
        else:
            print(f"No matches found for '{search_query}'.")

        print("="*50)
        
    else:
        print("\nCould not run example search. Ensure the data is loaded correctly.")
import pandas as pd
import os

def load_all_data(data_directory="data"):
    """
    Loads all CSV files from a specified directory into a dictionary of pandas DataFrames.
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
                # Use low_memory=False for robustness against mixed data types in columns
                all_dataframes[filename] = pd.read_csv(file_path, low_memory=False) 
                print(f"  - Loaded '{filename}' successfully.")
            except Exception as e:
                print(f"  - Failed to load '{filename}'. Error: {e}")
                
    return all_dataframes

def find_entities_in_profiles(search_term, profiles_df):
    """
    Searches for a term across multiple identifying columns in the profiles DataFrame.
    """
    # Ensure the search term is a string to prevent errors with numeric IDs
    search_term = str(search_term)

    # List of all identifying columns to search across
    search_cols = ['name', 'entity_id', 'email', 'card_id', 'device_hash', 'face_id', 'student_id', 'staff_id']
    
    # --- 1. Create a combined boolean "mask" for the search ---
    combined_mask = pd.Series(False, index=profiles_df.index)

    for col in search_cols:
        if col in profiles_df.columns:
            series = profiles_df[col].astype(str)
            # Use partial match for 'name', exact match for IDs
            if col == 'name':
                mask = series.str.contains(search_term, case=False, na=False)
            else:
                mask = series == search_term
            
            combined_mask = combined_mask | mask

    # --- 2. Apply the combined filter and return the list of profile dictionaries ---
    matching_df = profiles_df[combined_mask]
    
    # Fill NA values with None before converting to dictionary, to ensure keys exist
    results = matching_df.where(pd.notna(matching_df), None).to_dict('records') 

    return results

def generate_timeline(entity_identifiers: dict, all_data: dict, time_window=None):
    """
    Generates a chronological timeline of events for a single entity based on their identifiers.
    """
    timeline_entries = []

    # Get the key identifiers from the profile dictionary.
    card_id = entity_identifiers.get('card_id')
    device_hash = entity_identifiers.get('device_hash')
    face_id = entity_identifiers.get('face_id')
    entity_id = entity_identifiers.get('entity_id')
    entity_name = entity_identifiers.get('name', 'UNKNOWN ENTITY')

    # Define how to map log files to their search column, timestamp column, and event description
    LOG_CONFIGS = {
        'campus card_swipes.csv': {
            'search_val': card_id,         
            'search_col': 'card_id',      
            'ts_col': 'timestamp', 
            'desc_cols': ['location_id'], 
            'source': 'Card Swipe'
        },
        'wifi_associations_logs.csv': {
            'search_val': device_hash,
            'search_col': 'device_hash', 
            'ts_col': 'timestamp', 
            'desc_cols': ['ap_id'], 
            'source': 'WiFi Connection'
        },
        'cctv_frames.csv': {
            'search_val': face_id,
            'search_col': 'face_id', 
            'ts_col': 'timestamp', 
            'desc_cols': ['location_id'], 
            'source': 'Camera/Facial Rec'
        }
    }
    
    # Add other logs that link via entity_id 
    if entity_id is not None:
        OTHER_LOGS = {
            'lab_bookings.csv': {
                'search_col': 'entity_id',
                'ts_col': 'start_time', 
                'desc_cols': ['room_id', 'end_time', 'attended (YES/NO)'],
                'source': 'Lab Booking',
                'search_val': entity_id
            },
            'library_checkouts.csv': {
                'search_col': 'entity_id',
                'ts_col': 'timestamp', 
                'desc_cols': ['book_id'],
                'source': 'Library Checkout',
                'search_val': entity_id
            },
            'free_text_notes (helpdesk or RSVPs).csv': {
                'search_col': 'entity_id',
                'ts_col': 'timestamp',
                'desc_cols': ['category', 'text'],
                'source': 'Free Text Note',
                'search_val': entity_id
            }
        }
        LOG_CONFIGS.update(OTHER_LOGS)


    # 1. Iterate through all relevant log DataFrames
    for filename, config in LOG_CONFIGS.items():
        if filename in all_data:
            df = all_data[filename].copy()

            search_val = config['search_val']
            search_col = config['search_col']

            # Only proceed if we have an ID for this type and the log file has the column
            if search_val is not None and search_col in df.columns and config['ts_col'] in df.columns:
                
                # Try to convert log column to the type of search_val (robustness)
                try:
                    df[search_col] = df[search_col].astype(type(search_val))
                except:
                    df[search_col] = df[search_col].astype(str)
                    search_val = str(search_val)


                # 2. Filter the log data to find all rows matching the entity.
                df_filtered = df[df[search_col] == search_val]

                # 3. Create standardized timeline entry for each matching log row
                for _, row in df_filtered.iterrows():
                    
                    details = {}
                    for col in config['desc_cols']:
                        if col in row:
                            details[col] = str(row[col])
                        else:
                            details[col] = "N/A"
                            
                    timeline_entries.append({
                        'Timestamp': row[config['ts_col']],
                        'Source': config['source'],
                        'Details': details, # Store details as a dict for cleaner formatting
                        'Name': entity_name
                    })


    # 5. Sort all collected entries chronologically.
    try:
        timeline_entries.sort(key=lambda x: x['Timestamp'])
    except Exception as e:
        pass 

    # 6. Format the entries into a clear, human-readable string.
    
    # CLEANER FORMATTING START
    formatted_timeline_string = (
        f"\nTIMELINE FOR: {entity_name} (ID: {entity_id})\n"
        f"{'='*30}\n"
    )
    
    if not timeline_entries:
        formatted_timeline_string += "No logged activities found for this entity based on provided identifiers.\n"
        return formatted_timeline_string

    for entry in timeline_entries:
        # Line 1: Time and Source, with no bolding
        formatted_timeline_string += f"{entry['Timestamp']} | Source: {entry['Source'].upper()} \n"

        # Line 2 onwards: Details with clear indentation and simplified keys
        for key, value in entry['Details'].items():
            
            display_key = key
            
            # --- FIX APPLIED HERE ---
            # 1. Handle the specific replacement for lab bookings key
            if display_key == 'attended (YES/NO)':
                display_key = 'Attended'
            
            # 2. Apply generic cleanups: replace underscores and title-case for all others
            else:
                # Clean up the key for display (e.g., replace underscores, capitalize)
                display_key = display_key.replace('_', ' ').strip().title()
            # --- END FIX ---
            
            # Use consistent indentation
            formatted_timeline_string += f"    {display_key}: {value}\n"

        # Add an extra empty line as a separator
        formatted_timeline_string += "\n"
        
    return formatted_timeline_string.rstrip('\n') # Remove trailing newlines

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
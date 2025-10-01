import pandas as pd
import os

# --- (Existing code from your file) ---

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
                df = pd.read_csv(file_path)
                # Attempt to convert any column with 'timestamp' in its name to datetime
                for col in df.columns:
                    if 'timestamp' in col.lower():
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                all_dataframes[filename] = df
                print(f"  - Loaded '{filename}' successfully.")
            except Exception as e:
                print(f"  - Failed to load '{filename}'. Error: {e}")
                
    return all_dataframes

def find_entities_in_profiles(search_term, profiles_df):
    """
    Searches for a term across multiple identifying columns in the profiles DataFrame.
    """
    search_term = str(search_term)
    name_mask = profiles_df['name'].str.contains(search_term, case=False, na=False)
    entity_id_mask = profiles_df['entity_id'] == search_term
    card_id_mask = profiles_df['card_id'] == search_term
    device_hash_mask = profiles_df['device_hash'] == search_term
    face_id_mask = profiles_df['face_id'] == search_term
    email_mask = profiles_df['email'] == search_term
    student_id_mask = profiles_df['student_id'] == search_term
    staff_id_mask = profiles_df['staff_id'] == search_term

    combined_mask = (name_mask | entity_id_mask | card_id_mask | 
                     device_hash_mask | face_id_mask | email_mask |
                     student_id_mask | staff_id_mask)

    matching_df = profiles_df[combined_mask]
    return matching_df.to_dict('records')

# --- (New code to add) ---

def get_entity_timeline(entity_profile, all_data):
    """
    Builds a chronological timeline of activities for a given entity.
    This is the core of "Timeline Generation"[cite: 19].
    """
    timeline = []
    
    # Extract all known identifiers for the entity
    card_id = entity_profile.get('card_id')
    device_hash = entity_profile.get('device_hash')
    entity_id = entity_profile.get('entity_id')

    # 1. Check Card Swipes
    swipes_df = all_data.get("campus card swipe logs.csv")
    if card_id and swipes_df is not None:
        entity_swipes = swipes_df[swipes_df['card_id'] == card_id]
        for _, row in entity_swipes.iterrows():
            event = {
                "timestamp": row['timestamp'],
                "activity": f"Card swipe at location '{row['location_id']}'",
                "source": "Campus Card Swipes"
            }
            timeline.append(event)

    # 2. Check Wi-Fi Association Logs
    wifi_df = all_data.get("wifi association logs.csv")
    if device_hash and wifi_df is not None:
        entity_wifi = wifi_df[wifi_df['device_hash'] == device_hash]
        for _, row in entity_wifi.iterrows():
            event = {
                "timestamp": row['timestamp'],
                "activity": f"Device connected to Wi-Fi AP '{row['ap_id']}'",
                "source": "Wi-Fi Logs"
            }
            timeline.append(event)
            
    # 3. Check Library Checkouts (assuming it uses entity_id)
    library_df = all_data.get("library checkouts.csv")
    if entity_id and library_df is not None:
        entity_library = library_df[library_df['entity_id'] == entity_id]
        for _, row in entity_library.iterrows():
            event = {
                "timestamp": row['timestamp'],
                "activity": f"Checked out item '{row['item_id']}' from library",
                "source": "Library Checkouts"
            }
            timeline.append(event)

    # Sort the combined timeline by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    
    return timeline

def check_for_alerts(timeline):
    """
    Checks if an entity has been unobserved for more than 12 hours.
    This fulfills the "Security & Alerting" requirement[cite: 21].
    """
    if not timeline:
        return "ALERT: No activity data found for this entity."

    last_event_time = timeline[-1]['timestamp']
    # Ensure timezone awareness is handled or stripped for comparison
    last_event_time = last_event_time.tz_localize(None) if last_event_time.tzinfo else last_event_time
    
    current_time = pd.Timestamp.now()
    time_difference = current_time - last_event_time

    if time_difference > pd.Timedelta(hours=12):
        return (f"ALERT: No activity observed for this entity in the last 12 hours.\n"
                f"Last seen: {last_event_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return None
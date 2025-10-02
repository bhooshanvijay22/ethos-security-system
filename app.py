import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np

def load_all_data(data_directory="clean_data"):
    """Loads all CSV files from a directory into a dictionary of pandas DataFrames."""
    if not os.path.exists(data_directory):
        print(f"Error: Data directory '{data_directory}' not found.")
        return {}

    all_dataframes = {}
    print(f"Loading data from '{data_directory}'...")

    for filename in os.listdir(data_directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(data_directory, filename)
            try:
                all_dataframes[filename] = pd.read_csv(file_path, low_memory=False)
                print(f"  - Loaded '{filename}' successfully.")
            except Exception as e:
                print(f"  - Failed to load '{filename}'. Error: {e}")

    return all_dataframes

def find_entities_in_profiles(search_term, profiles_df):
    """Searches for a term across multiple identifying columns in the profiles DataFrame."""
    search_term = str(search_term)
    search_cols = ['name', 'entity_id', 'email', 'card_id', 'device_hash', 'face_id', 'student_id', 'staff_id']
    combined_mask = pd.Series(False, index=profiles_df.index)

    for col in search_cols:
        if col in profiles_df.columns:
            series = profiles_df[col].astype(str)
            if col == 'name':
                mask = series.str.contains(search_term, case=False, na=False)
            else:
                mask = series == search_term
            combined_mask = combined_mask | mask

    matching_df = profiles_df[combined_mask]
    results = matching_df.where(pd.notna(matching_df), None).to_dict('records')
    return results

def generate_timeline(entity_identifiers: dict, all_data: dict, time_window=None):
    """Generates a chronological timeline of events for a single entity based on their identifiers."""
    timeline_entries = []
    
    card_id = entity_identifiers.get('card_id')
    device_hash = entity_identifiers.get('device_hash')
    face_id = entity_identifiers.get('face_id')
    entity_id = entity_identifiers.get('entity_id')
    entity_name = entity_identifiers.get('name', 'UNKNOWN ENTITY')

    LOG_CONFIGS = {
        'campus card_swipes.csv': {'search_val': card_id, 'search_col': 'card_id', 'ts_col': 'timestamp', 'desc_cols': ['location_id'], 'source': 'Card Swipe'},
        'wifi_associations_logs.csv': {'search_val': device_hash, 'search_col': 'device_hash', 'ts_col': 'timestamp', 'desc_cols': ['ap_id'], 'source': 'WiFi Connection'},
        'cctv_frames.csv': {'search_val': face_id, 'search_col': 'face_id', 'ts_col': 'timestamp', 'desc_cols': ['location_id'], 'source': 'Camera/Facial Rec'}
    }

    if entity_id is not None:
        OTHER_LOGS = {
            'lab_bookings.csv': {'search_col': 'entity_id', 'ts_col': 'start_time', 'desc_cols': ['room_id', 'end_time', 'attended (YES/NO)'], 'source': 'Lab Booking', 'search_val': entity_id},
            'library_checkouts.csv': {'search_col': 'entity_id', 'ts_col': 'timestamp', 'desc_cols': ['book_id'], 'source': 'Library Checkout', 'search_val': entity_id},
            'free_text_notes (helpdesk or RSVPs).csv': {'search_col': 'entity_id', 'ts_col': 'timestamp', 'desc_cols': ['category', 'text'], 'source': 'Free Text Note', 'search_val': entity_id}
        }
        LOG_CONFIGS.update(OTHER_LOGS)

    for filename, config in LOG_CONFIGS.items():
        if filename in all_data:
            df = all_data[filename].copy()
            search_val = config['search_val']
            search_col = config['search_col']

            if search_val is not None and search_col in df.columns and config['ts_col'] in df.columns:
                try:
                    df[search_col] = df[search_col].astype(type(search_val))
                except (ValueError, TypeError):
                    df[search_col] = df[search_col].astype(str)
                    search_val = str(search_val)

                df_filtered = df[df[search_col] == search_val]

                for _, row in df_filtered.iterrows():
                    details = {col: str(row.get(col, "N/A")) for col in config['desc_cols']}
                    timeline_entries.append({
                        'Timestamp': row[config['ts_col']],
                        'Source': config['source'],
                        'Details': details,
                        'Name': entity_name
                    })

    try:
        timeline_entries.sort(key=lambda x: pd.to_datetime(x['Timestamp'], errors='coerce'))
    except Exception:
        pass

    formatted_timeline_string = f"\nTIMELINE FOR: {entity_name} (ID: {entity_id})\n{'='*30}\n"
    if not timeline_entries:
        formatted_timeline_string += "No logged activities found for this entity.\n"
        return formatted_timeline_string

    for entry in timeline_entries:
        formatted_timeline_string += f"{entry['Timestamp']} | Source: {entry['Source'].upper()} \n"
        for key, value in entry['Details'].items():
            display_key = 'Attended' if key == 'attended (YES/NO)' else key.replace('_', ' ').strip().title()
            formatted_timeline_string += f"    {display_key}: {value}\n"
        formatted_timeline_string += "\n"

    return formatted_timeline_string.rstrip('\n')

# --- NEW --- Helper function to get the most recent location for prediction
def get_last_known_location(entity_identifiers: dict, all_data: dict):
    """Finds the most recent location log entry for an entity."""
    card_id = entity_identifiers.get('card_id')
    device_hash = entity_identifiers.get('device_hash')
    
    location_entries = []

    # Check card swipes
    if card_id and 'campus card_swipes.csv' in all_data:
        swipes_df = all_data['campus card_swipes.csv']
        entity_swipes = swipes_df[swipes_df['card_id'] == card_id]
        for _, row in entity_swipes.iterrows():
            location_entries.append({'timestamp': row['timestamp'], 'location': row['location_id']})

    # Check WiFi logs
    if device_hash and 'wifi_associations_logs.csv' in all_data:
        wifi_df = all_data['wifi_associations_logs.csv']
        entity_wifi = wifi_df[wifi_df['device_hash'] == device_hash]
        for _, row in entity_wifi.iterrows():
            location_entries.append({'timestamp': row['timestamp'], 'location': row['ap_id']})

    if not location_entries:
        return None, "No location history found to make a prediction."

    # Sort to find the most recent entry
    try:
        location_entries.sort(key=lambda x: pd.to_datetime(x['timestamp'], errors='coerce'), reverse=True)
    except Exception:
        return None, "Could not sort location history due to time format errors."

    last_location = location_entries[0]['location']
    return last_location, f"Last known location was '{last_location}' at {location_entries[0]['timestamp']}."

def train_location_predictor(clean_data):
    """Trains a simple ML model to predict next location."""
    required_files = ["campus card_swipes.csv", "wifi_associations_logs.csv", "profiles_cleaned.csv"]
    if not all(f in clean_data for f in required_files):
        print("⚠️ Missing required data files (swipes, wifi, or profiles) for training predictor.")
        return None, None, None

    # Merge profiles to get a consistent entity_id
    profiles = clean_data["profiles_cleaned.csv"][['entity_id', 'card_id', 'device_hash']].copy()
    swipes = clean_data["campus card_swipes.csv"].copy()
    wifi = clean_data["wifi_associations_logs.csv"].copy()

    swipes = pd.merge(swipes, profiles, on='card_id', how='left')
    wifi = pd.merge(wifi, profiles, on='device_hash', how='left')

    dfs = []
    if not swipes.empty:
        df = swipes[["entity_id", "location_id", "timestamp"]].dropna()
        dfs.append(df)
    if not wifi.empty:
        df = wifi[["entity_id", "ap_id", "timestamp"]].dropna()
        df = df.rename(columns={"ap_id": "location_id"})
        dfs.append(df)

    if not dfs:
        return None, None, None

    data = pd.concat(dfs).sort_values(by="timestamp").dropna(subset=['entity_id', 'location_id'])
    if data.empty:
        return None, None, None
    
    entity_encoder = LabelEncoder()
    loc_encoder = LabelEncoder()
    data["entity_id_enc"] = entity_encoder.fit_transform(data["entity_id"].astype(str))
    data["location_id_enc"] = loc_encoder.fit_transform(data["location_id"].astype(str))

    X, y = [], []
    for eid in data["entity_id_enc"].unique():
        sub = data[data["entity_id_enc"] == eid].sort_values("timestamp")
        locs = sub["location_id_enc"].values
        for i in range(len(locs) - 1):
            X.append([eid, locs[i]])
            y.append(locs[i+1])

    if not X:
        print("Not enough sequential data to train the predictor.")
        return None, None, None

    X, y = np.array(X), np.array(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if len(X_train) == 0:
        print("Not enough training data after split.")
        return None, None, None

    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X_train, y_train)

    accuracy = clf.score(X_test, y_test) if len(X_test) > 0 else "N/A"
    print(f"✅ Location predictor trained. Accuracy: {accuracy}")
    return clf, entity_encoder, loc_encoder

def predict_next_location(entity_id, current_location, clf, entity_encoder, loc_encoder):
    """Predicts the next location for an entity."""
    if clf is None or current_location is None:
        return "⚠️ Predictor not available or current location is unknown."

    try:
        # Encode inputs, handling unseen labels
        if entity_id not in entity_encoder.classes_:
            return "Entity ID not seen during training."
        if current_location not in loc_encoder.classes_:
            return "Location not seen during training."

        entity_id_enc = entity_encoder.transform([entity_id])[0]
        current_loc_enc = loc_encoder.transform([current_location])[0]
        
        X_pred = np.array([[entity_id_enc, current_loc_enc]])
        y_pred_enc = clf.predict(X_pred)
        predicted_location = loc_encoder.inverse_transform(y_pred_enc)[0]
        
        return f"Predicted Next Location: **{predicted_location}**"

    except Exception as e:
        return f"Error during prediction: {e}"
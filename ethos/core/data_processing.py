import pandas as pd
import os
from ethos import config
from ethos.core import cleaner as Sweeper

class DataProcessor:
    def __init__(self, data_directory=config.CLEAN_DATA_DIR):
        self.data_directory = data_directory
        self.all_data = self._load_all_data()
        self.profiles_df = self.all_data.get(config.PROFILES_CLEANED_FILENAME, pd.DataFrame())

    def _load_all_data(self):
        if not os.path.exists(self.data_directory):
            cleaner = Sweeper.DataCleaner()
            cleaner.run_cleaning_pipeline()
            return {}

        all_dataframes = {}
        print(f"Loading data from '{self.data_directory}'...")
        for filename in os.listdir(self.data_directory):
            if filename.endswith(".csv"):
                file_path = os.path.join(self.data_directory, filename)
                try:
                    all_dataframes[filename] = pd.read_csv(file_path, low_memory=False)
                    print(f"  - Loaded '{filename}' successfully.")
                except Exception as e:
                    print(f"  - Failed to load '{filename}'. Error: {e}")
        return all_dataframes

    def find_entities(self, search_term):
        search_term = str(search_term).lower()
        search_cols = ['name', 'entity_id', 'email', 'card_id', 'device_hash', 'face_id', 'student_id', 'staff_id']
        combined_mask = pd.Series(False, index=self.profiles_df.index)

        for col in search_cols:
            if col in self.profiles_df.columns:
                series = self.profiles_df[col].astype(str).str.lower()
                if col == 'name':
                    mask = series.str.contains(search_term, na=False)
                else:
                    mask = (series == search_term)
                combined_mask |= mask

        matching_df = self.profiles_df[combined_mask]
        return matching_df.where(pd.notna(matching_df), None).to_dict('records')

    def generate_timeline(self, entity_identifiers):
        timeline_entries = []
        entity_id = entity_identifiers.get('entity_id')
        entity_name = entity_identifiers.get('name', 'UNKNOWN ENTITY')

        LOG_CONFIGS = self._get_log_configs(entity_identifiers)

        for filename, config in LOG_CONFIGS.items():
            if filename in self.all_data:
                df = self.all_data[filename].copy()
                search_val = config['search_val']
                search_col = config['search_col']

                if search_val is not None and search_col in df.columns:
                    df_filtered = df[df[search_col].astype(str) == str(search_val)]
                    for _, row in df_filtered.iterrows():
                        details = {col: str(row.get(col, "N/A")) for col in config['desc_cols']}
                        timeline_entries.append({
                            'Timestamp': row[config['ts_col']],
                            'Source': config['source'],
                            'Details': details,
                            'Name': entity_name
                        })

        timeline_entries.sort(key=lambda x: pd.to_datetime(x['Timestamp'], errors='coerce'))
        return self._format_timeline(timeline_entries, entity_name, entity_id)

    def _get_log_configs(self, entity_identifiers):
        card_id = entity_identifiers.get('card_id')
        device_hash = entity_identifiers.get('device_hash')
        face_id = entity_identifiers.get('face_id')
        entity_id = entity_identifiers.get('entity_id')

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
        return LOG_CONFIGS

    def _format_timeline(self, timeline_entries, entity_name, entity_id):
        if not timeline_entries:
            return f"\nTIMELINE FOR: {entity_name} (ID: {entity_id})\n{'='*30}\nNo logged activities found."

        formatted_timeline = f"\nTIMELINE FOR: {entity_name} (ID: {entity_id})\n{'='*30}\n"
        for entry in timeline_entries:
            formatted_timeline += f"{entry['Timestamp']} | Source: {entry['Source'].upper()}\n"
            for key, value in entry['Details'].items():
                display_key = key.replace('_', ' ').strip().title()
                formatted_timeline += f"    {display_key}: {value}\n"
            formatted_timeline += "\n"
        return formatted_timeline.rstrip('\n')

    def get_last_known_location(self, entity_identifiers):
        card_id = entity_identifiers.get('card_id')
        device_hash = entity_identifiers.get('device_hash')
        
        location_entries = []

        # Check card swipes
        if card_id and 'campus card_swipes.csv' in self.all_data:
            swipes_df = self.all_data['campus card_swipes.csv']
            entity_swipes = swipes_df[swipes_df['card_id'] == card_id]
            for _, row in entity_swipes.iterrows():
                location_entries.append({'timestamp': row['timestamp'], 'location': row['location_id']})

        # Check WiFi logs
        if device_hash and 'wifi_associations_logs.csv' in self.all_data:
            wifi_df = self.all_data['wifi_associations_logs.csv']
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

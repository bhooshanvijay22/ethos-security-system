import customtkinter
# Import the backend functions
from app import load_all_data, find_entities_in_profiles, get_entity_timeline, check_for_alerts

# --- GLOBAL DATA LOADING ---
# Load all data once when the application starts
print("Initializing application and loading data...")
ALL_DATA = load_all_data(data_directory="data")
PROFILES_FILENAME = "student or staff profiles.csv"
PROFILES_DF = ALL_DATA.get(PROFILES_FILENAME)
print("Data loading complete.")

# --- UI SETUP ---
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.title("Campus Security Monitor")
app.geometry("800x600")

# --- WIDGETS ---
control_frame = customtkinter.CTkFrame(app)
control_frame.pack(pady=20, padx=60, fill="x", expand=False)

label = customtkinter.CTkLabel(control_frame, text="Select Entity/Asset:")
label.pack(side="left", padx=10, pady=10)

# Populate dropdown with actual data if profiles were loaded
entity_options = ["Select..."]
if PROFILES_DF is not None:
    # Use a unique identifier like name or entity_id
    entity_options.extend(list(PROFILES_DF["name"].unique()))

entity_dropdown = customtkinter.CTkComboBox(control_frame, values=entity_options)
entity_dropdown.pack(side="left", padx=10, pady=10)
entity_dropdown.set("Select...")

# --- BUTTON CALLBACK (UPDATED LOGIC) ---
def search_button_callback():
    selected_entity = entity_dropdown.get()
    
    # Clear previous results
    result_textbox.delete("1.0", "end")

    if selected_entity == "Select..." or PROFILES_DF is None:
        result_textbox.insert("1.0", "Please select an entity from the dropdown.")
        return

    print(f"Search button clicked for: {selected_entity}")
    
    # 1. Find the full entity profile
    # Note: This assumes names are unique. For a real system, you'd handle multiple matches.
    matches = find_entities_in_profiles(selected_entity, PROFILES_DF)
    
    if not matches:
        result_textbox.insert("1.0", f"Could not find a profile for '{selected_entity}'.")
        return
        
    entity_profile = matches[0] # Taking the first match
    
    # 2. Get the chronological timeline
    timeline = get_entity_timeline(entity_profile, ALL_DATA)
    
    # 3. Check for security alerts
    alert = check_for_alerts(timeline)
    
    # 4. Format and display the results
    display_text = f"Timeline and data for: {entity_profile.get('name', 'N/A')}\n"
    display_text += f"Entity ID: {entity_profile.get('entity_id', 'N/A')}\n"
    display_text += "="*50 + "\n\n"
    
    if alert:
        display_text += f"*** {alert} ***\n\n"
        
    if not timeline:
        display_text += "No activity records found in the selected timeframe."
    else:
        for event in timeline:
            timestamp_str = event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            activity = event['activity']
            source = event['source']
            display_text += f"[{timestamp_str}] - {activity} (Source: {source})\n"
            
    result_textbox.insert("1.0", display_text)


search_button = customtkinter.CTkButton(control_frame, text="Get History", command=search_button_callback)
search_button.pack(side="left", padx=10, pady=10)

result_textbox = customtkinter.CTkTextbox(app, height=400, font=("Courier New", 12))
result_textbox.pack(pady=10, padx=60, fill="both", expand=True)
result_textbox.insert("0.0", "Results will be shown here...")

# --- RUN THE APP ---
app.mainloop()
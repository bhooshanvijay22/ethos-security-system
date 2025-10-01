import customtkinter
# 1. Import the necessary functions from app.py
from app import load_all_data, find_entities_in_profiles, generate_timeline
import pandas as pd 

# --- GLOBAL DATA INITIALIZATION ---
ALL_DATA = load_all_data() 
PROFILES_FILENAME = "student or staff profiles.csv"
PROFILES_DF = ALL_DATA.get(PROFILES_FILENAME, pd.DataFrame())

# Extract identifiers for the search list
if not PROFILES_DF.empty:
    initial_options = set()
    for col in ['name', 'entity_id', 'email']:
        if col in PROFILES_DF.columns:
            initial_options.update(PROFILES_DF[col].dropna().astype(str).unique())
    ALL_ENTITY_IDENTIFIERS = sorted(list(initial_options))
else:
    ALL_ENTITY_IDENTIFIERS = ["Data Not Loaded"]


# Set the appearance mode and default color theme
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# Create the main application window
app = customtkinter.CTk()
app.title("Campus Security Monitor")
app.geometry("1000x700")

# --- HELPER FUNCTION TO GET FULL PROFILE DATA ---
def get_profile_by_id(entity_id):
    """Fetches the full profile dictionary for a given entity_id."""
    if PROFILES_DF.empty:
        return None
        
    # Find the row where entity_id matches
    match_row = PROFILES_DF[PROFILES_DF['entity_id'] == entity_id]
    
    if not match_row.empty:
        # Convert the first matching row to a dictionary
        return match_row.iloc[0].to_dict()
    return None


# --- CORE FUNCTIONS ---

def update_dropdown(event=None):
    """Filters the list of entity identifiers based on the current text in the entry."""
    search_term = entity_entry.get().strip()
    
    if search_term:
        filtered_options = [opt for opt in ALL_ENTITY_IDENTIFIERS if search_term.lower() in opt.lower()]
    else:
        filtered_options = ALL_ENTITY_IDENTIFIERS[:10] 
    
    if not filtered_options:
        filtered_options = ["No matches found"]

    entity_dropdown.configure(values=filtered_options)
    entity_dropdown.set(search_term if search_term else "Type to Search...")

def check_timeline_callback(entity_id):
    """
    Handles the click event for a Timeline button, fetches the profile, 
    and calls the generate_timeline function.
    """
    result_textbox.delete("1.0", "end")
    result_textbox.insert("1.0", f"Fetching timeline for Entity ID: {entity_id}...\n\n")

    # 1. Get the full profile match dictionary
    entity_profile = get_profile_by_id(entity_id)

    if entity_profile:
        try:
            # 2. Call the newly implemented backend function
            timeline_text = generate_timeline(entity_profile, ALL_DATA)
            result_textbox.insert("end", timeline_text)
        except Exception as e:
            result_textbox.insert("end", f"Error generating timeline: {e}")
    else:
        result_textbox.insert("end", f"Error: Could not find profile details for ID {entity_id} to generate timeline.")


def search_button_callback():
    """
    Performs the search and dynamically creates widgets for each match found.
    """
    selected_entity = entity_entry.get().strip() 
    
    # Clear the results scroll frame before populating new results
    for widget in results_scroll_frame.winfo_children():
        widget.destroy()

    if not selected_entity:
        customtkinter.CTkLabel(results_scroll_frame, text="Please enter a search term (Name, ID, Email, etc.).").pack(padx=10, pady=5, anchor="w")
        return
        
    if PROFILES_DF.empty:
        customtkinter.CTkLabel(results_scroll_frame, text="ERROR: Profile data not loaded.").pack(padx=10, pady=5, anchor="w")
        return

    matches = find_entities_in_profiles(selected_entity, PROFILES_DF)
    
    if not matches:
        customtkinter.CTkLabel(results_scroll_frame, text=f"No profile matches found for '{selected_entity}'.", text_color="orange").pack(padx=10, pady=5, anchor="w")
        return
    
    # Header for the results
    customtkinter.CTkLabel(results_scroll_frame, text=f"Found {len(matches)} match(es) for '{selected_entity}':", font=customtkinter.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5), anchor="w")
    
    # Iterate through matches and create a display row for each
    for i, match in enumerate(matches):
        
        # --- 1. Create a sub-frame for each result to hold the text and button ---
        match_frame = customtkinter.CTkFrame(results_scroll_frame, fg_color="transparent")
        match_frame.pack(fill="x", padx=10, pady=5)
        
        # --- 2. Build the descriptive text ---
        entity_role = match.get('role', 'N/A')
        # Ensure we use 'entity_id' as the key for the timeline lookup
        entity_id = match.get('entity_id', 'N/A') 
        
        match_info = f"[{i+1}] Name: {match.get('name', 'N/A')} | ID: {entity_id} | Type: {entity_role}"
        
        if entity_role.lower() == 'student':
            department = match.get('department', 'N/A')
            match_info += f" | Dept: {department}"
        
        # --- 3. Display the details (left side) ---
        details_label = customtkinter.CTkLabel(match_frame, text=match_info, justify="left", wraplength=500)
        details_label.pack(side="left", padx=5, pady=5)

        # --- 4. Create the Timeline Button (right side) ---
        if entity_id != 'N/A':
            # IMPORTANT: Use lambda to capture the entity_id for the button's command
            timeline_button = customtkinter.CTkButton(
                match_frame, 
                text="Check Timeline", 
                width=150,
                command=lambda id=entity_id: check_timeline_callback(id)
            )
            timeline_button.pack(side="right", padx=5, pady=5)
        
        # Add a separator line
        customtkinter.CTkFrame(results_scroll_frame, height=1, fg_color="gray").pack(fill="x", padx=10)


# --- WIDGETS ---

# Control Frame (Search Bar and Dropdown)
control_frame = customtkinter.CTkFrame(app)
control_frame.pack(pady=20, padx=60, fill="x", expand=False)

label = customtkinter.CTkLabel(control_frame, text="Search Entity/Asset:")
label.pack(side="left", padx=(10, 0), pady=10)

entity_entry = customtkinter.CTkEntry(control_frame, placeholder_text="Type name, ID, or email...")
entity_entry.bind("<KeyRelease>", update_dropdown) 
entity_entry.pack(side="left", padx=(10, 5), pady=10, fill="x", expand=True)

entity_dropdown = customtkinter.CTkComboBox(
    control_frame, 
    values=ALL_ENTITY_IDENTIFIERS[:10],
    width=200
)
entity_dropdown.set("Type to Search...") 
entity_dropdown.pack(side="left", padx=5, pady=10)

search_button = customtkinter.CTkButton(control_frame, text="Search Profiles", command=search_button_callback)
search_button.pack(side="left", padx=(10, 10), pady=10)

# --- Scrollable Frame for Dynamic Search Results and Buttons ---
results_scroll_frame = customtkinter.CTkScrollableFrame(app, label_text="Profile Matches")
results_scroll_frame.pack(pady=10, padx=60, fill="x", expand=False)
results_scroll_frame.configure(height=200)

# Textbox to display the results (now dedicated for the Timeline output)
result_textbox = customtkinter.CTkTextbox(app, height=250)
result_textbox.pack(pady=10, padx=60, fill="both", expand=True)
result_textbox.insert("0.0", "Timeline results will be shown here after clicking 'Check Timeline'.")

# --- RUN THE APP ---
app.mainloop()
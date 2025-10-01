import customtkinter
# 1. Import the necessary functions from app.py
from app import load_all_data, find_entities_in_profiles
import pandas as pd # You'll need pandas for data manipulation

# --- GLOBAL DATA INITIALIZATION ---
# 2. Load all data once when the app starts
ALL_DATA = load_all_data() 
PROFILES_FILENAME = "student or staff profiles.csv"
PROFILES_DF = ALL_DATA.get(PROFILES_FILENAME, pd.DataFrame())

# Extract all names and entity IDs for the initial suggestion list
# Use a Set to store unique identifiers from the profile data
if not PROFILES_DF.empty:
    # Combine relevant columns into a single list of unique identifiers
    initial_options = set()
    for col in ['name', 'entity_id', 'email']:
        if col in PROFILES_DF.columns:
            initial_options.update(PROFILES_DF[col].dropna().astype(str).unique())
    # Sort and convert back to a list
    ALL_ENTITY_IDENTIFIERS = sorted(list(initial_options))
else:
    ALL_ENTITY_IDENTIFIERS = ["Data Not Loaded"]


# Set the appearance mode and default color theme
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# Create the main application window
app = customtkinter.CTk()
app.title("Campus Security Monitor")
app.geometry("800x600")

# --- FUNCTIONS ---

def update_dropdown(event=None):
    """
    Filters the list of entity identifiers based on the current text in the entry
    and updates the Combobox's values.
    """
    search_term = entity_entry.get().strip()
    
    # 1. Filter the global list of identifiers
    if search_term:
        filtered_options = [
            opt for opt in ALL_ENTITY_IDENTIFIERS 
            if search_term.lower() in opt.lower()
        ]
    else:
        # If the search bar is empty, show the top 10 options or a sensible default
        filtered_options = ALL_ENTITY_IDENTIFIERS[:10] 
    
    if not filtered_options:
        filtered_options = ["No matches found"]

    # 2. Update the Combobox's values
    # The Combobox will now only display these filtered options
    entity_dropdown.configure(values=filtered_options)
    
    # 3. Set the currently typed text as the displayed value in the Combobox
    # This keeps the typed text visible even after the filter updates
    entity_dropdown.set(search_term if search_term else "Type to Search...")

def search_button_callback():
    """
    Called when the 'Get History' button is pressed.
    It takes the value from the Entry widget for the search.
    """
    # Use the value from the Entry widget, which is the user's intended search term
    selected_entity = entity_entry.get().strip() 
    
    print(f"Search button clicked for: {selected_entity}")
    
    if not selected_entity:
        result_textbox.delete("1.0", "end")
        result_textbox.insert("1.0", "Please enter a search term (Name, ID, Email, etc.).")
        return
        
    # Use the imported function to find matches
    if not PROFILES_DF.empty:
        matches = find_entities_in_profiles(selected_entity, PROFILES_DF)
        
        result_textbox.delete("1.0", "end") # Clear previous text
        
        if matches:
            # Display basic profile information for the found entity
            match_summary = f"Found {len(matches)} match(es) for '{selected_entity}':\n\n"
            for i, match in enumerate(matches):
                match_summary += f"--- Entity {i+1} ---\n"
                match_summary += f"Name: {match.get('name', 'N/A')}\n"
                match_summary += f"Entity ID: {match.get('entity_id', 'N/A')}\n"
                
                # --- CORRECTED: Use 'role' column for type/role ---
                entity_role = match.get('role', 'N/A')
                match_summary += f"Type (Role): {entity_role}\n"
                
                # --- Check role and display department if it's a student ---
                # Check for "student" case-insensitively just in case of data variance
                if entity_role.lower() == 'student':
                    # Assuming the department column is named 'department'
                    department = match.get('department', 'N/A')
                    match_summary += f"Department: {department}\n"
                
                match_summary += f"Email: {match.get('email', 'N/A')}\n"
                match_summary += "\n"
            
            result_textbox.insert("1.0", match_summary)
            
            # --- NEXT: Call the timeline generation function here ---
            # timeline_text = generate_timeline(matches[0]['entity_id'], ALL_DATA)
            # result_textbox.insert("end", timeline_text)
            
        else:
            result_textbox.insert("1.0", f"ERROR: No profile found for '{selected_entity}'.\n")
            
    else:
        result_textbox.insert("1.0", "ERROR: Profile data is not loaded. Check 'data/' folder and file name.\n")

# --- WIDGETS ---

# Frame for the controls
control_frame = customtkinter.CTkFrame(app)
control_frame.pack(pady=20, padx=60, fill="x", expand=False)

# Label
label = customtkinter.CTkLabel(control_frame, text="Search Entity/Asset:")
label.pack(side="left", padx=(10, 0), pady=10)

# 1. Search Entry (The main text input for typing)
entity_entry = customtkinter.CTkEntry(control_frame, placeholder_text="Type name, ID, or email...")
# Bind the <KeyRelease> event to the update_dropdown function
entity_entry.bind("<KeyRelease>", update_dropdown) 
entity_entry.pack(side="left", padx=(10, 5), pady=10, fill="x", expand=True)

# 2. Filtered Dropdown (Displays the suggested matches)
entity_dropdown = customtkinter.CTkComboBox(
    control_frame, 
    values=ALL_ENTITY_IDENTIFIERS[:10], # Initial small list
    width=200 # Fixed width for a compact look
)
entity_dropdown.set("Type to Search...") 
entity_dropdown.pack(side="left", padx=5, pady=10)

# Button to trigger the search
search_button = customtkinter.CTkButton(control_frame, text="Get History", command=search_button_callback)
search_button.pack(side="left", padx=(10, 10), pady=10)

# Textbox to display the results
result_textbox = customtkinter.CTkTextbox(app, height=400)
result_textbox.pack(pady=10, padx=60, fill="both", expand=True)
result_textbox.insert("0.0", "Results will be shown here...")

# --- RUN THE APP ---
app.mainloop()
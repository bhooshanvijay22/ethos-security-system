import customtkinter
# Import the necessary functions from app.py
from app import load_all_data, find_entities_in_profiles, generate_timeline
import pandas as pd
import os
from PIL import Image

# --- GLOBAL DATA INITIALIZATION ---
ALL_DATA = load_all_data()
PROFILES_FILENAME = "student or staff profiles.csv"
PROFILES_DF = ALL_DATA.get(PROFILES_FILENAME, pd.DataFrame())
# Define the directory where face images are stored
FACE_IMAGE_DIR = r"C:\Users\nirbh\ethos-security-system\data\face_images"

# --- COMBOBOX DATA PREPARATION ---
# Extract unique identifiers for the dynamic dropdown menu
if not PROFILES_DF.empty:
    initial_options = set()
    # Collect unique values from key search columns
    for col in ['name', 'entity_id', 'email', 'card_id', 'device_hash']:
        if col in PROFILES_DF.columns:
            # Drop NaN, convert to string, and get unique values
            initial_options.update(PROFILES_DF[col].dropna().astype(str).unique())
    # Sort and convert to list for the Combobox
    ALL_ENTITY_IDENTIFIERS = sorted(list(initial_options))
else:
    # Fallback if data loading fails
    ALL_ENTITY_IDENTIFIERS = ["Data Not Loaded"]

# Define the text to use as a placeholder
PLACEHOLDER_TEXT = "Select or type name, ID, or email..."

# --- APP SETUP ---
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")
app = customtkinter.CTk()
app.title("Campus Security Monitor")
app.geometry("1000x550")

# --- HELPER FUNCTIONS ---
def get_profile_by_id(entity_id):
    """Fetches the full profile dictionary for a given entity_id."""
    if PROFILES_DF.empty:
        return None
    # Find the row where entity_id matches
    match_row = PROFILES_DF[PROFILES_DF['entity_id'] == entity_id]
    # Convert the first matching row to a dictionary
    return match_row.iloc[0].to_dict() if not match_row.empty else None

def dynamic_combobox_filter(event=None):
    """Filters the combobox options based on the text currently in the entry field."""
    typed_text = entity_combobox.get().strip().lower()
    
    # Check if the current value is the placeholder. If so, show all options.
    if typed_text == PLACEHOLDER_TEXT.lower() or not typed_text:
        entity_combobox.configure(values=ALL_ENTITY_IDENTIFIERS)
        return

    # Filter the identifiers list
    filtered_options = [
        item for item in ALL_ENTITY_IDENTIFIERS 
        if typed_text in item.lower()
    ]
    
    # Update the combobox with the filtered values
    if filtered_options:
        entity_combobox.configure(values=filtered_options)
    else:
        # If no matches, set to an empty list to prevent showing all old values
        entity_combobox.configure(values=[])
        
    # The Combobox text should remain what the user is typing
    entity_combobox.set(typed_text)

def set_placeholder(event):
    """Clears the placeholder text when the combobox is clicked/focused."""
    current_value = entity_combobox.get()
    if current_value == PLACEHOLDER_TEXT:
        entity_combobox.set("")
        # Reset the values to all options when the user starts typing
        entity_combobox.configure(values=ALL_ENTITY_IDENTIFIERS)

def restore_placeholder(event):
    """Restores the placeholder text if the field is empty upon losing focus."""
    current_value = entity_combobox.get().strip()
    if not current_value:
        entity_combobox.set(PLACEHOLDER_TEXT)
        # Reset values to all options just in case
        entity_combobox.configure(values=ALL_ENTITY_IDENTIFIERS)


def hide_all_extra_views():
    """Hides Timeline and Image views and shows the Profile Matches view."""
    # 1. Hide all extra widgets
    timeline_close_button.pack_forget()
    result_textbox.pack_forget()
    image_frame.pack_forget()
    
    # 2. Shrink the window back
    app.geometry("1000x550")
    
    # 3. Show the Profile Matches frame again
    results_label.pack(pady=(10, 0), padx=60, anchor="w")
    results_scroll_frame.pack(pady=10, padx=60, fill="both", expand=True)

# Aliases for convenience:
hide_timeline_view = hide_all_extra_views
hide_image_view = hide_all_extra_views

def show_timeline_view():
    """Hides other views and shows the Timeline widgets."""
    # 1. Hide the Profile Matches frame and Image View widgets
    results_label.pack_forget()
    results_scroll_frame.pack_forget()
    image_frame.pack_forget()
    
    # 2. Show the Timeline widgets
    app.geometry("1000x700")
    timeline_close_button.pack(pady=(10, 5), padx=60, anchor="e")
    result_textbox.pack(pady=(0, 10), padx=60, fill="both", expand=True)

def show_image_view(image_path, entity_name):
    """Hides other views and shows the Image Frame."""
    # 1. Hide other view widgets
    results_label.pack_forget()
    results_scroll_frame.pack_forget()
    timeline_close_button.pack_forget()
    result_textbox.pack_forget()

    # 2. Configure and show the Image Frame
    app.geometry("1000x700")
    image_frame.pack(pady=10, padx=60, fill="both", expand=True)
    image_close_button.pack(pady=(10, 5), padx=5, anchor="e")

    # Clear previous image and set loading text
    image_label.configure(image=None, text=f"Loading Face Image for: {entity_name}...")
    image_label.pack(fill="both", expand=True, padx=20, pady=20)

    # Attempt to load and display the image
    try:
        if not os.path.exists(FACE_IMAGE_DIR):
             raise FileNotFoundError(f"Directory not found: {FACE_IMAGE_DIR}")

        img = Image.open(image_path)
        # Resize image to fit
        max_size = (600, 600)
        img.thumbnail(max_size)

        ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        image_label.configure(image=ctk_img, text=f"Facial Profile: {entity_name}", compound="top")
        image_label.image = ctk_img # Keep a reference
    except FileNotFoundError:
        image_label.configure(text=f"Facial Profile for: {entity_name}\n\nERROR: Image not found.\nExpected file: {image_path}", image=None)
    except Exception as e:
        image_label.configure(text=f"Facial Profile for: {entity_name}\n\nERROR loading image: {e}", image=None)

# --- CORE CALLBACKS ---
def view_face_callback(entity_id):
    """Handles the click event for the View Face button, constructing the path and calling show_image_view."""
    entity_profile = get_profile_by_id(entity_id)

    if not entity_profile:
        print(f"Error: Could not find profile details for ID {entity_id}.")
        return

    face_id = entity_profile.get('face_id')
    entity_name = entity_profile.get('name', 'N/A')

    if not face_id:
        print(f"Warning: Profile for {entity_name} (ID: {entity_id}) does not have a 'face_id'.")
        return

    # Construct the expected image file path
    image_filename = f"{face_id}.jpg"
    image_path = os.path.join(FACE_IMAGE_DIR, image_filename)

    show_image_view(image_path, entity_name)

def check_timeline_callback(entity_id):
    """Fetches the profile, generates the timeline, and displays the result in the textbox."""
    show_timeline_view()

    result_textbox.delete("1.0", "end")
    result_textbox.insert("1.0", f"Fetching timeline for Entity ID: {entity_id}...\n\n")

    entity_profile = get_profile_by_id(entity_id)

    if entity_profile:
        try:
            timeline_text = generate_timeline(entity_profile, ALL_DATA)
            result_textbox.insert("end", timeline_text)
        except Exception as e:
            result_textbox.insert("end", f"Error generating timeline: {e}")
    else:
        result_textbox.insert("end", f"Error: Could not find profile details for ID {entity_id} to generate timeline.")

def create_match_widget(parent_frame, match, index):
    """Helper function to dynamically create the frame, label, and buttons for a single profile match result."""
    match_frame = customtkinter.CTkFrame(parent_frame, fg_color="transparent")
    match_frame.pack(fill="x", padx=10, pady=5)

    entity_role = match.get('role', 'N/A')
    entity_id = match.get('entity_id', 'N/A')
    face_id = match.get('face_id', 'N/A')
    entity_name = match.get('name', 'N/A')

    # Construct the display string for the match details
    match_info = f"[{index+1}] Name: {entity_name} | ID: {entity_id} | Type: {entity_role}"
    if entity_role.lower() == 'student':
        match_info += f" | Dept: {match.get('department', 'N/A')}"

    details_label = customtkinter.CTkLabel(match_frame, text=match_info, justify="left", wraplength=500)
    details_label.pack(side="left", padx=5, pady=5)

    # Frame to hold the buttons on the right side
    button_frame = customtkinter.CTkFrame(match_frame, fg_color="transparent")
    button_frame.pack(side="right", padx=5, pady=5)

    if entity_id != 'N/A':
        # --- BUTTON: View Face ---
        if face_id != 'N/A':
            customtkinter.CTkButton(
                button_frame,
                text="View Face 📷",
                width=120,
                fg_color="darkgreen",
                hover_color="green",
                command=lambda id=entity_id: view_face_callback(id)
            ).pack(side="right", padx=5, pady=5)

        # --- BUTTON: Check Timeline ---
        customtkinter.CTkButton(
            button_frame,
            text="Check Timeline",
            width=150,
            command=lambda id=entity_id: check_timeline_callback(id)
        ).pack(side="right", padx=5, pady=5)

    # Separator line
    customtkinter.CTkFrame(parent_frame, height=1, fg_color="gray").pack(fill="x", padx=10)

def search_button_callback():
    """Performs the search, clears previous results, and dynamically creates widgets for each match found."""
    # Get the value from the Combobox (it can be selected or typed)
    selected_entity = entity_combobox.get().strip()
    
    # Check if the placeholder text is still present
    if selected_entity == PLACEHOLDER_TEXT:
        selected_entity = ""

    hide_all_extra_views()
    # Clear previous results
    for widget in results_scroll_frame.winfo_children():
        widget.destroy()

    # Handle different search states (empty query, data error, no matches, successful matches)
    if not selected_entity:
        text = "Please enter a search term (Name, ID, Email, etc.)."
    elif PROFILES_DF.empty:
        text = "ERROR: Profile data not loaded."
    else:
        matches = find_entities_in_profiles(selected_entity, PROFILES_DF)
        if not matches:
            text = f"No profile matches found for '{selected_entity}'.", "orange"
        else:
            # Display match count label
            customtkinter.CTkLabel(results_scroll_frame, text=f"Found {len(matches)} match(es) for '{selected_entity}':", font=customtkinter.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5), anchor="w")
            # Create widgets for each match
            for i, match in enumerate(matches):
                create_match_widget(results_scroll_frame, match, i)
            return # Exit since successful matches were handled

    # If the function reaches here, it means it's a non-match/error scenario
    label_text = text if isinstance(text, str) else text[0]
    label_color = "white" if isinstance(text, str) else text[1]

    customtkinter.CTkLabel(results_scroll_frame, text=label_text, text_color=label_color).pack(padx=10, pady=5, anchor="w")


# --- WIDGETS ---

# Control Frame (Search Bar)
control_frame = customtkinter.CTkFrame(app); control_frame.pack(pady=20, padx=60, fill="x")
customtkinter.CTkLabel(control_frame, text="Search Entity/Asset:").pack(side="left", padx=(10, 0), pady=10)

# The Combobox widget (dynamic dropdown + entry)
entity_combobox = customtkinter.CTkComboBox(
    control_frame, 
    values=ALL_ENTITY_IDENTIFIERS,
    command=None, 
)
# Manually set the placeholder text and bind the events
entity_combobox.set(PLACEHOLDER_TEXT)
entity_combobox.bind("<FocusIn>", set_placeholder)
entity_combobox.bind("<FocusOut>", restore_placeholder)
# BIND THE KEY RELEASE EVENT FOR DYNAMIC FILTERING
entity_combobox.bind("<KeyRelease>", dynamic_combobox_filter)
entity_combobox.pack(side="left", padx=(10, 5), pady=10, fill="x", expand=True)

# Search button
customtkinter.CTkButton(control_frame, text="Search Profiles", command=search_button_callback).pack(side="left", padx=(10, 10), pady=10)

# Profile Matches View Widgets
results_label = customtkinter.CTkLabel(app, text="Profile Matches", font=customtkinter.CTkFont(weight="bold"))
# Scrollable Frame for Dynamic Search Results and Buttons
results_scroll_frame = customtkinter.CTkScrollableFrame(app, height=200)

# Timeline View Widgets
# Button to close the timeline (and return to matches)
timeline_close_button = customtkinter.CTkButton(app, text="Back to Matches ⬅", width=150, command=hide_all_extra_views)
# Textbox to display the results (Timeline output)
result_textbox = customtkinter.CTkTextbox(app, height=250)
result_textbox.insert("0.0", "Timeline results will be shown here after clicking 'Check Timeline'.")

# Image View Widgets
# Frame to hold the image and the back button
image_frame = customtkinter.CTkFrame(app)
# Button to close the image view (and return to matches)
image_close_button = customtkinter.CTkButton(image_frame, text="Back to Matches ⬅", width=150, command=hide_all_extra_views)
# Label to display the image (or a placeholder text)
image_label = customtkinter.CTkLabel(image_frame, text="Image placeholder.", justify="center", font=customtkinter.CTkFont(size=16))


# --- RUN THE APP ---
hide_all_extra_views() # Start with the search view
app.mainloop()
import customtkinter
# 1. Import the necessary functions from app.py
from app import load_all_data, find_entities_in_profiles, generate_timeline
import pandas as pd 
import os 
from PIL import Image # Need PIL to handle images

# --- GLOBAL DATA INITIALIZATION ---
ALL_DATA = load_all_data() 
PROFILES_FILENAME = "student or staff profiles.csv"
PROFILES_DF = ALL_DATA.get(PROFILES_FILENAME, pd.DataFrame())

# Define the directory where face images are stored
FACE_IMAGE_DIR = r"C:\Users\nirbh\ethos-security-system\data\face_images"

# Extract identifiers for the search list (No longer strictly needed for dropdown, but kept for data reference)
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
app.geometry("1000x550") 

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

# --- UI VISIBILITY FUNCTIONS ---

def show_timeline_view():
    """Hides other views and shows the Timeline widgets."""
    
    # 1. Hide the Profile Matches frame, its label, and Image View widgets
    results_label.pack_forget()
    results_scroll_frame.pack_forget()
    image_frame.pack_forget() 
    
    # 2. Show the Timeline widgets
    app.geometry("1000x700") 
    timeline_close_button.pack(pady=(10, 5), padx=60, anchor="e")
    result_textbox.pack(pady=(0, 10), padx=60, fill="both", expand=True)

def show_image_view(image_path, entity_name):
    """Hides other views and shows the Image Frame."""
    
    # 1. Hide the Profile Matches frame, its label, and Timeline widgets
    results_label.pack_forget()
    results_scroll_frame.pack_forget()
    timeline_close_button.pack_forget()
    result_textbox.pack_forget()
    
    # 2. Configure and show the Image Frame
    app.geometry("1000x700") 
    
    # Pack the frame first
    image_frame.pack(pady=10, padx=60, fill="both", expand=True)
    # Pack the back button inside the frame
    image_close_button.pack(pady=(10, 5), padx=5, anchor="e") 
    
    # Clear previous image or text
    image_label.configure(image=None, text=f"Loading Face Image for: {entity_name}...")
    image_label.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Attempt to load and display the image
    try:
        if not os.path.exists(FACE_IMAGE_DIR):
             image_label.configure(text=f"ERROR: Face image directory not found.\nExpected path: {FACE_IMAGE_DIR}")
             return
             
        img = Image.open(image_path)
        # Resize image to fit, maintaining aspect ratio (example resize logic)
        max_size = (600, 600)
        img.thumbnail(max_size) 
        
        ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        image_label.configure(image=ctk_img, text=f"Facial Profile: {entity_name}", compound="top")
        image_label.image = ctk_img # Keep a reference
        
    except FileNotFoundError:
        image_label.configure(text=f"Facial Profile for: {entity_name}\n\nERROR: Image not found.\nExpected file: {image_path}", image=None)
    except Exception as e:
        image_label.configure(text=f"Facial Profile for: {entity_name}\n\nERROR loading image: {e}", image=None)


def hide_all_extra_views():
    """Hides Timeline and Image views and shows the Profile Matches view."""
    
    # Hide all extra widgets
    timeline_close_button.pack_forget()
    result_textbox.pack_forget()
    image_frame.pack_forget()
    
    # Shrink the window back
    app.geometry("1000x550") 
    
    # Show the Profile Matches frame again
    results_label.pack(pady=(10, 0), padx=60, anchor="w")
    results_scroll_frame.pack(pady=10, padx=60, fill="both", expand=True)

# Alias for convenience:
hide_timeline_view = hide_all_extra_views 
hide_image_view = hide_all_extra_views 


# --- CORE FUNCTION FOR VIEW FACE ---

def view_face_callback(entity_id):
    """
    Handles the click event for the View Face button.
    """
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

    # Show the image view
    show_image_view(image_path, entity_name)


# --- CORE FUNCTIONS (SIMPLIFIED) ---

# The combobox_callback and update_dropdown functions are no longer needed.

def check_timeline_callback(entity_id):
    """
    Handles the click event for a Timeline button, fetches the profile, 
    and calls the generate_timeline function. Also shows the timeline view.
    """
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


def search_button_callback():
    """
    Performs the search and dynamically creates widgets for each match found.
    Now relies only on the text in the entry box.
    """
    selected_entity = entity_entry.get().strip() 
    
    hide_all_extra_views()
    
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
    
    customtkinter.CTkLabel(results_scroll_frame, text=f"Found {len(matches)} match(es) for '{selected_entity}':", font=customtkinter.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5), anchor="w")
    
    for i, match in enumerate(matches):
        
        match_frame = customtkinter.CTkFrame(results_scroll_frame, fg_color="transparent")
        match_frame.pack(fill="x", padx=10, pady=5)
        
        entity_role = match.get('role', 'N/A')
        entity_id = match.get('entity_id', 'N/A') 
        face_id = match.get('face_id', 'N/A') 
        
        match_info = f"[{i+1}] Name: {match.get('name', 'N/A')} | ID: {entity_id} | Type: {entity_role}"
        
        if entity_role.lower() == 'student':
            department = match.get('department', 'N/A')
            match_info += f" | Dept: {department}"
        
        details_label = customtkinter.CTkLabel(match_frame, text=match_info, justify="left", wraplength=500)
        details_label.pack(side="left", padx=5, pady=5)
        
        # Frame to hold the buttons on the right side
        button_frame = customtkinter.CTkFrame(match_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=5, pady=5)

        if entity_id != 'N/A':
            
            # --- BUTTON: View Face ---
            if face_id != 'N/A':
                face_button = customtkinter.CTkButton(
                    button_frame, 
                    text="View Face 📷", 
                    width=120,
                    fg_color="darkgreen", 
                    hover_color="green",
                    command=lambda id=entity_id: view_face_callback(id) 
                )
                face_button.pack(side="right", padx=5, pady=5)
            
            # --- BUTTON: Check Timeline ---
            timeline_button = customtkinter.CTkButton(
                button_frame, 
                text="Check Timeline", 
                width=150,
                command=lambda id=entity_id: check_timeline_callback(id) 
            )
            timeline_button.pack(side="right", padx=5, pady=5)
        
        customtkinter.CTkFrame(results_scroll_frame, height=1, fg_color="gray").pack(fill="x", padx=10)


# --- WIDGETS ---

# Control Frame (Search Bar)
control_frame = customtkinter.CTkFrame(app)
control_frame.pack(pady=20, padx=60, fill="x", expand=False)

label = customtkinter.CTkLabel(control_frame, text="Search Entity/Asset:")
label.pack(side="left", padx=(10, 0), pady=10)

# The primary search entry
entity_entry = customtkinter.CTkEntry(control_frame, placeholder_text="Type name, ID, or email...")
# Removed .bind("<KeyRelease>", update_dropdown) as the dropdown is gone
entity_entry.pack(side="left", padx=(10, 5), pady=10, fill="x", expand=True)

# The old dropdown widget is now removed.

search_button = customtkinter.CTkButton(control_frame, text="Search Profiles", command=search_button_callback)
search_button.pack(side="left", padx=(10, 10), pady=10)

# --- Profile Matches View ---

# Label for the Profile Matches section
results_label = customtkinter.CTkLabel(app, text="Profile Matches", font=customtkinter.CTkFont(weight="bold"))

# Scrollable Frame for Dynamic Search Results and Buttons
results_scroll_frame = customtkinter.CTkScrollableFrame(app) 
results_scroll_frame.configure(height=200) 

# --- WIDGETS FOR TIMELINE VIEW ---

# Button to close the timeline (and return to matches)
timeline_close_button = customtkinter.CTkButton(
    app, 
    text="Back to Matches ⬅", 
    width=150, 
    command=hide_all_extra_views
)

# Textbox to display the results (Timeline output)
result_textbox = customtkinter.CTkTextbox(app, height=250)
result_textbox.insert("0.0", "Timeline results will be shown here after clicking 'Check Timeline'.")


# --- WIDGETS FOR IMAGE VIEW ---

# Frame to hold the image and the back button
image_frame = customtkinter.CTkFrame(app) 

# Button to close the image view (and return to matches)
image_close_button = customtkinter.CTkButton(
    image_frame, 
    text="Back to Matches ⬅", 
    width=150, 
    command=hide_all_extra_views
)

# Label to display the image (or a placeholder text)
image_label = customtkinter.CTkLabel(
    image_frame, 
    text="Image placeholder.", 
    justify="center",
    font=customtkinter.CTkFont(size=16)
)


# --- RUN THE APP ---
hide_all_extra_views() # Start with the search view
app.mainloop()
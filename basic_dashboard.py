import customtkinter
# --- NEW --- Import prediction functions
from app import load_all_data, find_entities_in_profiles, generate_timeline, train_location_predictor, get_last_known_location, predict_next_location
import pandas as pd
import os
from PIL import Image

# --- GLOBAL DATA & MODEL INITIALIZATION ---
ALL_DATA = load_all_data()
PROFILES_FILENAME = "profiles_cleaned.csv"
PROFILES_DF = ALL_DATA.get(PROFILES_FILENAME, pd.DataFrame())
FACE_IMAGE_DIR = r"data\face_images"

# --- NEW --- Train the ML model when the app starts
print("\n--- Training Location Predictor Model ---")
LOCATION_MODEL, ENTITY_ENCODER, LOC_ENCODER = train_location_predictor(ALL_DATA)
if LOCATION_MODEL:
    print("Model ready for predictions.")
else:
    print("Could not train model. Prediction feature will be disabled.")
# --- END NEW ---

# --- COMBOBOX DATA PREPARATION ---
if not PROFILES_DF.empty:
    initial_options = set()
    for col in ['name', 'entity_id', 'email', 'card_id', 'device_hash']:
        if col in PROFILES_DF.columns:
            initial_options.update(PROFILES_DF[col].dropna().astype(str).unique())
    ALL_ENTITY_IDENTIFIERS = sorted(list(initial_options))
else:
    ALL_ENTITY_IDENTIFIERS = ["Data Not Loaded"]
PLACEHOLDER_TEXT = "Select or type name, ID, or email..."

# --- APP SETUP ---
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")
app = customtkinter.CTk()
app.title("Campus Security Monitor")
app.geometry("1000x550")

# --- HELPER FUNCTIONS ---
def get_profile_by_id(entity_id):
    if PROFILES_DF.empty: return None
    match_row = PROFILES_DF[PROFILES_DF['entity_id'] == entity_id]
    return match_row.iloc[0].to_dict() if not match_row.empty else None

def dynamic_combobox_filter(event=None):
    typed_text = entity_combobox.get().strip().lower()
    if typed_text == PLACEHOLDER_TEXT.lower() or not typed_text:
        entity_combobox.configure(values=ALL_ENTITY_IDENTIFIERS)
        return
    filtered_options = [item for item in ALL_ENTITY_IDENTIFIERS if typed_text in item.lower()]
    entity_combobox.configure(values=filtered_options if filtered_options else [])
    entity_combobox.set(typed_text)

def set_placeholder(event):
    if entity_combobox.get() == PLACEHOLDER_TEXT:
        entity_combobox.set("")
        entity_combobox.configure(values=ALL_ENTITY_IDENTIFIERS)

def restore_placeholder(event):
    if not entity_combobox.get().strip():
        entity_combobox.set(PLACEHOLDER_TEXT)
        entity_combobox.configure(values=ALL_ENTITY_IDENTIFIERS)

def hide_all_extra_views():
    timeline_close_button.pack_forget()
    result_textbox.pack_forget()
    image_frame.pack_forget()
    app.geometry("1000x550")
    results_label.pack(pady=(10, 0), padx=60, anchor="w")
    results_scroll_frame.pack(pady=10, padx=60, fill="both", expand=True)

hide_timeline_view = hide_all_extra_views
hide_image_view = hide_all_extra_views

def show_timeline_view():
    results_label.pack_forget()
    results_scroll_frame.pack_forget()
    image_frame.pack_forget()
    app.geometry("1000x700")
    timeline_close_button.pack(pady=(10, 5), padx=60, anchor="e")
    result_textbox.pack(pady=(0, 10), padx=60, fill="both", expand=True)

def show_image_view(image_path, entity_name):
    results_label.pack_forget()
    results_scroll_frame.pack_forget()
    timeline_close_button.pack_forget()
    result_textbox.pack_forget()
    app.geometry("1000x700")
    image_frame.pack(pady=10, padx=60, fill="both", expand=True)
    image_close_button.pack(pady=(10, 5), padx=5, anchor="e")
    image_label.configure(image=None, text=f"Loading Face Image for: {entity_name}...")
    image_label.pack(fill="both", expand=True, padx=20, pady=20)
    try:
        if not os.path.exists(FACE_IMAGE_DIR): raise FileNotFoundError(f"Directory not found: {FACE_IMAGE_DIR}")
        img = Image.open(image_path)
        img.thumbnail((600, 600))
        ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        image_label.configure(image=ctk_img, text=f"Facial Profile: {entity_name}", compound="top")
    except FileNotFoundError:
        image_label.configure(text=f"Facial Profile for: {entity_name}\n\nERROR: Image not found.\nExpected file: {image_path}", image=None)
    except Exception as e:
        image_label.configure(text=f"Facial Profile for: {entity_name}\n\nERROR loading image: {e}", image=None)

# --- CORE CALLBACKS ---
def view_face_callback(entity_id):
    entity_profile = get_profile_by_id(entity_id)
    if not entity_profile: return
    face_id = entity_profile.get('face_id')
    entity_name = entity_profile.get('name', 'N/A')
    if not face_id: return
    image_path = os.path.join(FACE_IMAGE_DIR, f"{face_id}.jpg")
    show_image_view(image_path, entity_name)

def check_timeline_callback(entity_id):
    show_timeline_view()
    result_textbox.delete("1.0", "end")
    result_textbox.insert("1.0", f"Fetching timeline for Entity ID: {entity_id}...\n")
    entity_profile = get_profile_by_id(entity_id)
    if entity_profile:
        timeline_text = generate_timeline(entity_profile, ALL_DATA)
        result_textbox.insert("end", timeline_text)
    else:
        result_textbox.insert("end", f"Error: Could not find profile details for ID {entity_id}.")

# --- NEW --- Callback for the prediction button
def predict_location_callback(entity_id):
    """Handles the prediction logic and displays the result in the timeline view."""
    show_timeline_view()
    result_textbox.delete("1.0", "end")
    result_textbox.insert("1.0", f"Running prediction for Entity ID: {entity_id}...\n\n")

    entity_profile = get_profile_by_id(entity_id)
    if not entity_profile:
        result_textbox.insert("end", f"Error: Could not find profile details for ID {entity_id}.")
        return

    # 1. Get the last known location from the backend
    last_location, justification = get_last_known_location(entity_profile, ALL_DATA)
    result_textbox.insert("end", f"Justification: {justification}\n\n")

    # 2. If a location was found, run the prediction
    if last_location:
        prediction_result = predict_next_location(
            entity_id, last_location, LOCATION_MODEL, ENTITY_ENCODER, LOC_ENCODER
        )
        result_textbox.insert("end", f"RESULT: {prediction_result}")
    else:
        # The justification already contains the error message (e.g., "No location history...")
        pass

def create_match_widget(parent_frame, match, index):
    match_frame = customtkinter.CTkFrame(parent_frame, fg_color="transparent")
    match_frame.pack(fill="x", padx=10, pady=5)

    entity_role = match.get('role', 'N/A')
    entity_id = match.get('entity_id', 'N/A')
    face_id = match.get('face_id', 'N/A')
    entity_name = match.get('name', 'N/A')

    match_info = f"[{index+1}] Name: {entity_name} | ID: {entity_id} | Type: {entity_role}"
    if entity_role.lower() == 'student':
        match_info += f" | Dept: {match.get('department', 'N/A')}"

    customtkinter.CTkLabel(match_frame, text=match_info, justify="left", wraplength=400).pack(side="left", padx=5, pady=5, expand=True, fill='x')
    button_frame = customtkinter.CTkFrame(match_frame, fg_color="transparent")
    button_frame.pack(side="right", padx=5, pady=5)

    if entity_id != 'N/A':
        # --- NEW --- Button for Prediction
        if LOCATION_MODEL: # Only show the button if the model was trained successfully
            customtkinter.CTkButton(
                button_frame, text="Predict 🔮", width=100, fg_color="#581845", hover_color="#C70039",
                command=lambda id=entity_id: predict_location_callback(id)
            ).pack(side="right", padx=5, pady=5)
        # --- END NEW ---

        if face_id != 'N/A':
            customtkinter.CTkButton(
                button_frame, text="View Face 📷", width=120, fg_color="darkgreen", hover_color="green",
                command=lambda id=entity_id: view_face_callback(id)
            ).pack(side="right", padx=5, pady=5)

        customtkinter.CTkButton(
            button_frame, text="Check Timeline", width=150,
            command=lambda id=entity_id: check_timeline_callback(id)
        ).pack(side="right", padx=5, pady=5)

    customtkinter.CTkFrame(parent_frame, height=1, fg_color="gray").pack(fill="x", padx=10)

def search_button_callback():
    selected_entity = entity_combobox.get().strip()
    if selected_entity == PLACEHOLDER_TEXT: selected_entity = ""
    hide_all_extra_views()
    for widget in results_scroll_frame.winfo_children(): widget.destroy()

    if not selected_entity:
        text = "Please enter a search term (Name, ID, Email, etc.)."
    elif PROFILES_DF.empty:
        text = "ERROR: Profile data not loaded."
    else:
        matches = find_entities_in_profiles(selected_entity, PROFILES_DF)
        if not matches:
            text = (f"No profile matches found for '{selected_entity}'.", "orange")
        else:
            customtkinter.CTkLabel(results_scroll_frame, text=f"Found {len(matches)} match(es) for '{selected_entity}':", font=customtkinter.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5), anchor="w")
            for i, match in enumerate(matches):
                create_match_widget(results_scroll_frame, match, i)
            return

    label_text, label_color = (text, "white") if isinstance(text, str) else text
    customtkinter.CTkLabel(results_scroll_frame, text=label_text, text_color=label_color).pack(padx=10, pady=5, anchor="w")

# --- WIDGETS ---
control_frame = customtkinter.CTkFrame(app); control_frame.pack(pady=20, padx=60, fill="x")
customtkinter.CTkLabel(control_frame, text="Search Entity/Asset:").pack(side="left", padx=(10, 0), pady=10)
entity_combobox = customtkinter.CTkComboBox(control_frame, values=ALL_ENTITY_IDENTIFIERS)
entity_combobox.set(PLACEHOLDER_TEXT)
entity_combobox.bind("<FocusIn>", set_placeholder)
entity_combobox.bind("<FocusOut>", restore_placeholder)
entity_combobox.bind("<KeyRelease>", dynamic_combobox_filter)
entity_combobox.pack(side="left", padx=(10, 5), pady=10, fill="x", expand=True)
customtkinter.CTkButton(control_frame, text="Search Profiles", command=search_button_callback).pack(side="left", padx=(10, 10), pady=10)

results_label = customtkinter.CTkLabel(app, text="Profile Matches", font=customtkinter.CTkFont(weight="bold"))
results_scroll_frame = customtkinter.CTkScrollableFrame(app, height=200)

timeline_close_button = customtkinter.CTkButton(app, text="Back to Matches ⬅", width=150, command=hide_all_extra_views)
result_textbox = customtkinter.CTkTextbox(app, height=250, font=("Courier New", 12))
result_textbox.insert("0.0", "Results will be shown here.")

image_frame = customtkinter.CTkFrame(app)
image_close_button = customtkinter.CTkButton(image_frame, text="Back to Matches ⬅", width=150, command=hide_all_extra_views)
image_label = customtkinter.CTkLabel(image_frame, text="", justify="center", font=customtkinter.CTkFont(size=16))

# --- RUN THE APP ---
hide_all_extra_views()
app.mainloop()
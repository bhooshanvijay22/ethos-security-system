import customtkinter

# Set the appearance mode and default color theme
customtkinter.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

# Create the main application window
app = customtkinter.CTk()
app.title("Campus Security Monitor")
app.geometry("800x600")

# --- WIDGETS ---

# Create a frame for the controls
control_frame = customtkinter.CTkFrame(app)
control_frame.pack(pady=20, padx=60, fill="x", expand=False)

# Label for the dropdown
label = customtkinter.CTkLabel(control_frame, text="Select Entity/Asset:")
label.pack(side="left", padx=10, pady=10)

# Dropdown for queries (as required by the challenge)
# We'll populate this with dummy data for now
entity_options = ["Student-101", "Staff-205", "Asset-Laptop-5", "Device-ABC123"]
entity_dropdown = customtkinter.CTkComboBox(control_frame, values=entity_options)
entity_dropdown.pack(side="left", padx=10, pady=10)
entity_dropdown.set("Select...") # Set a default value

# Button to trigger the search
def search_button_callback():
    selected_entity = entity_dropdown.get()
    print(f"Search button clicked for: {selected_entity}")
    # Later, this will call your backend logic to fetch the timeline
    # For now, we just update the textbox
    result_textbox.delete("1.0", "end") # Clear previous text
    result_textbox.insert("1.0", f"Timeline and data for {selected_entity} will be displayed here.\n\n")

search_button = customtkinter.CTkButton(control_frame, text="Get History", command=search_button_callback)
search_button.pack(side="left", padx=10, pady=10)

# Textbox to display the results (timeline, alerts, etc.)
result_textbox = customtkinter.CTkTextbox(app, height=400)
result_textbox.pack(pady=10, padx=60, fill="both", expand=True)
result_textbox.insert("0.0", "Results will be shown here...")

# --- RUN THE APP ---
app.mainloop()
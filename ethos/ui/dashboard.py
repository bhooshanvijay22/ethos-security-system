import customtkinter
import pandas as pd
import os
from PIL import Image
from ethos import config

class DashboardApp:
    """
    The main application class for the security dashboard UI.
    """
    PLACEHOLDER_TEXT = config.PLACEHOLDER_TEXT
    FACE_IMAGE_DIR = config.FACE_IMAGE_DIR

    def __init__(self, data_processor, location_predictor):
        self.data_processor = data_processor
        self.location_predictor = location_predictor
        self.profiles_df = data_processor.profiles_df
        self.all_entity_identifiers = self._get_all_entity_identifiers()

        self.app = customtkinter.CTk()
        self.app.title("Campus Security Monitor")
        self.app.geometry("1000x550")
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")

        self._create_widgets()

    def run(self):
        """Runs the main application loop."""
        self.hide_all_extra_views()
        self.app.mainloop()

    def _get_all_entity_identifiers(self):
        """Gathers all unique identifiers from the profiles DataFrame."""
        if self.profiles_df.empty:
            return ["Data Not Loaded"]
        
        initial_options = set()
        for col in ['name', 'entity_id', 'email', 'card_id', 'device_hash']:
            if col in self.profiles_df.columns:
                initial_options.update(self.profiles_df[col].dropna().astype(str).unique())
        return sorted(list(initial_options))

    def _create_widgets(self):
        """Creates and configures all the UI widgets."""
        # Control Frame
        control_frame = customtkinter.CTkFrame(self.app)
        control_frame.pack(pady=20, padx=60, fill="x")
        customtkinter.CTkLabel(control_frame, text="Search Entity/Asset:").pack(side="left", padx=(10, 0), pady=10)
        self.entity_combobox = customtkinter.CTkComboBox(control_frame, values=self.all_entity_identifiers)
        self.entity_combobox.set(self.PLACEHOLDER_TEXT)
        self.entity_combobox.bind("<FocusIn>", self._set_placeholder)
        self.entity_combobox.bind("<FocusOut>", self._restore_placeholder)
        self.entity_combobox.bind("<KeyRelease>", self._dynamic_combobox_filter)
        self.entity_combobox.pack(side="left", padx=(10, 5), pady=10, fill="x", expand=True)
        customtkinter.CTkButton(control_frame, text="Search Profiles", command=self._search_button_callback).pack(side="left", padx=(10, 10), pady=10)

        # Results Frame
        self.results_label = customtkinter.CTkLabel(self.app, text="Profile Matches", font=customtkinter.CTkFont(weight="bold"))
        self.results_scroll_frame = customtkinter.CTkScrollableFrame(self.app, height=200)

        # Timeline View
        self.timeline_close_button = customtkinter.CTkButton(self.app, text="Back to Matches ⬅", width=150, command=self.hide_all_extra_views)
        self.result_textbox = customtkinter.CTkTextbox(self.app, height=250, font=("Courier New", 12))

        # Image View
        self.image_frame = customtkinter.CTkFrame(self.app)
        self.image_close_button = customtkinter.CTkButton(self.image_frame, text="Back to Matches ⬅", width=150, command=self.hide_all_extra_views)
        self.image_label = customtkinter.CTkLabel(self.image_frame, text="", justify="center", font=customtkinter.CTkFont(size=16))

    def _set_placeholder(self, event):
        if self.entity_combobox.get() == self.PLACEHOLDER_TEXT:
            self.entity_combobox.set("")
            self.entity_combobox.configure(values=self.all_entity_identifiers)

    def _restore_placeholder(self, event):
        if not self.entity_combobox.get().strip():
            self.entity_combobox.set(self.PLACEHOLDER_TEXT)
            self.entity_combobox.configure(values=self.all_entity_identifiers)

    def _dynamic_combobox_filter(self, event=None):
        typed_text = self.entity_combobox.get().strip().lower()
        if typed_text == self.PLACEHOLDER_TEXT.lower() or not typed_text:
            self.entity_combobox.configure(values=self.all_entity_identifiers)
            return
        filtered_options = [item for item in self.all_entity_identifiers if typed_text in item.lower()]
        self.entity_combobox.configure(values=filtered_options if filtered_options else [])
        self.entity_combobox.set(typed_text)

    def hide_all_extra_views(self):
        self.timeline_close_button.pack_forget()
        self.result_textbox.pack_forget()
        self.image_frame.pack_forget()
        self.app.geometry("1000x550")
        self.results_label.pack(pady=(10, 0), padx=60, anchor="w")
        self.results_scroll_frame.pack(pady=10, padx=60, fill="both", expand=True)

    def _show_timeline_view(self):
        self.results_label.pack_forget()
        self.results_scroll_frame.pack_forget()
        self.image_frame.pack_forget()
        self.app.geometry("1000x700")
        self.timeline_close_button.pack(pady=(10, 5), padx=60, anchor="e")
        self.result_textbox.pack(pady=(0, 10), padx=60, fill="both", expand=True)

    def _show_image_view(self, image_path, entity_name):
        self.results_label.pack_forget()
        self.results_scroll_frame.pack_forget()
        self.timeline_close_button.pack_forget()
        self.result_textbox.pack_forget()
        self.app.geometry("1000x700")
        self.image_frame.pack(pady=10, padx=60, fill="both", expand=True)
        self.image_close_button.pack(pady=(10, 5), padx=5, anchor="e")
        self.image_label.configure(image=None, text=f"Loading Face Image for: {entity_name}...")
        self.image_label.pack(fill="both", expand=True, padx=20, pady=20)
        try:
            if not os.path.exists(self.FACE_IMAGE_DIR): raise FileNotFoundError(f"Directory not found: {self.FACE_IMAGE_DIR}")
            img = Image.open(image_path)
            img.thumbnail((600, 600))
            ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            self.image_label.configure(image=ctk_img, text=f"Facial Profile: {entity_name}", compound="top")
            self.image_label.image = ctk_img # pyright: ignore[reportAttributeAccessIssue]
        except FileNotFoundError:
            self.image_label.configure(text=f"Facial Profile for: {entity_name}\n\nERROR: Image not found.\nExpected file: {image_path}", image=None)
        except Exception as e:
            self.image_label.configure(text=f"Facial Profile for: {entity_name}\n\nERROR loading image: {e}", image=None)

    def _search_button_callback(self):
        selected_entity = self.entity_combobox.get().strip()
        if selected_entity == self.PLACEHOLDER_TEXT: selected_entity = ""
        self.hide_all_extra_views()
        for widget in self.results_scroll_frame.winfo_children(): widget.destroy()

        if not selected_entity:
            text = "Please enter a search term (Name, ID, Email, etc.)."
        elif self.profiles_df.empty:
            text = "ERROR: Profile data not loaded."
        else:
            matches = self.data_processor.find_entities(selected_entity)
            if not matches:
                text = (f"No profile matches found for '{selected_entity}'.", "orange")
            else:
                customtkinter.CTkLabel(self.results_scroll_frame, text=f"Found {len(matches)} match(es) for '{selected_entity}':", font=customtkinter.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5), anchor="w")
                for i, match in enumerate(matches):
                    self._create_match_widget(self.results_scroll_frame, match, i)
                return

        label_text, label_color = (text, "white") if isinstance(text, str) else text
        customtkinter.CTkLabel(self.results_scroll_frame, text=label_text, text_color=label_color).pack(padx=10, pady=5, anchor="w")

    def _create_match_widget(self, parent_frame, match, index):
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
            if self.location_predictor.model:
                customtkinter.CTkButton(
                    button_frame, text="Predict 🔮", width=100, fg_color="#581845", hover_color="#C70039",
                    command=lambda id=entity_id: self._predict_location_callback(id)
                ).pack(side="right", padx=5, pady=5)

            if face_id != 'N/A':
                customtkinter.CTkButton(
                    button_frame, text="View Face 📷", width=120, fg_color="darkgreen", hover_color="green",
                    command=lambda id=entity_id: self._view_face_callback(id)
                ).pack(side="right", padx=5, pady=5)

            customtkinter.CTkButton(
                button_frame, text="Check Timeline", width=150,
                command=lambda id=entity_id: self._check_timeline_callback(id)
            ).pack(side="right", padx=5, pady=5)

        customtkinter.CTkFrame(parent_frame, height=1, fg_color="gray").pack(fill="x", padx=10)

    def _get_profile_by_id(self, entity_id):
        if self.profiles_df.empty: return None
        match_row = self.profiles_df[self.profiles_df['entity_id'] == entity_id]
        return match_row.iloc[0].to_dict() if not match_row.empty else None

    def _view_face_callback(self, entity_id):
        entity_profile = self._get_profile_by_id(entity_id)
        if not entity_profile: return
        face_id = entity_profile.get('face_id')
        entity_name = entity_profile.get('name', 'N/A')
        if not face_id: return
        image_path = os.path.join(self.FACE_IMAGE_DIR, f"{face_id}.jpg")
        self._show_image_view(image_path, entity_name)

    def _check_timeline_callback(self, entity_id):
        self._show_timeline_view()
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", f"Fetching timeline for Entity ID: {entity_id}...\n")
        entity_profile = self._get_profile_by_id(entity_id)
        if entity_profile:
            timeline_text = self.data_processor.generate_timeline(entity_profile)
            self.result_textbox.insert("end", timeline_text)
        else:
            self.result_textbox.insert("end", f"Error: Could not find profile details for ID {entity_id}.")

    def _predict_location_callback(self, entity_id):
        self._show_timeline_view()
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", f"Running prediction for Entity ID: {entity_id}...\n\n")

        entity_profile = self._get_profile_by_id(entity_id)
        if not entity_profile:
            self.result_textbox.insert("end", f"Error: Could not find profile details for ID {entity_id}.")
            return

        last_location, justification = self.data_processor.get_last_known_location(entity_profile)
        self.result_textbox.insert("end", f"Justification: {justification}\n\n")

        if last_location:
            prediction_result = self.location_predictor.predict(entity_id, last_location)
            self.result_textbox.insert("end", f"RESULT: {prediction_result}")

from ethos.core.data_processing import DataProcessor
from ethos.ml.location_predictor import LocationPredictor
from ethos.ui.dashboard import DashboardApp
from ethos import config

class App:
    """
    Main application class to coordinate the different modules.
    """
    def __init__(self):
        self.data_processor = DataProcessor(data_directory=config.CLEAN_DATA_DIR)
        self.location_predictor = LocationPredictor(model_dir=config.MODEL_DIR)

    def run(self):
        """
        Initializes and runs the application.
        """
        # Try to load the model, if it fails, train a new one
        if not self.location_predictor.load_model():
            print("No pre-trained model found. Training a new one...")
            self.location_predictor.train(self.data_processor.all_data)

        # --- To switch between UIs, comment/uncomment the following lines ---

        # --- Old CustomTkinter UI ---
        dashboard = DashboardApp(self.data_processor, self.location_predictor)
        dashboard.run()

        # --- New Flet UI ---
        # dashboard = FletDashboard(self.data_processor, self.location_predictor)
        # dashboard.run()

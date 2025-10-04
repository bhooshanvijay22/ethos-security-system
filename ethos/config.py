import os

# --- DIRECTORIES ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This will be the ethos directory
SOURCE_DATA_DIR = os.path.join(ROOT_DIR, '..', 'data')
CLEAN_DATA_DIR = os.path.join(ROOT_DIR, '..', 'clean_data')
MODEL_DIR = os.path.join(ROOT_DIR, 'ml', 'models')

# --- FILENAMES ---
PROFILES_CLEANED_FILENAME = "profiles_cleaned.csv"
LOCATION_PREDICTOR_MODEL_FILENAME = "location_predictor.joblib"
LOCATION_PREDICTOR_ENCODERS_FILENAME = "location_encoders.joblib"

# --- UI CONSTANTS ---
PLACEHOLDER_TEXT = "Select or type name, ID, or email..."
FACE_IMAGE_DIR = os.path.join(SOURCE_DATA_DIR, "face_images")

# --- ML MODEL ---
LOCATION_PREDICTOR_N_ESTIMATORS = 50
LOCATION_PREDICTOR_TEST_SIZE = 0.2
LOCATION_PREDICTOR_RANDOM_STATE = 42

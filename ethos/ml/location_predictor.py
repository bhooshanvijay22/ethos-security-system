import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from ethos import config

class LocationPredictor:
    """
    Manages the training, prediction, and persistence of the location prediction model.
    """
    def __init__(self, model_dir=config.MODEL_DIR):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, config.LOCATION_PREDICTOR_MODEL_FILENAME)
        self.encoders_path = os.path.join(model_dir, config.LOCATION_PREDICTOR_ENCODERS_FILENAME)
        self.model = None
        self.entity_encoder = None
        self.loc_encoder = None
        self._ensure_model_dir_exists()

    def _ensure_model_dir_exists(self):
        """Creates the model directory if it doesn't exist."""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def train(self, clean_data):
        """Trains the location prediction model."""
        required_files = ["campus card_swipes.csv", "wifi_associations_logs.csv", "profiles_cleaned.csv"]
        if not all(f in clean_data for f in required_files):
            print("Missing required data for training predictor.")
            return False

        data = self._prepare_training_data(clean_data)
        if data.empty:
            print("Not enough data to train the predictor.")
            return False

        X, y, self.entity_encoder, self.loc_encoder = self._create_features(data)
        if not X.any():
            print("Not enough sequential data to train.")
            return False

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=config.LOCATION_PREDICTOR_TEST_SIZE, random_state=config.LOCATION_PREDICTOR_RANDOM_STATE)
        if len(X_train) == 0:
            print("Not enough training data after split.")
            return False

        self.model = RandomForestClassifier(n_estimators=config.LOCATION_PREDICTOR_N_ESTIMATORS, random_state=config.LOCATION_PREDICTOR_RANDOM_STATE)
        self.model.fit(X_train, y_train)

        accuracy = self.model.score(X_test, y_test) if len(X_test) > 0 else "N/A"
        print(f"Location predictor trained. Accuracy: {accuracy}")
        self.save_model()
        return True

    def predict(self, entity_id, current_location):
        """Predicts the next location for an entity."""
        if self.model is None or current_location is None:
            return "Predictor not available or current location is unknown."

        try:
            if entity_id not in self.entity_encoder.classes_:
                return "Entity ID not seen during training."
            if current_location not in self.loc_encoder.classes_:
                return "Location not seen during training."

            entity_id_enc = self.entity_encoder.transform([entity_id])[0]
            current_loc_enc = self.loc_encoder.transform([current_location])[0]

            X_pred = np.array([[entity_id_enc, current_loc_enc]])
            y_pred_enc = self.model.predict(X_pred)
            predicted_location = self.loc_encoder.inverse_transform(y_pred_enc)[0]

            return f"Predicted Next Location: **{predicted_location}**"
        except Exception as e:
            return f"Error during prediction: {e}"

    def load_model(self):
        """Loads the model and encoders from disk."""
        if os.path.exists(self.model_path) and os.path.exists(self.encoders_path):
            self.model = joblib.load(self.model_path)
            self.entity_encoder, self.loc_encoder = joblib.load(self.encoders_path)
            print("Location predictor model loaded from disk.")
            return True
        return False

    def save_model(self):
        """Saves the model and encoders to disk."""
        if self.model is not None:
            joblib.dump(self.model, self.model_path)
            joblib.dump((self.entity_encoder, self.loc_encoder), self.encoders_path)
            print(f"Model saved to {self.model_dir}")

    def _prepare_training_data(self, clean_data):
        """Prepares the training data by merging and cleaning datasets."""
        profiles = clean_data["profiles_cleaned.csv"][['entity_id', 'card_id', 'device_hash']].copy()
        swipes = pd.merge(clean_data["campus card_swipes.csv"].copy(), profiles, on='card_id', how='left')
        wifi = pd.merge(clean_data["wifi_associations_logs.csv"].copy(), profiles, on='device_hash', how='left')

        dfs = []
        if not swipes.empty:
            dfs.append(swipes[["entity_id", "location_id", "timestamp"]].dropna())
        if not wifi.empty:
            wifi = wifi.rename(columns={"ap_id": "location_id"})
            dfs.append(wifi[["entity_id", "location_id", "timestamp"]].dropna())

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs).sort_values(by="timestamp").dropna(subset=['entity_id', 'location_id'])

    def _create_features(self, data):
        """Creates features and labels for the model."""
        entity_encoder = LabelEncoder()
        loc_encoder = LabelEncoder()
        data["entity_id_enc"] = entity_encoder.fit_transform(data["entity_id"].astype(str))
        data["location_id_enc"] = loc_encoder.fit_transform(data["location_id"].astype(str))

        X, y = [], []
        for eid in data["entity_id_enc"].unique():
            locs = data[data["entity_id_enc"] == eid].sort_values("timestamp")["location_id_enc"].values
            for i in range(len(locs) - 1):
                X.append([eid, locs[i]])
                y.append(locs[i+1])

        return np.array(X), np.array(y), entity_encoder, loc_encoder

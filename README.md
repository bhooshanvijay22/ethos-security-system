# Ethos Security System

## Introduction

Ethos is a comprehensive security dashboard designed for monitoring personnel movement and activity within a campus environment. It provides a centralized interface to track individuals, view their activity timelines, and predict their next location based on historical data. This project was developed for a hackathon challenge.

## Features

*   **Unified Dashboard**: A user-friendly graphical interface to search for individuals and view their security-related data.
*   **Comprehensive Data Integration**: Consolidates data from various sources, including card swipes, WiFi access logs, CCTV, lab bookings, and library checkouts.
*   **Data Cleaning and Processing**: Automatically cleans and standardizes data from different sources to ensure consistency and accuracy.
*   **Timeline Generation**: Creates a chronological timeline of an individual's activities across the campus.
*   **Facial Recognition**: Displays images of individuals for visual identification.
*   **Location Prediction**: Utilizes a machine learning model to predict an individual's next location based on their movement patterns.

## Project Structure

The project is organized into the following directories:

```
ethos-security-system/
├── .gitignore
├── main.py
├── clean_data/
├── data/
│   └── face_images/
└── ethos/
    ├── __init__.py
    ├── app.py
    ├── config.py
    ├── core/
    │   ├── cleaner.py
    │   └── data_processing.py
    ├── ml/
    │   ├── location_predictor.py
    │   └── models/
    ├── ui/
    │   └── dashboard.py
    └── utils/
```

*   `main.py`: The main entry point to run the application.
*   `data/`: Contains the raw data from various sources.
*   `clean_data/`: Stores the cleaned and processed data.
*   `ethos/`: The main application package.
    *   `app.py`: The main application class that coordinates the different modules.
    *   `config.py`: Configuration file for file paths and model parameters.
    *   `core/`: Core modules for data cleaning and processing.
    *   `ml/`: Machine learning module for location prediction.
    *   `ui/`: User interface module for the dashboard.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ethos-security-system
    ```

2.  **Add the dataset:**
    The dataset for this project should be placed in the `data/` directory. This includes the CSV files with the security data and a folder named `face_images` containing the images for facial recognition.

3.  **Install dependencies:**
    This project requires the following Python libraries:
    *   pandas
    *   scikit-learn
    *   customtkinter
    *   joblib
    *   Pillow

    You can install them using pip:
    ```bash
    pip install pandas scikit-learn customtkinter joblib Pillow
    ```

## Usage

To run the Ethos Security System, execute the `main.py` script from the root of the project directory:

```bash
python main.py
```

This will launch the dashboard application. The first time you run the application, it will automatically train the location prediction model if a pre-trained model is not found.

## Machine Learning Model

The location prediction model is a `RandomForestClassifier` from the `scikit-learn` library. It is trained on the historical location data of individuals to predict their next move.

*   **Training**: The model is trained on a dataset created by combining card swipes, WiFi logs, lab bookings, and library checkouts. The data is processed to create sequences of locations for each individual.
*   **Prediction**: Given an individual's current location, the model predicts their next likely location.
*   **Model Storage**: The trained model and encoders are saved to the `ethos/ml/models/` directory.

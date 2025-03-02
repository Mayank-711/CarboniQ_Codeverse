import os
import joblib
import pandas as pd
from django.conf import settings
from sklearn.preprocessing import OneHotEncoder

# Define the path to the ML models directory
ML_MODELS_DIR = os.path.join(settings.BASE_DIR, "mainapp", "ml", "models")

# Load the trained model and scaler dynamically using ML_MODELS_DIR
model = joblib.load(os.path.join(ML_MODELS_DIR, "CarbonIQ_rf_model.pkl"))
scaler = joblib.load(os.path.join(ML_MODELS_DIR, "CarbonIQ_scaler.pkl"))

# Available transport modes for encoding
transport_modes = ["acbus", "actrain", "bicycle", "bike", "bus", "car",
                   "eacbus", "ebike", "ebus", "ecar", "erickshaw", "escooter",
                   "etrain", "rickshaw", "scooter", "walk"]

# Initialize OneHotEncoder with known transport modes and fit it
encoder = OneHotEncoder(categories=[transport_modes], sparse_output=False)
encoder.fit(pd.DataFrame(transport_modes, columns=["mode_of_transport"]))


def predict_co2_emission(mode_of_transport: str, passengers: int, distance: float, time: float) -> float:
    """+
    Predicts the CO₂ emissions based on mode of transport, passenger count, distance, and time.
    """

    # Prepare input data
    input_data = pd.DataFrame({
        "mode_of_transport": [mode_of_transport],
        "passengers": [passengers],
        "distance": [distance],
        "time": [time]
    })

    # One-hot encode transport mode
    encoded_input = encoder.transform(input_data[['mode_of_transport']])
    encoded_df = pd.DataFrame(encoded_input, columns=encoder.get_feature_names_out())

    # Scale numeric inputs
    scaled_input = scaler.transform(input_data[['passengers', 'distance', 'time']])
    scaled_df = pd.DataFrame(scaled_input, columns=['passengers', 'distance', 'time'])

    # Combine scaled and encoded features, ensuring correct order
    final_input = pd.concat([scaled_df, encoded_df], axis=1)
    final_input = final_input.reindex(columns=model.feature_names_in_, fill_value=0)

    # Predict CO₂ emissions
    predicted_co2 = model.predict(final_input)

    # Apply reduction for non-electric vehicles and for cars
    if not mode_of_transport.startswith("e"):
        predicted_co2 *= 0.75
    if mode_of_transport == "car":
        predicted_co2 *= 0.75

    # Debugging logs
    # print("===== Prediction Debugging =====")
    # print(f"Mode of Transport: {mode_of_transport}")
    # print(f"Passengers: {passengers}")
    # print(f"Distance: {distance} km")
    # print(f"Time Taken: {time} mins")
    # print(f"Predicted CO2 Emission: {predicted_co2[0]:.2f}g")

    return float(predicted_co2[0])

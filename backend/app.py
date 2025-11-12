import os
import joblib
import json
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
import keras

app = Flask(__name__)

MODEL_PATH = 'model\model_Genre_Analyzer.keras'
SCALER_PATH = 'model\scaler.pkl'

ALL_GENRES = ['Pop', 'Hiphop', 'Rock', 'Classic', 'EDM', 'Ballad', 'Jazz']

try:
    model = keras.models.load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    print(f"모델 또는 스케일러 로드 실패: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Genre Prediction API is running."}), 200


@app.route('/predict', methods=['GET','POST'])
def predict():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    required_keys = ['gender', 'age_group', 'ei_score', 'sn_score', 'tf_score', 'jp_score', 'pop', 'hiphop', 'rock', 'classic', 'edm', 'ballad', 'jazz']
    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        input_df = pd.DataFrame([{
            "Gender": data["gender"],
            "Age_Group": data["age_group"],
            "E_I_Score": data["ei_score"],
            "S_N_Score": data["sn_score"],
            "T_F_Score": data["tf_score"],
            "J_P_Score": data["jp_score"],
            "Pop" : data["pop"],
            "Hiphop" : data["hiphop"],
            "Rock" : data["rock"],
            "Classic" : data["classic"],
            "EDM" : data["edm"],
            "Ballad" : data["ballad"],
            "Jazz" : data["jazz"]
        }])

        feature_cols = ['Gender', 'Age_Group', 'E_I_Score', 'S_N_Score', 'T_F_Score', 'J_P_Score', 'Pop', 'Hiphop', 'Rock', 'Classic', 'EDM', 'Ballad', 'Jazz']
        
        X_test = input_df[feature_cols].values
        
        X_test_scaled = scaler.transform(X_test)
        
        predictions_raw = model.predict(X_test_scaled)
        
        predictions_binary = (predictions_raw > 0.5).astype(int)

        result = {}
        for i, genre in enumerate(ALL_GENRES):
            result[genre] = {
                "probability": float(predictions_raw[0][i]),
                "prefers": int(predictions_binary[0][i])
            }
        
        return jsonify({"user_prediction": result}), 200

    except Exception as e:
        return jsonify({"error": str(e), "message": "Prediction failed due to internal processing error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
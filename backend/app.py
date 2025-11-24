import os
import sys
import joblib
import json
from flask import Flask, request, jsonify, redirect, url_for
import keras
import pandas as pd
from werkzeug.utils import secure_filename
from flask_cors import CORS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import find_music as fm

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'

UPLOAD_PATH = os.path.join(app.root_path, UPLOAD_FOLDER)

app.config['uploads'] = UPLOAD_PATH

try:
    os.makedirs(UPLOAD_PATH, exist_ok=True) 
    print(f"Upload folder ready: {UPLOAD_PATH}")
except OSError as e:
    print(f"Error: Failed to create upload folder: {e}")

MODEL_PATH = '/app/model\model_Genre_Analyzer.keras'
SCALER_PATH = '/app/model\scaler.pkl'

ALL_GENRES = ['Pop', 'Hiphop', 'Rock', 'Classic', 'EDM', 'Ballad', 'Jazz']
ACTIVITIES = ["viewing_history.json", "playlist.csv", "music_library_songs.csv", "subscribed.csv", "comment.csv"]

try:
    model = keras.models.load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    print(f"모델 또는 스케일러 로드 실패: {e}")

@app.route('/')
def home():
    return "Music Genre Prediction API is running!"

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Genre Prediction API is running."}), 200


@app.route('/upload_with_json', methods=['POST'])
def predict():
    #JSON 요청 처리
    json_string = request.form.get('metadata')

    if not json_string:
        return jsonify({"error": f"JSON metadata field is missing or empty."}), 400
    
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format."}), 400

    required_keys = ['gender', 'age_group', 'ei_score', 'sn_score', 'tf_score', 'jp_score']
    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing required fields"}), 400
    
    uploaded_files = request.files.getlist('files')

    if len(uploaded_files) != 5 or uploaded_files[0].filename == '':
        return jsonify({"message": f"need exactly 5 files. now {len(uploaded_files)}sent."}), 400
    
    # 파일 저장 및 경로 저장
    saved_paths = [None] * 5

    for file in uploaded_files:
        if file and file.filename:
            original_filename = file.filename
            filename = secure_filename(original_filename)
            
            file_index = -1
            for i, activ in enumerate(ACTIVITIES):
                if activ in original_filename:
                    file_index = i
                    break
            
            if file_index != -1:
                file_path = os.path.join(app.config['uploads'], filename)
                file.save(file_path)
                
                saved_paths[file_index] = file_path
            else:
                return jsonify({"error": f"Undefined file name included: {original_filename}"}), 400

    if None in saved_paths:
        return jsonify({"error": "A fatal error occurred while saving the file, or none of the 5 files contained the correct type"}), 500
    
    try:
        score = fm.find_music(saved_paths[0], saved_paths[1], saved_paths[2], saved_paths[3], saved_paths[4])
        input_df = pd.DataFrame([{
            "Gender": data["gender"],
            "Age_Group": data["age_group"],
            "E_I_Score": data["ei_score"],
            "S_N_Score": data["sn_score"],
            "T_F_Score": data["tf_score"],
            "J_P_Score": data["jp_score"],
            'Pop': score['Pop'],
            'Hiphop': score['Hiphop'],
            'Rock': score['Rock'],
            'Classic': score['Classic'],
            'EDM': score['EDM'],
            'Ballad': score['Ballad'],
            'Jazz': score['Jazz']
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
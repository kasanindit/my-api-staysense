from flask import Flask, json, request, jsonify
import pandas as pd
import numpy as np
import os
import joblib
import io
import firebase_admin
import re
from firebase_admin import credentials, firestore, storage
from datetime import datetime
from wordcloud import WordCloud


firebase_key = os.getenv("FIREBASE_CREDENTIALS")
cred = credentials.Certificate(json.loads(firebase_key))

firebase_admin.initialize_app(cred, {
    'storageBucket': 'staysense-624b4.firebasestorage.app'
})

# cred = credentials.Certificate("staysenseKey.json")

# firebase_admin.initialize_app(cred, {
#     'storageBucket': 'staysense-624b4.firebasestorage.app'
# })

db = firestore.client() 

app = Flask(__name__)

def to_snake_case(name):
    name = re.sub(r"[\s/]+", "_", name)
    return name.lower()


# model_path = os.path.join("model", "model_tabnet_reall.pkl")
model_path = os.path.join("model", "model_xgboost.pkl")
model_bundle = joblib.load(model_path)
model = model_bundle["model"]
encoder = {to_snake_case(k): v for k, v in model_bundle["label_encoders"].items()}
columns = [to_snake_case(col) for col in model_bundle["columns"]]

bucket = storage.bucket()

TRESHOLD =  0.437


# Kolom yang dibutuhkan
required_cols = [
    "age", "number_of_dependents", "city", "tenure_in_months",
    "internet_service", "online_security", "online_backup", "device_protection_plan",
    "premium_tech_support", "streaming_tv", "streaming_movies", "streaming_music",
    "unlimited_data", "contract", "payment_method", "monthly_charge",
    "total_charges", "total_revenue", "satisfaction_score", "churn_score", "cltv"
]

def encode_input(data_dict):
    processed = {}
    for col in columns:
        val = data_dict.get(col)
        if val is None:
            raise ValueError(f"Missing required input: '{col}'")
        
        if col in encoder:
            le = encoder[col]
            if val not in le.classes_:
                raise ValueError(
                    f"Invalid value '{val}' for column '{col}'. Expected one of: {list(le.classes_)}"
                )
            val = le.transform([val])[0]
        else:
            if isinstance(val, str) and val.strip().lower() in ['yes', 'no']:
                val = 1 if val.strip().lower() == 'yes' else 0
            elif isinstance(val, str):
                try:
                    val = float(val)
                except ValueError:
                    raise ValueError(f"Invalid non-numeric input after encoding: {val}")
        
        processed[col] = val

    return np.array([list(processed.values())], dtype=np.float32)


@app.route("/", methods=["GET"])
def index():
    return "API is running!"

@app.route("/valid-values", methods=["GET"])
def valid_values():
    return jsonify({
        col: list(encoder[col].classes_)
        for col in encoder
    })

# Input Manual
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        user_id = data.get("id")
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        data = {k.lower(): v for k, v in data.items()}
        
        input_data = encode_input(data)

        churn_probability = model.predict_proba(input_data)[0][1]

        # output yang keluar
        if churn_probability > TRESHOLD:
            result = {
                "is_churn": True,                
                "churn_rate": f"{round(churn_probability * 100, 2):.2f}%",
                "message": "The model predicts that this customer is likely to CHURN.",
                "solution": "It is recommended to take proactive actions such as offering promotions, personalized support, or loyalty programs to retain the customer."
                }
        else:
            result = {
                "is_churn": False,
                "not_churn_rate": f"{round((1 - churn_probability) * 100, 2):.2f}%",
                "message": "The model predicts that this customer is likely to STAY.",
                "solution": "Continue providing consistent service quality and consider rewarding loyalty to maintain customer satisfaction."        
            }

        now = datetime.now()
        month_str = now.strftime("%Y-%m")

        # output masuk ke firestore
        db.collection("predictions").add({
            "user_id": user_id,
            "input_source":"manual",
            "timestamp": now.isoformat(),
            "month": month_str,
            "is_churn": result["is_churn"],
            "rate": float(churn_probability),
            "customer_data": data 
        })
        
        return jsonify({
            "status": "success",
            "prediction": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Missing input data : {str(e)}",
            "prediction": {
                "is_churn": "unknown",
                "churn_probability": "unknown",
                "message": "Prediction failed due to an internal error."
            }
        }), 500
            
# Upload File
def upload_to_storage(user_id, file, filename, folder="uploaded_files"):
    # user_folder = f"{folder}/{user_id}/"
    blob = bucket.blob(f"{folder}/{user_id}/{filename}")
    blob.upload_from_file(file, content_type=file.content_type)
    blob.make_public()
    return blob.public_url

@app.route("/upload", methods=["POST"])
def upload():
    try:
        user_id = request.form.get("id")

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        if 'file' not in request.files:
            return jsonify({"error": "File is required"}), 400

        file = request.files['file']
        filename = file.filename.lower()

        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(file)
        else:
            return jsonify({"error": "Unsupported file format. Only CSV, XLS, XLSX allowed."}), 400

        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '', regex=True)

        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            return jsonify({"error": f"Missing columns: {missing_cols}"}), 400

        df = df[columns]

        # Encode data
        for col in df.columns:
            if col in encoder:
                le = encoder[col]
                if not df[col].isin(le.classes_).all():
                    unknown_vals = df[~df[col].isin(le.classes_)][col].unique().tolist()
                    return jsonify({
                        "error": f"Invalid values in column '{col}': {unknown_vals}. Expected one of: {list(le.classes_)}"
                    }), 400
                df[col] = le.transform(df[col])

        input_data = df.to_numpy()
        proba = model.predict_proba(input_data)
        churn_flags = proba[:, 1] > TRESHOLD

        total_customers = len(proba)
        churn_count = int(np.sum(churn_flags))

        # Upload file ke Firebase Storage dengan user_id
        file.stream.seek(0)
        file_url = upload_to_storage(file, filename, user_id) 

        # Simpan summary hasil prediksi ke Firestore
        summary = {
            "user_id": user_id, 
            "input_source": "Upload file",
            "total_customers": total_customers,
            "churn_count": churn_count,
            "not_churn_count": total_customers - churn_count,
            "churn_rate": f"{(churn_count / total_customers) * 100:.2f}%",
            "filename": filename,
            "file_url": file_url,
            "timestamp": datetime.now().isoformat(),
            "month": datetime.now().strftime("%Y-%m")
        }
        
        db.collection("predictions").add(summary)

        return jsonify({
            "status": "success",
            "summary": summary
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

from collections import defaultdict
@app.route("/history", methods=["GET"])
def get_summary_history():
    try:
        docs = db.collection("predictions").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        
        # Dictionary untuk menyimpan data per bulan
        history_per_month = defaultdict(list)

        for doc in docs:
            data = doc.to_dict()
            timestamp = data.get("timestamp")
            month = data.get("month", "")  # Jika data sudah ada field month yang berisi bulan dalam format "YYYY-MM"

            # Ambil bulan dari timestamp jika tidak ada field "month"
            if not month and timestamp:
                month = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m")

            if month:
                history_per_month[month].append(data)

        # Convert dictionary to list of dictionaries for output
        grouped_history = [{"month": month, "data": history} for month, history in history_per_month.items()]

        return jsonify({"history_per_month": grouped_history})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Dashboard
@app.route("/dashboard/chart", methods=["GET"])
def get_chart_data():
    try:
        # docs = db.collection("predictions").stream()
        user_id = request.args.get("id")
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        docs = db.collection("predictions").where("user_id", "==", user_id).stream()
        
        total_churn = 0
        total_not_churn = 0
        total_customers = 0
        churn_data_per_month = {}
        total_customers_per_month = {}
        
        for doc in docs:
            data = doc.to_dict()
            is_churn = data.get("is_churn", None)
            month = data.get("month", "")
            customers = data.get("total_customers", 1)
            churn_count = data.get("churn_count", 0)
            
            total_customers += customers
            
            # update customer
            if is_churn is not None:
                if is_churn:
                    total_churn += customers  
                else:
                    total_not_churn += customers 
            if churn_count is not None:
                total_churn += churn_count 
                total_not_churn += (customers - churn_count)  
                
            # update churn per bulan
            if month:
                if month not in churn_data_per_month:
                    churn_data_per_month[month] = 0
                if is_churn is not None:
                    if is_churn:
                        churn_data_per_month[month] += customers  
                if churn_count is not None:
                    churn_data_per_month[month] += churn_count  
                
                total_customers_per_month[month] = total_customers_per_month.get(month, 0) + customers

        # bar chart
        churn_rate_per_month = []
        for month in churn_data_per_month:
            churn_rate = (churn_data_per_month[month] / total_customers_per_month[month]) * 100
            churn_rate_per_month.append({
                "month": month,
                "churn_rate": round(churn_rate, 2)
            })

        # pie chart
        churn_percent = round((total_churn / total_customers) * 100, 2) if total_customers > 0 else 0
        not_churn_percent = 100 - churn_percent

        return jsonify({
            "pie_chart": {
                "churn": churn_percent,  
                "not_churn": not_churn_percent
            },
            "bar_chart": churn_rate_per_month,
            "total_customer": total_customers,
            "total_churn": total_churn, 
            "churn_data_per_month": churn_data_per_month,
            "total_customer_per_month": total_customers_per_month  
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/dashboard/informations", methods = ["GET"])
def get_informations():
    try:
        user_id = request.args.get("id")
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        docs = db.collection("predictions").where("user_id", "==", user_id).stream()
        
        total_churn = 0
        total_not_churn = 0
        total_customers = 0
        predictions_per_month = {}
        
        for doc in docs:
            data = doc.to_dict()
           
            is_churn = data.get("is_churn", None)
            churn_count = data.get("churn_count", None)
            month = data.get("month", "")
            customers = data.get("total_customers", 1)
                        
            total_customers += customers
            
            if not month:
                continue
            
            if is_churn is not None:
                if is_churn:
                    total_churn += customers
                else:
                    total_not_churn += customers
            elif churn_count is not None:
                total_churn += churn_count
                total_not_churn += (customers - churn_count)
                
            if month not in predictions_per_month:
                predictions_per_month[month] = 0
            predictions_per_month[month] += 1
            
        total_predictions_per_month = [
            {
                "month": month,
                "total_predictions": predictions_per_month.get(month, 0)
            }
            for month in sorted(predictions_per_month.keys())
        ]    
    
        return jsonify({
            "information": {
                    "total_customers": total_customers,
                    "total_churn": total_churn,
                    "total_not_churn": total_not_churn,
                    "total_predictions_per_month": total_predictions_per_month,
                }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
# Wordcloud
def upload_to_storage(file, filename, folder="wordcloud_files"):
    blob = bucket.blob(f"{folder}/{filename}")
    blob.upload_from_file(file, content_type=file.content_type)
    blob.make_public()
    return blob.public_url

def upload_wordcloud_image(image_bytes, filename):
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type='image/png')
    blob.make_public()
    return blob.public_url

def append_to_firestore_text(user_id, new_text):
    doc_ref = db.collection("wordcloud").document(f"{user_id}_cumulative_wordcloud")
    doc = doc_ref.get()
    if doc.exists:
        existing_text = doc.to_dict().get("text", "")
        updated_text = existing_text + " " + new_text
    else:
        updated_text = new_text
    doc_ref.set({"text": updated_text})

def read_firestore_text(user_id):
    doc_ref = db.collection("wordcloud").document(f"{user_id}_cumulative_wordcloud")
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("text", "")
    return ""
    
@app.route('/wordcloud', methods=['POST'])
def generate_wordcloud_from_model():
    text_from_file = ""
    form_text = ""
    
    user_id = request.form.get("id") if request.form.get("id") else request.json.get("id", "")
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    # untuk input file
    if 'file' in request.files:
        file = request.files['file']
        filename = file.filename.lower()

        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith(".xls") or filename.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            return jsonify({"error": "Unsupported file format. Only CSV, XLS, XLSX allowed."}), 400

        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '', regex=True)
        text_columns = df.select_dtypes(include=['object'])
        text_from_file = " ".join(text_columns.fillna(' ').astype(str).agg(' '.join, axis=1).tolist())
    
    # untuk input form
    if request.is_json:
        form_text = request.json.get("text", "")
    else:
        form_text = request.form.get("text", "")
    
    # menggabungkan reason dari file dan form
    combined_input = f"{text_from_file} {form_text}".strip()
    if not combined_input:
        return jsonify({"error": "No valid text input from file or form."}), 400
    
    append_to_firestore_text(user_id, combined_input)
    text = read_firestore_text(user_id)
    
    # membuat wordcloud
    wc = WordCloud(width=800, height=400, background_color=None, mode="RGBA").generate(text)
    
    img_byte_arr = io.BytesIO()
    wc.to_image().save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    image_url = upload_wordcloud_image(img_byte_arr, f"wordclouds/{user_id}_wordcloud.png")

    return jsonify({"image_url": image_url})

# Cluster
clustering_path = os.path.join("model", "kmeans7_model_joblib.pkl")
clustering_data = joblib.load(clustering_path)
clustering_model = clustering_data["model"]

cluster_descriptions = {
    0: 'Limited Services & Device Issues',
    1: 'Customer Support Dissatisfaction',
    2: 'Data Offers & Extra Charges',
    3: 'Faster Competitor Speeds',
    4: 'Product/Service Dissatisfaction',
    5: 'Unclear/Unknown Reason',
    6: 'Better Offers from Competitors'
}
    
@app.route("/cluster/chart", methods=["GET"])
def get_clustering_data():
    
    labels = clustering_model.labels_
    counts = {}

    for label in labels:
        counts[label] = counts.get(label, 0) + 1

    output = []
    for cluster_num, desc in cluster_descriptions.items():
        output.append({
            "cluster": cluster_num,
            "description": desc,
            "count": counts.get(cluster_num, 0)
        })

    return jsonify(output)

@app.route("/user/data", methods=["GET"])
def get_user_data():
    try:
        user_id = request.args.get("id")
    
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        user_data_ref = db.collection("predictions").where("user_id", "==", user_id).stream()
        
        user_data = []
        for doc in user_data_ref:
            user_data.append(doc.to_dict())
            
        if not user_data:
            return jsonify({"error": "No data found for this user"}), 404
        
        return jsonify({"user_data": user_data})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
if __name__ == "__main__":
    app.run(debug=True)
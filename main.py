from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import os
import joblib
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime

cred = credentials.Certificate("staysenseKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'staysense-624b4.firebasestorage.app'
})

db = firestore.client() 

app = Flask(__name__)

model_path = os.path.join("model", "tabnet_model.pkl")
model = joblib.load(model_path)


# Kolom yang dibutuhkan
# required_cols = [
#     "Age", "Number_of_Dependents", "City", "Tenure_in_Months",
#     "Internet_Service", "Online_Security", "Online_Backup", "Device_Protection_Plan",
#     "Premium_Tech_Support", "Streaming_TV", "Streaming_Movies", "Streaming_Music",
#     "Unlimited_Data", "Contract", "Payment_Method", "Monthly_Charge",
#     "Total_Charges", "Total_Revenue", "Satisfaction_Score", "Churn_Score", "CLTV"
# ]

required_cols = [
    "age", "number_of_dependents", "city", "tenure_in_months",
    "internet_service", "online_security", "online_backup", "device_protection_plan",
    "premium_tech_support", "streaming_tv", "streaming_movies", "streaming_music",
    "unlimited_data", "contract", "payment_method", "monthly_charge",
    "total_charges", "total_revenue", "satisfaction_score", "churn_score", "cltv"
]


@app.route("/", methods=["GET"])
def index():
    return "API is running!"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        
        input_data = np.array([[ 
            data["age"],
            data["number_of_dependents"],
            data["city"],
            data["tenure_in_months"],
            data["internet_service"],
            data["online_security"],
            data["online_backup"],
            data["device_protection_plan"],
            data["premium_tech_support"],
            data["streaming_tv"],
            data["streaming_movies"],
            data["streaming_music"],
            data["unlimited_data"],
            data["contract"],
            data["payment_method"],
            data["monthly_charge"],
            data["total_charges"],
            data["total_revenue"],
            data["satisfaction_score"],
            data["churn_score"],
            data["cltv"]
        ]])

        churn_probability = model.predict_proba(input_data)[0][1]

        # output yang keluar
        if churn_probability > 0.5:
            result = {
                "is_churn": True,
                "churn_rate": f"{round(churn_probability * 100, 2):.2f}%",
                "message": f"Customer will churn with probability {churn_probability * 100:.2f}%"
            }
        else:
            result = {
                "is_churn": False,
                "not_churn_rate": f"{round((1 - churn_probability) * 100, 2):.2f}%",
                "message": f"Customer will not churn with probability {(1 - churn_probability) * 100:.2f}%"
            }


        now = datetime.now()
        month_str = now.strftime("%Y-%m")

        # output masuk ke firestore
        db.collection("predictions").add({
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
            
    

def upload_to_storage(file, filename, folder="uploaded_files"):
    bucket = storage.bucket()
    blob = bucket.blob(f"{folder}/{filename}")
    blob.upload_from_file(file, content_type=file.content_type)
    blob.make_public()
    return blob.public_url

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "File is required"}), 400

    file = request.files['file']
    filename = file.filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(file)
    elif filename.endswith(".xls") or filename.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        return jsonify({"error": "Unsupported file format. Only CSV, XLS, XLSX allowed."}), 400
    
    # cek nama kolom
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '', regex=True)

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return jsonify({"error": f"Missing columns: {missing_cols}"}), 400

    try:
        
        # Prediksi
        df = df[required_cols]
        input_data = df.to_numpy()
        proba = model.predict_proba(input_data)
        churn_flags = proba[:, 1] > 0.5

        total_customers = len(proba)
        churn_count = int(np.sum(churn_flags))
        
        file.stream.seek(0) 
        file_url = upload_to_storage(file, filename)
        
        # summary adalah output yang akan ditampilkan 
        summary = {
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

        # dan akan terkirim ke firestore
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

    
@app.route("/history", methods=["GET"])
def get_summary_history():
    try:
        docs = db.collection("predictions").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        summaries = [doc.to_dict() for doc in docs]
        return jsonify({"history": summaries})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/chart", methods=["GET"])
def get_chart_data():
    try:
        docs = db.collection("predictions").stream()

        total_churn = 0
        total_not_churn = 0
        per_month = {}

        for doc in docs:
            data = doc.to_dict()
            is_churn = data.get("is_churn", False)
            month = data.get("month", "")

            if not month:
                continue 
            if is_churn:
                total_churn += 1
            else:
                total_not_churn += 1

            if month not in per_month:
                per_month[month] = {"churn": 0, "total": 0}
            per_month[month]["total"] += 1 
            if is_churn:
                per_month[month]["churn"] += 1 

        churn_rate_per_month = [
            {
                "month": m,
                "churn_rate": round((d["churn"] / d["total"]) * 100, 2) if d["total"] > 0 else 0
            }
            for m, d in sorted(per_month.items())
        ]

        return jsonify({
            "pie_chart": {
                "churn": total_churn,
                "not_churn": total_not_churn
            },
            "bar_chart": churn_rate_per_month
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)
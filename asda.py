# import joblib
# import os

# model_path = os.path.join("model", "tabnet_churn_model2.pkl")
# model = joblib.load(model_path)

# print(dir(model))

import joblib

# Load file .pkl
model_path = "model/model_TabNet3.pkl"
# model_path = "model/tabnet_churn_model2.pkl"
model_bundle = joblib.load(model_path)

# Tampilkan type dan keys isi file
print("Tipe objek:", type(model_bundle))

if isinstance(model_bundle, dict):
    print("Keys:", list(model_bundle.keys()))

    if "model" in model_bundle:
        print("Model type:", type(model_bundle["model"]))
    
    if "target_encoder" in model_bundle:
        print("Encoder type:", type(model_bundle["target_encoder"]))
        
    if "feature_encoders" in model_bundle:
        print("Feature Encoder type:", type(model_bundle["feature_encoders"]))

    if "columns" in model_bundle:
        print("Columns:", model_bundle["columns"])
else:
    print("Isi bukan dictionary, tapi:", type(model_bundle))

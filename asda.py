# import joblib
# import os

# model_path = os.path.join("model", "tabnet_churn_model2.pkl")
# model = joblib.load(model_path)

# print(dir(model))

# import joblib
# import os

# Load file .pkl
# model_path = "model/model_tabnet_reall.pkl"
# # model_path = "model/tabnet_churn_model2.pkl"
# model_bundle = joblib.load(model_path)

# clustering_path = os.path.join("model", "kmeans7_model_joblib.pkl")
# clustering_model = joblib.load(clustering_path)

# clustering_data = joblib.load(clustering_path)
# print(type(clustering_data))  # kemungkinan besar: <class 'dict'>
# print(clustering_data.keys())


# # Tampilkan type dan keys isi file
# print("Tipe objek:", type(model_bundle))

# if isinstance(model_bundle, dict):
#     print("Keys:", list(model_bundle.keys()))

#     if "model" in model_bundle:
#         print("Model type:", type(model_bundle["model"]))
    
#     if "target_encoder" in model_bundle:
#         print("Encoder type:", type(model_bundle["target_encoder"]))
        
#     if "label_encoders" in model_bundle:
#         print("Feature Encoder type:", type(model_bundle["label_encoders"]))
        
#     if "feature_encoders" in model_bundle:
#         print("Feature Encoder type:", type(model_bundle["feature_encoders"]))

#     if "columns" in model_bundle:
#         print("Columns:", model_bundle["columns"])
        
#     if "City" in model_bundle["columns"]:
#         city_encoder = model_bundle["label_encoders"]["Contract"]
#         city_list = list(city_encoder.classes_)
#         print("Daftar City yang dikenal oleh model:")
#         for city in city_list:
#             print(city)
# else:
#     print("Isi bukan dictionary, tapi:", type(model_bundle))

import pickle  # atau joblib jika kamu pakai joblib
from flask import Flask
import os
import joblib

# # model_path = os.path.join("model", "model_tabnet_reall.pkl")
# model_path = os.path.join("model", "model_tabnet_fix.pkl")
# model_bundle = joblib.load(model_path)

# # Cetak tipe model
# print("Model type:", type(model_bundle))

# # Tampilkan isi / struktur model (jika ada)
# try:
#     print("Model details:")
#     print(model_bundle)
# except Exception as e:
#     print("Could not print model details:", str(e))
    
# # print("Tipe model:", type(model_bundle["model"]))
# # if hasattr(model_bundle["model"], "predict_proba"):
# #     print("Model mendukung predict_proba()")
# # else:
# #     print("Model TIDAK mendukung predict_proba()")

# import joblib

# Memuat model KMeans yang sudah dilatih
clustering_model = joblib.load("model/kmeans7_model_joblib.pkl")
# print(clustering_model.keys())

kmeans_model = clustering_model['model']
vectorizer = clustering_model['vectorizer']

# Memeriksa cluster centers (pusat cluster)
print("Cluster Centers (pusat cluster):")
print(kmeans_model.cluster_centers_)

# Memeriksa label (hasil cluster untuk data yang dilatih)
print("Labels (label untuk data):")
print(kmeans_model.labels_)

# Memeriksa jumlah fitur yang digunakan oleh vectorizer
print("Fitur yang digunakan oleh vectorizer:")
print(vectorizer.get_feature_names_out())
# **StaySense API Documentation**

## **URL**
* StaySense API Base URL
    ```
    https://my-api-staysense-production.up.railway.app
    ```

---

## **Root Endpoint**
- **Endpoint:** `/`
- **Method:** `GET`
- **Description:** Endpoint dasar untuk memastikan API berjalan.
- **Response:**
    ```json
    "API is running!"
    ```

---

## **Predict**
- **Endpoint:** `/predict`
- **Method:** `POST`
- **Description:** Memprediksi kemungkinan customer churn berdasarkan data input.
- **Request Header:**
    ```
    Content-Type: application/json
    ```
- **Request Body (JSON):**
    ```json
    {
        "age": "int",
        "number_of_dependents": "int",
        "city": "string",
        "tenure_in_months": "int",
        "internet_service": "string",
        "online_security": "string",
        "online_backup": "string",
        "device_protection_plan": "string",
        "premium_tech_support": "string",
        "streaming_tv": "string",
        "streaming_movies": "string",
        "streaming_music": "string",
        "unlimited_data": "string",
        "contract": "string",
        "payment_method": "string",
        "monthly_charge": "float",
        "total_charges": "float",
        "total_revenue": "float",
        "satisfaction_score": "int",
        "churn_score": "int",
        "cltv": "float"
    }
    ```
- **Response:**
    ```json
    {
        "prediction": {
            "is_churn": "boolean",
            "churn_probability": "float%",
            "message": "string"
        }
    }
    ```

---

## **Upload**
- **Endpoint:** `/upload`
- **Method:** `POST`
- **Description:** Mengupload file (CSV, XLS, atau XLSX) untuk prediksi churn secara batch.
- **Request Header:**
    ```
    Content-Type: multipart/form-data
    ```
- **Request Body:**
    - Form field `file` (berisi file `.csv`, `.xls`, atau `.xlsx`)

- **Response:**
    ```json
    {
        "summary": {
            "total_customers": "int",
            "churn_count": "int",
            "not_churn_count": "int",
            "churn_rate": "float%",
            "filename": "string",
            "file_url": "string (URL)",
            "timestamp": "string (ISO8601)",
            "month": "string (YYYY-MM)"
        }
    }
    ```

---

## **History**
- **Endpoint:** `/history`
- **Method:** `GET`
- **Description:** Mengambil riwayat prediksi churn (baik individual maupun batch).
- **Response:**
    ```json
    {
        "history": [
            {
                "timestamp": "string (ISO8601)",
                "month": "string (YYYY-MM)",
                "is_churn": boolean, (hanya untuk prediksi individu)
                "churn_probability": float, (hanya untuk prediksi individu)
                "customer_data": { ... }, (hanya untuk prediksi individu)
                "total_customers": int, (hanya untuk prediksi batch)
                "churn_count": int, (hanya untuk prediksi batch)
                "not_churn_count": int, (hanya untuk prediksi batch)
                "churn_rate": "float%", (hanya untuk prediksi batch)
                "filename": "string", (hanya untuk prediksi batch)
                "file_url": "string (URL)" (hanya untuk prediksi batch)
            }
        ]
    }
    ```

---

## **Chart**
- **Endpoint:** `/dashboar/chart`
- **Method:** `GET`
- **Description:** Mengambil data untuk kebutuhan visualisasi pie chart dan bar chart churn.
- **Response:**
    ```json
    {
        "pie_chart": {
            "churn": int,
            "not_churn": int
        },
        "bar_chart": [
            {
                "month": "string (YYYY-MM)",
                "churn_rate": float
            }
        ]
    }
    ```

    ## **Wordcloud**
- **Endpoint:** `/wordcloud`
- **Method:** `POST`
- **Description:** Mengirim data untuk kebutuhan visualisasi Wordcloud.
- - **Request Header:**
    ```
    Content-Type: application/json
    ```
- **Request:**
    ```json
    {
      "text": "string"
    }
    ```
- **Response:**
    ```json
    {
      "image_url": "string"
    }
    ```

  ## **Clustering**
- **Endpoint:** `/cluster/chart`
- **Method:** `GET`
- **Description:** Mendapat data untuk kebutuhan visualisasi Vertical Bar.
- **Response:**
    ```json
    [
      {
        "cluster": int,
        "description": "string",
        "count": int
      },
      {
        "cluster": int,
        "description": "string",
        "count": int
      }
    ]
    ```

---

## **Notes**
- Semua waktu (`timestamp`) menggunakan format ISO 8601 (`YYYY-MM-DDTHH:MM:SS`).
- `month` menggunakan format `YYYY-MM`.
- Untuk prediksi individual (`/predict`), field `is_churn` dan `churn_probability` dikembalikan.
- Untuk prediksi batch upload (`/upload`), yang dikembalikan adalah ringkasan (`summary`) dari file yang diupload.

---

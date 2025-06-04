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
    - **Status code:** 
        - `200 OK` on success
        - `400 Bad Request` if `id` is missing
        - `500 Internal Server Error` on failure
    - **Body**
        - Success:
        ```json
        {
            "status": "success",
            "prediction": {
                "is_churn": "boolean",
                "churn_rate": "string",
                "message": "string",
                "solution": "string"
            }
        }
        ```
        - Error (missing `id`):
        ```json
        {
            "status": "error",
            "message": "user_id is required",
            "prediction": {
                "is_churn": "unknown",
                "churn_probability": "unknown",
                "message": "Prediction failed due to an internal error."
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
    - `id`: User id (required) 
    - `file` : Form field file (berisi file `.csv`, `.xls`, atau `.xlsx`)

- **Response:**
    - **Status code:** 
        - `200 OK` on success
        - `400 Bad Request` if `id` is missing
        - `500 Internal Server Error` on failure
    ```json
    {
        "status": "success",
        "summary": {
            "user_id": "string",
            "churn_rate": "string",
            "total_customers": "int",
            "churn_count": "int",
            "not_churn_count": "int",
            "file_url": "https://storage.googleapis.com/..."
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
                "is_churn": "boolean", 
                "churn_probability": "float", 
                "customer_data": { ... }, 
                "total_customers": "int", 
                "churn_count": "int", 
                "not_churn_count": "int", 
                "churn_rate": "float%", 
                "filename": "string", 
                "file_url": "string (URL)" 
            }
        ]
    }
    ```

---

## **Chart**
- **Endpoint:** `/dashboard/chart`
- **Method:** `GET`
- **Description:** Mengambil data untuk kebutuhan visualisasi pie chart dan bar chart churn.
- **Request Parameters:**
    - `id` (required): The ID of the user.
- **Response:**
    ```json
    {
        "pie_chart": {
            "churn": "int",
            "not_churn": "int"
        },
        "bar_chart": [
            {
                "month": "string (YYYY-MM)",
                "churn_rate": "float"
            }
        ],
        "total_customer": "int"
    }
    ```

## **Informations**
- **Endpoint:** `/dashboard/informations`
- **Method:** `GET`
- **Description:** Mengambil data untuk informations dashboard.
- **Request Parameters:**
    - `id` (required): The ID of the user.
- **Response:**
    ```json
    {
        "information": {
            "total_customers": 100,
            "total_churn": 45,
            "total_not_churn": 55,
            "total_predictions_per_month": [
            {
                "month": "YYYY-MM",
                "total_predictions": "int"
            },
            {
                "month": "YYYY-MM",
                "total_predictions": "int"
            },

            ]
        }
    }
    ```
## **Generate Word Cloud**
- **Endpoint:** `/wordcloud`
- **Method:** `POST`
- **Description:** Generates Word Cloud berdasarkan user input file.
- **Request Header:**
    ```
    Content-Type: multipart/form-data or application/json
    ```
- **Request Body (JSON or Form Data):**
    - **Text** (optional): If provided in the form, it will be used along with the file data.
    - **File** (optional): CSV or XLS file for text extraction.
- **Response:**
    - **Status code:**
        - `200 OK` on success
        - `400 Bad Request` if input text or file is missing
    - **Body:**
        ```json
        {
            "image_url": "https://storage.googleapis.com/.../wordcloud.png"
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
        "cluster": "int",
        "description": "string",
        "count": "int"
      },
      {
        "cluster": "int",
        "description": "string",
        "count": "int"
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

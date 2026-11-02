# 🌾 CaneCare AI - Sugarcane Leaf Disease Prediction Backend

CaneCare AI is a fast, lightweight, and production-ready Python backend designed to help sugarcane farmers and agronomists diagnose leaf diseases from photos and receive immediate treatment guidance in English, Marathi, and Hindi.

---

## 📁 Project Structure & File Guide

Here is what each folder and file does in simple words:

```text
canecare-backend/
├── app/
│   ├── main.py              # The main entry point: creates the FastAPI app, sets up CORS, routes, static /media, and creates database tables on startup.
│   ├── config.py            # Reads configuration (secret keys, token expiry, folder paths) from the .env file.
│   ├── database.py          # Connects to the SQLite database (no separate database server needed) and provides sessions.
│   ├── models.py            # Defines the database tables (Users, Scans, Predictions, Feedback) using SQLAlchemy.
│   ├── schemas.py           # Defines the rules and shapes for request bodies and response outputs using Pydantic.
│   ├── security.py          # Handles password hashing using direct 'bcrypt' and JWT access token creation/validation with 'PyJWT'.
│   ├── routers/
│   │   ├── auth.py          # Handles /signup, /login, and /me user authentication endpoints.
│   │   ├── users.py         # Handles profile updates (PATCH /me for name, phone, language).
│   │   ├── predict.py       # Validates leaf photos, runs ML inference, saves scans, and returns diagnosis & guidance.
│   │   ├── diseases.py      # Public library providing disease details in English, Marathi, and Hindi.
│   │   ├── history.py       # Allows users to view their scan history, view single scan details, and delete scans.
│   │   └── feedback.py      # Collects farmer feedback on whether the diagnosis was accurate.
│   └── services/
│       ├── ml_service.py    # Isolated ML engine: uses a realistic MOCK predictor today, and automatically switches to TensorFlow when a model file is placed in models/.
│       └── disease_data.json # Multilingual advisory content (symptoms, causes, cultural treatment, prevention).
├── models/                  # Place your trained .h5, .keras, or .tflite model file here later.
├── uploads/                 # Uploaded sugarcane leaf images are safely saved here.
├── tests/
│   └── test_api.py          # Automated tests verifying signup, login, predictions, image validation, and history.
├── .env.example             # Example configuration template.
├── .env                     # Your active configuration with a secure secret key.
├── .gitignore               # Keeps temporary files, virtual environments, and database files out of git.
├── requirements.txt         # List of required Python packages.
└── README.md                # This comprehensive user guide.
```

---

## 🚀 How to Run the Backend

Follow these step-by-step instructions. You only need Python 3.11 or higher installed on your computer.

### Step 1: Open Terminal in the Project Directory
Navigate to the `canecare-backend` directory:
```bash
cd canecare-backend
```

### Step 2: Create a Virtual Environment
A virtual environment keeps the project libraries separate from the rest of your computer.

- **On Windows:**
  ```powershell
  python -m venv venv
  ```
- **On Mac / Linux:**
  ```bash
  python3 -m venv venv
  ```

### Step 3: Activate the Virtual Environment
- **On Windows (Command Prompt or PowerShell):**
  ```powershell
  .\venv\Scripts\activate
  ```
  *(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

- **On Mac / Linux:**
  ```bash
  source venv/bin/activate
  ```

### Step 4: Install Required Packages
```bash
pip install -r requirements.txt
```

### Step 5: Start the API Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
You will see output indicating the server is running at:
`http://127.0.0.1:8000`

---

## 📖 Interactive API Documentation (Swagger UI)

Open your web browser and go to:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

This is an interactive dashboard where you can see all available endpoints and test them directly.

### Step-by-Step Testing Walkthrough in Swagger Docs:

1. **Sign Up a New Farmer Account**:
   - Scroll to **`POST /api/v1/auth/signup`**.
   - Click **Try it out**.
   - Enter your name, email, and password (at least 8 characters, containing both letters and numbers, e.g. `Kisan@123`).
   - Click **Execute**. You will receive an HTTP 201 response with your created user profile.

2. **Log In to Get Your Access Token**:
   - Scroll to **`POST /api/v1/auth/login`**.
   - Click **Try it out**.
   - Enter your email and password.
   - Click **Execute**. The response contains an `access_token` string. Copy this token (without quotes).

3. **Authorize in Swagger**:
   - Scroll to the top of the `/docs` page and click the green **Authorize 🔓** button.
   - Paste your copied token into the **Value** box.
   - Click **Authorize**, then click **Close**. All protected endpoints are now unlocked!

4. **Upload a Leaf Photo for Diagnosis**:
   - Scroll to **`POST /api/v1/predict`**.
   - Click **Try it out**.
   - In the `file` field, choose any sugarcane leaf image (JPG or PNG) from your computer.
   - In the `language` field, select `mr` (Marathi), `hi` (Hindi), or `en` (English).
   - Click **Execute**. You will receive the predicted disease, confidence score, severity, and agronomic treatment guidance.

5. **View Your Scan History**:
   - Scroll to **`GET /api/v1/history`**.
   - Click **Try it out** -> **Execute**.
   - You will see your recent scans, complete with image links and diagnoses.

---

## 🧪 How to Run Automated Tests

To verify that all endpoints, authentication, and image validation logic work properly:

```bash
pytest
```
Or for detailed output:
```bash
pytest -v
```

All tests will run against an isolated in-memory test database and should pass cleanly.

---

## 🔌 Connecting Your Real Trained ML Model

Today, the backend runs in **MOCK Mode**, meaning it returns realistic simulated disease predictions so you can develop and test immediately without installing heavy deep learning libraries.

When your real model is trained:
1. Export your model file from TensorFlow/Keras as **`sugarcane_model.h5`** or **`model.tflite`**.
2. Copy the file into the **`models/`** folder:
   ```text
   canecare-backend/models/sugarcane_model.h5
   ```
3. Install TensorFlow into your virtual environment:
   ```bash
   pip install tensorflow
   ```
4. Restart the server! The backend will automatically detect the file, load the weights, and switch from `MOCK` to `REAL` mode. The rest of your app, database, and APIs remain unchanged.

---

## ❓ Common Errors and Quick Fixes

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **`Script execution is disabled` (PowerShell)** | Windows security policy prevents running scripts by default. | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then re-run `.\venv\Scripts\activate`. |
| **`401 Unauthorized` on `/predict` or `/history`** | Missing or expired token. | Log in again at `/api/v1/auth/login`, copy the new token, and paste it into the **Authorize** box in Swagger. |
| **`400 Bad Request: Invalid file extension`** | Uploaded file is not JPG, JPEG, or PNG. | Ensure the image has a `.jpg`, `.jpeg`, or `.png` extension. |
| **`400 Bad Request: Uploaded file is not a valid image`** | The file is corrupted or not a real image stream. | Use a standard photo taken from a mobile phone or camera. |
| **`Port 8000 is already in use`** | Another application is running on port 8000. | Start uvicorn on an alternate port: `uvicorn app.main:app --reload --port 8001`. |
| **`Using MOCK model` warning in console** | Expected behavior when no `.h5` model file is in `models/`. | This is normal! The system uses mock predictions until you place your trained model in `models/`. |


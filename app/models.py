"""import requests
import joblib
import io

# -------------------------
# 1️⃣ Define URLs for all 4 models on Hugging Face
# -------------------------

HATE_MODEL_URL = "https://huggingface.co/bhuloderupesh/hate/resolve/main/hate_speech_model2.pkl"
REQUEST_MODEL_URL = "https://huggingface.co/bhuloderupesh/request/resolve/main/request_0_1_newest_model.pkl"
QUESTION_MODEL_URL = "https://huggingface.co/bhuloderupesh/question/resolve/main/question_0_1_newest_model.pkl"
FEEDBACK_MODEL_URL = "https://huggingface.co/bhuloderupesh/feedback/resolve/main/feedback_0_1_newest_model.pkl"

# -------------------------
# 2️⃣ Load each model directly into memory
# -------------------------

print(f"Fetching hate_model from {HATE_MODEL_URL} ...")
hate_model = joblib.load(io.BytesIO(requests.get(HATE_MODEL_URL).content))
print("Loaded hate_model from HF.")

print(f"Fetching request_model from {REQUEST_MODEL_URL} ...")
request_model = joblib.load(io.BytesIO(requests.get(REQUEST_MODEL_URL).content))
print("Loaded request_model from HF.")

print(f"Fetching question_model from {QUESTION_MODEL_URL} ...")
question_model = joblib.load(io.BytesIO(requests.get(QUESTION_MODEL_URL).content))
print("Loaded question_model from HF.")

print(f"Fetching feedback_model from {FEEDBACK_MODEL_URL} ...")
feedback_model = joblib.load(io.BytesIO(requests.get(FEEDBACK_MODEL_URL).content))
print("Loaded feedback_model from HF.")

"""
# Load your trained models here, same as your notebook:
import joblib # type: ignore

hate_model = joblib.load("models/hate_speech_model2.pkl")
request_model = joblib.load("models/request_0_1_newest_model.pkl")
question_model = joblib.load("models/question_0_1_newest_model.pkl")
feedback_model = joblib.load("models/feedback_0_1_newest_model.pkl")
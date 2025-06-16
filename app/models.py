# Load your trained models here, same as your notebook:
import joblib # type: ignore

hate_model = joblib.load("models/hate_speech_model2.pkl")
request_model = joblib.load("models/request_0_1_newest_model.pkl")
question_model = joblib.load("models/question_0_1_newest_model.pkl")
feedback_model = joblib.load("models/feedback_0_1_newest_model.pkl")


# TubeLens

TubeLens is a web application that helps you **analyze YouTube comments with ease**. It classifies comments into categories such as **Hate Speech, Requests, Questions, and Feedback**, giving content creators and analysts clear insights into audience engagement.

---
![Screenshot (221)](https://github.com/user-attachments/assets/ca1c789a-9cb0-4908-a714-76d694d42555)

## 🎯 Features

✅ **Fetch and display comments** from YouTube videos  
✅ **Classify comments** into:
- Hate Speech
- Requests
- Questions
- Feedback  

✅ **View trends** across multiple videos using multi-line charts  
✅ **Analyze individual videos** with visualizations and top categorized comments  
✅ **Get the most liked comments** based on sentiment type  
✅ **Track comment activity trends** over 7 or 30 days  

---

## 🛠️ Technologies Used

- **React.js** – Frontend UI development  
- **Node.js / Express** – Backend routing for videos and comments  
- **FastAPI** – Comment classification and data analysis (Python)  
- **YouTube Data API** – Fetching video, channel, and comment data  
- **Machine Learning Models** – NLP for comment categorization  

---


## ⚙️ Installation & Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/tubelens-backend.git
   cd tubelens-backend


2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
  

##  🚀 Running the API Server

Launch the FastAPI server with Uvicorn:

uvicorn app.main:app --reload

http://127.0.0.1:8000/docs



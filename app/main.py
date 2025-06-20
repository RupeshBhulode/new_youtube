# app/main.py

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ChannelInfoSchema, MultiVideoTrendResponse, VideoTrend
from app.youtube_api import youtube, get_channel_info_data
from app.utils import analyze_video_comments, summarize_comments
from app.models import hate_model, request_model, question_model, feedback_model
from sklearn.cluster import KMeans
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

app = FastAPI(
    title="YouTube Channel Info API",
    description="Fetch channel details and videos with free/premium option",
    version="1.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/channel_info", response_model=ChannelInfoSchema)
async def channel_info(
    channel_name: str = Query(...),
    is_premium: bool = Query(False)
):
    """
    Get channel info + videos. Premium = 10 videos, Free = 3 videos.
    """
    result = get_channel_info_data(channel_name, is_premium)
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found")
    return result

@app.get("/multi_video_trend", response_model=MultiVideoTrendResponse)
async def multi_video_trend(
    channel_name: str = Query(...),
    is_premium: bool = Query(False)
):
    """
    Get trend data (hate/request/question/feedback counts) for multiple videos.
    Free = top 3, Premium = top 10.
    """
    videos = get_channel_info_data(channel_name, is_premium)
    if not videos:
        raise HTTPException(status_code=404, detail="Channel not found")

    trend_data = []
    for vid in videos["latest_videos"]:   # ✅ FIXED: iterate the list, not the dict
        counts = analyze_video_comments(vid["video_id"])
        trend_data.append(VideoTrend(
            video_id=vid["video_id"],
            title=vid["title"],
            hate_count=counts["hate_count"],
            request_count=counts["request_count"],
            question_count=counts["question_count"],
            feedback_count=counts["feedback_count"]
        ))

    return {"trend_data": trend_data}



@app.get("/video_analysis")
async def video_analysis(
    video_id: str = Query(...),
    is_premium: bool = Query(False)
):
    """
    Analyze single video's comments with clustering summarizer.
    Free: 200 comments
    Premium: 1000 comments
    """

    # === 1) Get video info ===
    video_response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    if not video_response["items"]:
        raise HTTPException(status_code=404, detail="Video not found")

    snippet = video_response["items"][0]["snippet"]
    title = snippet["title"]
    thumbnail_url = snippet["thumbnails"].get("high", {}).get("url") or \
                    snippet["thumbnails"].get("default", {}).get("url")

    # === 2) Fetch comments ===
    comments = []
    next_page_token = None
    max_comments = 1000 if is_premium else 200

    while len(comments) < max_comments:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)
            if len(comments) >= max_comments:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    # === 3) Classify comments ===
    pie_chart = {
        "hate_speech": 0,
        "questions": 0,
        "requests": 0,
        "feedback": 0,
        "neutral": 0
    }

    questions, requests, feedbacks = [], [], []

    for c in comments:
        hate = hate_model.predict([c])[0]
        question = question_model.predict([c])[0]
        request = request_model.predict([c])[0]
        feedback = feedback_model.predict([c])[0]

        if hate:
            pie_chart["hate_speech"] += 1
        elif question:
            pie_chart["questions"] += 1
            questions.append(c)
        elif request:
            pie_chart["requests"] += 1
            requests.append(c)
        elif feedback:
            pie_chart["feedback"] += 1
            feedbacks.append(c)
        else:
            pie_chart["neutral"] += 1

    # === 4) Summarize each category using your clustering method ===
    summaries = {
        "questions": summarize_comments(questions, max_points=10),
        "requests": summarize_comments(requests,  max_points=10),
        "feedback": summarize_comments(feedbacks,  max_points=10)
    }

    return {
        "video_id": video_id,
        "title": title,
        "thumbnail_url": thumbnail_url,
        "pie_chart_data": pie_chart,
        "summaries": summaries
    }


@app.get("/most_liked")
async def most_liked_comments(video_id: str = Query(...)):
    """
    Get the most liked comment for each category (question/request/feedback)
    """
    # === 1) Fetch all comments ===
    comments = []
    next_page_token = None

    while len(comments) < 1000:  # reasonable limit
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response["items"]:
            comment_snippet = item["snippet"]["topLevelComment"]["snippet"]
            comment_text = comment_snippet["textDisplay"]
            like_count = comment_snippet["likeCount"]

            comments.append((comment_text, like_count))

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    if not comments:
        return {
            "top_comments": {
                "most_liked_question": {"text": None, "like_count": 0},
                "most_liked_request": {"text": None, "like_count": 0},
                "most_liked_feedback": {"text": None, "like_count": 0},
            }
        }

    # === 2) Classify and find most liked for each category ===
    most_liked = {
        "question": {"text": "", "like_count": -1},
        "request": {"text": "", "like_count": -1},
        "feedback": {"text": "", "like_count": -1},
    }

    for text, like_count in comments:
        if question_model.predict([text])[0] == 1:
            if like_count > most_liked["question"]["like_count"]:
                most_liked["question"] = {"text": text, "like_count": like_count}
        elif request_model.predict([text])[0] == 1:
            if like_count > most_liked["request"]["like_count"]:
                most_liked["request"] = {"text": text, "like_count": like_count}
        elif feedback_model.predict([text])[0] == 1:
            if like_count > most_liked["feedback"]["like_count"]:
                most_liked["feedback"] = {"text": text, "like_count": like_count}

    # === 3) Prepare response ===
    return {
        "top_comments": {
            "most_liked_question": most_liked["question"],
            "most_liked_request": most_liked["request"],
            "most_liked_feedback": most_liked["feedback"],
        }
    }


@app.get("/comment_trend")
async def comment_trend(
    video_id: str = Query(...),
    is_premium: bool = Query(False)
):
    """
    Returns daily comment count trend for a video.
    Free: Last 7 days
    Premium: Last 28 days
    """

    # 1) How many days to look back
    days = 28 if is_premium else 7
    today = datetime.utcnow().date()
    date_counts = defaultdict(int)

    # 2) Fetch comments (reuse your logic)
    comments = []
    next_page_token = None
    max_comments = 1000  # enough for trending

    while len(comments) < max_comments:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response["items"]:
            comment_snippet = item["snippet"]["topLevelComment"]["snippet"]
            published_at = comment_snippet["publishedAt"]  # ISO 8601
            published_date = datetime.fromisoformat(
                published_at.replace('Z', '+00:00')
            ).date()

            # Consider only comments within the time window
            if today - timedelta(days=days) <= published_date <= today:
                date_counts[str(published_date)] += 1

            comments.append(comment_snippet["textDisplay"])
            if len(comments) >= max_comments:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    # 3) Create ordered list for each day (even if 0 comments)
    trend = []
    for i in range(days):
        day = today - timedelta(days=i)
        trend.append({
            "date": str(day),
            "comment_count": date_counts.get(str(day), 0)
        })

    # 4) Return with newest date last
    return {
        "video_id": video_id,
        "days": list(reversed(trend))
    }
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
from fastapi import Request
from app.rate_limiter import check_rate_limit
from app.schemas import ChannelInfoSchema, MultiVideoTrendResponse, VideoTrend
from app.youtube_api import youtube, get_channel_info_data
from app.utils import analyze_video_comments, rank_comments, summarize_comments
from app.filters import filter_feedbacks, filter_questions, filter_requests
from app.models import hate_model, request_model, question_model, feedback_model
from app.cache import get_cache, set_cache

from googleapiclient.errors import HttpError


app = FastAPI(
    title="YouTube Channel Info API",
    description="Fetch channel details and videos with free/premium option",
    version="1.2"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# 1) Channel Info
# -------------------------------
@app.get("/channel_info", response_model=ChannelInfoSchema)
async def channel_info(
    request: Request,
    channel_name: str = Query(...),
    is_premium: bool = Query(False)
):
    cache_key = f"channel_info:{channel_name}:{is_premium}"
    cached = get_cache(cache_key)
    if cached:
        return cached  # Serve from cache, no rate limit consumed

    # Only check rate limit on cache miss
    client_ip = request.client.host
    limit = 50 if is_premium else 5
    check_rate_limit(client_ip, limit)

    result = get_channel_info_data(channel_name, is_premium)
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found")

    set_cache(cache_key, result, 1800)
    return result



# -------------------------------
# 2) Multi Video Trend
# -------------------------------
@app.get("/multi_video_trend", response_model=MultiVideoTrendResponse)
async def multi_video_trend(
    request: Request,
    channel_name: str = Query(...),
    is_premium: bool = Query(False)
): 
    cache_key = f"multi_video_trend:{channel_name}:{is_premium}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    client_ip = request.client.host
    limit = 50 if is_premium else 5
    check_rate_limit(client_ip, limit)

    videos = get_channel_info_data(channel_name, is_premium)
    if not videos:
        raise HTTPException(status_code=404, detail="Channel not found")

    trend_data = []
    for vid in videos["latest_videos"]:
        counts = analyze_video_comments(vid["video_id"])
        trend_data.append(VideoTrend(
            video_id=vid["video_id"],
            title=vid["title"],
            hate_count=counts["hate_count"],
            request_count=counts["request_count"],
            question_count=counts["question_count"],
            feedback_count=counts["feedback_count"]
        ))

    set_cache(cache_key, {"trend_data": trend_data}, 1800)
    return {"trend_data": trend_data}


# -------------------------------
# 3) Video Analysis
# -------------------------------
@app.get("/video_analysis")
async def video_analysis(
    request: Request,
    video_id: str = Query(...),
    is_premium: bool = Query(False),
    batch_size: int = Query(50, description="Number of comments to process per batch")
):  
    cache_key = f"video_analysis:{video_id}:{is_premium}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    client_ip = request.client.host
    limit = 50 if is_premium else 5
    check_rate_limit(client_ip, limit)

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

    try:
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
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"YouTube API error: {str(e)}")

    # === 3) Batch classify ===
    pie_chart = {"hate_speech": 0, "questions": 0, "requests": 0, "feedback": 0, "neutral": 0}
    questions, requests, feedbacks = [], [], []

    # Process in batches
    for i in range(0, len(comments), batch_size):
        batch = comments[i:i+batch_size]

        hate_preds = hate_model.predict(batch)
        question_preds = question_model.predict(batch)
        request_preds = request_model.predict(batch)
        feedback_preds = feedback_model.predict(batch)

        for j, c in enumerate(batch):
            if hate_preds[j] == 1:
                pie_chart["hate_speech"] += 1
            elif question_preds[j] == 1:
                pie_chart["questions"] += 1
                questions.append(c)
            elif request_preds[j] == 1:
                pie_chart["requests"] += 1
                requests.append(c)
            elif feedback_preds[j] == 1:
                pie_chart["feedback"] += 1
                feedbacks.append(c)
            else:
                pie_chart["neutral"] += 1

    # === 4) Summarize & rank ===
    def process_category(data, filter_fn):
        if len(data) >= 10:
            data = filter_fn(data)
            data = rank_comments(data)
        return data

    filters = {
        "questions": process_category(questions, filter_questions),
        "requests": process_category(requests, filter_requests),
        "feedback": process_category(feedbacks, filter_feedbacks),
    }

    result = {
        "video_id": video_id,
        "title": title,
        "thumbnail_url": thumbnail_url,
        "pie_chart_data": pie_chart,
        "summaries": filters
    }

    set_cache(cache_key, result, 3600)  # cache for 1 hour
    return result



# -------------------------------
# 4) Most Liked Comments
# -------------------------------
@app.get("/most_liked")
async def most_liked_comments(
    request: Request,
    video_id: str = Query(...),
    is_premium: bool = Query(False)  # Add this
):
    cache_key = f"most_liked:{video_id}:{is_premium}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    client_ip = request.client.host
    limit = 50 if is_premium else 5
    check_rate_limit(client_ip, limit)
    """
    Get the most liked comment for each category (question/request/feedback).
    """
    comments = []
    next_page_token = None

    while len(comments) < 1000:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response["items"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append((snippet["textDisplay"], snippet["likeCount"]))

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    if not comments:
        return {"top_comments": {
            "most_liked_question": {"text": None, "like_count": 0},
            "most_liked_request": {"text": None, "like_count": 0},
            "most_liked_feedback": {"text": None, "like_count": 0},
        }}

    most_liked = {
        "question": {"text": "", "like_count": -1},
        "request": {"text": "", "like_count": -1},
        "feedback": {"text": "", "like_count": -1},
    }

    texts, likes = zip(*comments)
    question_preds = question_model.predict(texts)
    request_preds = request_model.predict(texts)
    feedback_preds = feedback_model.predict(texts)

    for i, text in enumerate(texts):
        like_count = likes[i]
        if question_preds[i] == 1 and like_count > most_liked["question"]["like_count"]:
            most_liked["question"] = {"text": text, "like_count": like_count}
        elif request_preds[i] == 1 and like_count > most_liked["request"]["like_count"]:
            most_liked["request"] = {"text": text, "like_count": like_count}
        elif feedback_preds[i] == 1 and like_count > most_liked["feedback"]["like_count"]:
            most_liked["feedback"] = {"text": text, "like_count": like_count}

    return {"top_comments": {
        "most_liked_question": most_liked["question"],
        "most_liked_request": most_liked["request"],
        "most_liked_feedback": most_liked["feedback"],
    }}


# -------------------------------
# 5) Comment Trend
# -------------------------------
@app.get("/comment_trend")
async def comment_trend(
    request: Request,
    video_id: str = Query(...),
    is_premium: bool = Query(False)
):  
    cache_key = f"comment_trend:{video_id}:{is_premium}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    client_ip = request.client.host
    limit = 50 if is_premium else 5
    check_rate_limit(client_ip, limit)
    """
    Returns daily comment count trend for a video.
    Free: Last 7 days
    Premium: Last 28 days
    """
    days = 28 if is_premium else 7
    today = datetime.utcnow().date()
    date_counts = defaultdict(int)

    comments = []
    next_page_token = None
    max_comments = 1000

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
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            published_at = snippet["publishedAt"]
            published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date()

            if today - timedelta(days=days) <= published_date <= today:
                date_counts[str(published_date)] += 1

            comments.append(snippet["textDisplay"])
            if len(comments) >= max_comments:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    trend = [{"date": str(today - timedelta(days=i)), "comment_count": date_counts.get(str(today - timedelta(days=i)), 0)}
             for i in range(days)]

    return {"video_id": video_id, "days": list(reversed(trend))}

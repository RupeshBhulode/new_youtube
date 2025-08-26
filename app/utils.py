# app/utils.py

from app.youtube_api import youtube
from app.models import hate_model, request_model, question_model, feedback_model
from app.cache import get_cache, set_cache   # ✅ FIXED

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from googleapiclient.errors import HttpError


def analyze_video_comments(video_id: str, max_comments: int = 200):
    cache_key = f"comments_analysis:{video_id}:{max_comments}"
    cached = get_cache(cache_key)
    if cached:
        return {"source": "cache", **cached}

    comments = []
    next_page_token = None

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
        if e.resp.status == 403 and "commentsDisabled" in str(e):
            return {
                "hate_count": 0,
                "request_count": 0,
                "question_count": 0,
                "feedback_count": 0
            }
        else:
            raise

    hate_count = sum([1 for c in comments if hate_model.predict([c])[0] == 1])
    request_count = sum([1 for c in comments if request_model.predict([c])[0] == 1])
    question_count = sum([1 for c in comments if question_model.predict([c])[0] == 1])
    feedback_count = sum([1 for c in comments if feedback_model.predict([c])[0] == 1])

    result = {
        "hate_count": hate_count,
        "request_count": request_count,
        "question_count": question_count,
        "feedback_count": feedback_count
    }

    # ✅ store in cache
    set_cache(cache_key, result, 3600)
    return result


def summarize_comments(comments, max_points=10):
    if not comments:
        return ["No comments in this category."]

    comments = [c for c in comments if c and isinstance(c, str)]
    return comments[:max_points]


def rank_comments(comments: list, top_k: int = 10):
    if len(comments) == 0:
        return []

    # Step 1: Vectorize
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(comments)

    # Step 2: Mean vector (flattened correctly ✅)
    mean_vec = X.mean(axis=0).A1

    # Step 3: Cosine similarity
    scores = cosine_similarity(X, mean_vec.reshape(1, -1)).flatten()

    # Step 4: Sort
    sorted_indices = np.argsort(scores)[::-1]
    sorted_comments = [comments[i] for i in sorted_indices]

    # Step 5: Pick diverse top_k
    chunk_size = max(1, len(sorted_comments) // top_k)
    diverse_comments = []

    for i in range(top_k):
        start = i * chunk_size
        end = start + chunk_size
        if start >= len(sorted_comments):
            break
        chunk = sorted_comments[start:end]
        if chunk:
            diverse_comments.append(chunk[0])

    return diverse_comments

# app/utils.py

from app.youtube_api import youtube
from app.models import hate_model, request_model, question_model, feedback_model
from app.cache import get_cache, set_cache   # ✅ FIXED

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from googleapiclient.errors import HttpError


def analyze_video_comments(video_id: str, max_comments: int = 200):
    """
    Fetch comments (up to max_comments), classify them in batches using the
    models, return counts and store result in cache.
    """
    cache_key = f"comments_analysis:{video_id}:{max_comments}"
    cached = get_cache(cache_key)
    if cached:
        # Return exactly the same shape as a fresh result (no unexpected keys)
        # If you want to keep a debug source, you can return {"source":"cache", **cached}
        return cached

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

            for item in response.get("items", []):
                # defensive extraction
                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                comment = snippet.get("textDisplay")
                if comment:
                    comments.append(comment)
                if len(comments) >= max_comments:
                    break

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

    except HttpError as e:
        # preserve your existing behavior for comments disabled
        if getattr(e, "resp", None) and getattr(e.resp, "status", None) == 403 and "commentsDisabled" in str(e):
            result = {
                "hate_count": 0,
                "request_count": 0,
                "question_count": 0,
                "feedback_count": 0
            }
            set_cache(cache_key, result, 3600)
            return result
        # re-raise other YouTube errors so upper layer can handle it
        raise

    # If no comments, return zeros
    if not comments:
        result = {
            "hate_count": 0,
            "request_count": 0,
            "question_count": 0,
            "feedback_count": 0
        }
        set_cache(cache_key, result, 3600)
        return result

    # Predict in batches to avoid calling predict per comment
    def batch_predict(model, texts, batch_size=128):
        preds = []
        for i in range(0, len(texts), batch_size):
            try:
                batch = texts[i:i+batch_size]
                p = model.predict(batch)
                preds.extend(list(p))
            except Exception:
                # if model fails for some reason, fallback to zeros for that batch
                preds.extend([0] * len(batch))
        return preds

    hate_preds = batch_predict(hate_model, comments)
    request_preds = batch_predict(request_model, comments)
    question_preds = batch_predict(question_model, comments)
    feedback_preds = batch_predict(feedback_model, comments)

    # Count occurrences: a simple rule — prioritize hate, otherwise check others
    hate_count = 0
    request_count = 0
    question_count = 0
    feedback_count = 0

    for i, _ in enumerate(comments):
        try:
            if hate_preds[i] == 1:
                hate_count += 1
            elif question_preds[i] == 1:
                question_count += 1
            elif request_preds[i] == 1:
                request_count += 1
            elif feedback_preds[i] == 1:
                feedback_count += 1
        except IndexError:
            # defensive: if lengths mismatch, skip
            continue

    result = {
        "hate_count": int(hate_count),
        "request_count": int(request_count),
        "question_count": int(question_count),
        "feedback_count": int(feedback_count)
    }

    # store in cache (SQLite json-serializable)
    try:
        set_cache(cache_key, result, 3600)
    except Exception:
        # don't fail the endpoint if cache write fails
        pass

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

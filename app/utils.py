from app.youtube_api import youtube
from app.models import hate_model, request_model, question_model, feedback_model
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np

from googleapiclient.errors import HttpError

def analyze_video_comments(video_id: str, max_comments: int = 200):
    """
    Fetch comments and categorize counts for 1 video.
    If comments are disabled, safely return zero counts.
    """
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
            # Comments are disabled for this video
            return {
                "hate_count": 0,
                "request_count": 0,
                "question_count": 0,
                "feedback_count": 0
            }
        else:
            # Other API errors: raise to debug properly
            raise

    hate_count = sum([1 for c in comments if hate_model.predict([c])[0] == 1])
    request_count = sum([1 for c in comments if request_model.predict([c])[0] == 1])
    question_count = sum([1 for c in comments if question_model.predict([c])[0] == 1])
    feedback_count = sum([1 for c in comments if feedback_model.predict([c])[0] == 1])

    return {
        "hate_count": hate_count,
        "request_count": request_count,
        "question_count": question_count,
        "feedback_count": feedback_count
    }

def summarize_comments(comments, model, max_points=10):
    if not comments:
        return ["No comments in this category."]
    if len(comments) <= max_points:
        return comments

    embeddings = model.encode(comments)

    for k in range(max_points, 1, -1):
        kmeans = KMeans(n_clusters=k, random_state=0)
        kmeans.fit(embeddings)
        cluster_assignment = kmeans.labels_
        cluster_centers = kmeans.cluster_centers_

        empty = any(np.sum(cluster_assignment == i) == 0 for i in range(k))
        if not empty:
            break
    else:
        k = 1
        kmeans = KMeans(n_clusters=k, random_state=0).fit(embeddings)
        cluster_assignment = kmeans.labels_
        cluster_centers = kmeans.cluster_centers_

    summary_sentences = []
    for i in range(k):
        cluster_indices = np.where(cluster_assignment == i)[0]
        closest_index = cluster_indices[
            np.argmin(np.linalg.norm(embeddings[cluster_indices] - cluster_centers[i], axis=1))
        ]
        summary_sentences.append(comments[closest_index])

    return summary_sentences
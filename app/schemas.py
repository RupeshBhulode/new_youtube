from pydantic import BaseModel # type: ignore
from typing import List


class VideoInfo(BaseModel):
    video_id: str
    title: str
    thumbnail_url: str


class ChannelInfoSchema(BaseModel):
    channel_id: str
    channel_name: str
    profile_image: str
    subscriber_count: int
    latest_videos: List[VideoInfo]


class VideoTrend(BaseModel):
    video_id: str
    title: str
    hate_count: int
    request_count: int
    question_count: int
    feedback_count: int


class MultiVideoTrendResponse(BaseModel):
    trend_data: List[VideoTrend]

class CommentRequest(BaseModel):
    comments: List[str]

class RankedCommentsResponse(BaseModel):
    top_comments: List[str]
    
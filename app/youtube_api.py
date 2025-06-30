from googleapiclient.discovery import build # type: ignore
from datetime import datetime


#API_KEY =  'AIzaSyDYjOKHNOf-fY55p_MQA93Eaj13Uvv4puY'
#AIzaSyA0s8gvFZJBQHgSlYdF4lG78FM0YLb4wm0
#AIzaSyCTFcusoP1DJb_nwSMwftESGyFchn_Kdgo


API_KEYS = [
    "AIzaSyDYjOKHNOf-fY55p_MQA93Eaj13Uvv4puY",
    "AIzaSyA0s8gvFZJBQHgSlYdF4lG78FM0YLb4wm0",
    "AIzaSyCTFcusoP1DJb_nwSMwftESGyFchn_Kdgo"
]

def get_current_api_key():
    """Rotate API key every 2 hours UTC."""
    now = datetime.utcnow()
    hour = now.hour
    key_index = (hour // 1) % len(API_KEYS)
    return API_KEYS[key_index]

# Get the rotated key
current_key = get_current_api_key()

# Build the YouTube API client
youtube = build("youtube", "v3", developerKey=current_key)

def get_channel_info_data(channel_name: str, is_premium: bool):
    search_response = youtube.search().list(
        q=channel_name,
        type="channel",
        part="id,snippet",
        maxResults=1
    ).execute()

    if not search_response["items"]:
        return None

    channel = search_response["items"][0]
    channel_id = channel["id"]["channelId"]
    channel_name = channel["snippet"]["title"]
    profile_image = channel["snippet"]["thumbnails"].get("high", {}).get("url") or \
                    channel["snippet"]["thumbnails"].get("default", {}).get("url")

    stats = youtube.channels().list(
        part="statistics",
        id=channel_id
    ).execute()
    subscriber_count = int(stats["items"][0]["statistics"].get("subscriberCount", 0))

  # Get branding settings (for banner image)
    


    uploads_playlist = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    max_videos = 10 if is_premium else 3

    playlist_items = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist,
        maxResults=max_videos
    ).execute()

    latest_videos = []
    for item in playlist_items.get("items", []):
        snippet = item["snippet"]
        vid = {
            "video_id": snippet["resourceId"]["videoId"],
            "title": snippet["title"],
            "thumbnail_url": snippet["thumbnails"]["high"]["url"]
        }
        latest_videos.append(vid)

    return {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "profile_image": profile_image,
        "subscriber_count": subscriber_count,
        "latest_videos": latest_videos
    }

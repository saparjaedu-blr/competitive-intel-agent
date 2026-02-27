from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from googleapiclient.discovery import build
import re


MAX_TRANSCRIPT_CHARS = 6000


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(video_id: str) -> str:
    """Fetch transcript for a YouTube video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([t["text"] for t in transcript_list])
        return text[:MAX_TRANSCRIPT_CHARS]
    except (NoTranscriptFound, TranscriptsDisabled):
        return "[No transcript available for this video]"
    except Exception as e:
        return f"[Transcript error: {str(e)}]"


def search_channel_videos(channel_handle: str, max_results: int = 5) -> list[dict]:
    """
    Search for recent videos from a YouTube channel.
    channel_handle: e.g. '@SalesforceYT' or a channel ID like 'UCxyz...'
    Returns list of {video_id, title, published_at}
    
    NOTE: Requires YOUTUBE_API_KEY in env for channel search.
    Falls back to empty list if not configured.
    """
    import os
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return []

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        # Resolve channel handle to channel ID if needed
        if channel_handle.startswith("@"):
            search_response = youtube.search().list(
                q=channel_handle,
                type="channel",
                part="id",
                maxResults=1
            ).execute()
            if not search_response.get("items"):
                return []
            channel_id = search_response["items"][0]["id"]["channelId"]
        else:
            channel_id = channel_handle

        # Get recent uploads
        search_response = youtube.search().list(
            channelId=channel_id,
            part="id,snippet",
            order="date",
            maxResults=max_results,
            type="video"
        ).execute()

        videos = []
        for item in search_response.get("items", []):
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"],
            })
        return videos

    except Exception as e:
        return []


def fetch_channel_transcripts(channel_handle: str, max_videos: int = 5) -> str:
    """
    Fetch transcripts for the most recent N videos from a channel.
    Returns concatenated transcript text.
    """
    if not channel_handle:
        return ""

    videos = search_channel_videos(channel_handle, max_results=max_videos)

    if not videos:
        # If no API key or channel lookup failed, return empty
        return "[YouTube channel configured but no videos retrieved — add YOUTUBE_API_KEY to .env]"

    results = []
    for video in videos:
        transcript = get_transcript(video["video_id"])
        results.append(
            f"--- Video: {video['title']} ({video['published_at'][:10]}) ---\n{transcript}"
        )

    return "\n\n".join(results)


def fetch_transcript_from_url(url: str) -> str:
    """Fetch transcript from a direct YouTube URL."""
    video_id = extract_video_id(url)
    if not video_id:
        return f"[Could not extract video ID from: {url}]"
    return get_transcript(video_id)

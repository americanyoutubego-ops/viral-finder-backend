from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeClient:
    """Обгортка над YouTube Data API v3."""

    def __init__(self, api_key):
        if not api_key:
            raise RuntimeError("API-ключ не заданий.")
        self.yt = build("youtube", "v3", developerKey=api_key, cache_discovery=False)

    def search(self, query, max_results=50, region="US",
               published_after=None, result_type="video",
               language=None, video_duration=None):
        ids, token, fetched = [], None, 0
        while fetched < max_results:
            page_size = min(50, max_results - fetched)
            params = dict(q=query, part="id", type=result_type,
                          maxResults=page_size, order="viewCount", regionCode=region)
            if token:
                params["pageToken"] = token
            if published_after and result_type == "video":
                params["publishedAfter"] = published_after
            if language and result_type == "video":
                params["relevanceLanguage"] = language
            if video_duration and result_type == "video":
                params["videoDuration"] = video_duration
            try:
                resp = self.yt.search().list(**params).execute()
            except HttpError as e:
                raise RuntimeError(f"Помилка пошуку YouTube: {e}") from e
            key = "videoId" if result_type == "video" else "channelId"
            for item in resp.get("items", []):
                _id = item["id"].get(key)
                if _id:
                    ids.append(_id)
            fetched += page_size
            token = resp.get("nextPageToken")
            if not token:
                break
        return ids

    def videos_details(self, video_ids):
        out = []
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i + 50]
            resp = self.yt.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(chunk), maxResults=50).execute()
            out.extend(resp.get("items", []))
        return out

    def channels_stats(self, channel_ids):
        out = {}
        uniq = list(dict.fromkeys(channel_ids))
        for i in range(0, len(uniq), 50):
            chunk = uniq[i:i + 50]
            resp = self.yt.channels().list(
                part="statistics,snippet",
                id=",".join(chunk), maxResults=50).execute()
            for item in resp.get("items", []):
                out[item["id"]] = item
        return out
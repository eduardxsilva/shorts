from __future__ import annotations

from pathlib import Path

class YouTubeUploadError(RuntimeError): pass

def upload_video(video_path: Path, secrets_path: Path, token_path: Path, *, title: str, description: str, tags: list[str], privacy_status="private") -> dict:
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
        creds=Credentials.from_authorized_user_file(str(token_path),scopes) if token_path.exists() else None
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        if not creds or not creds.valid:
            flow=InstalledAppFlow.from_client_secrets_file(str(secrets_path),scopes); creds=flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True,exist_ok=True); token_path.write_text(creds.to_json(),encoding="utf-8")
        service=build("youtube","v3",credentials=creds)
        request=service.videos().insert(part="snippet,status",body={"snippet":{"title":title,"description":description,"tags":tags,"categoryId":"22"},"status":{"privacyStatus":privacy_status}},media_body=MediaFileUpload(str(video_path),mimetype="video/mp4",resumable=True))
        response=None
        while response is None: _,response=request.next_chunk()
        return response
    except Exception as exc:
        raise YouTubeUploadError(str(exc)) from exc

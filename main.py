from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from instagrapi import Client
import os, base64, tempfile, json
from pathlib import Path

app = FastAPI(title="Instagram Poster API")

# ── Auth ──────────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("API_KEY", "supersecret123")
IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")
SESSION_FILE = "/tmp/ig_session.json"

cl = Client()

def get_client() -> Client:
    if os.path.exists(SESSION_FILE):
        cl.load_settings(SESSION_FILE)
        cl.login(IG_USERNAME, IG_PASSWORD)
    else:
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings(SESSION_FILE)
    return cl

# ── Models ────────────────────────────────────────────────────────────────────
class PhotoRequest(BaseModel):
    image_base64: str          # base64 encoded image
    caption: str = ""
    filename: str = "photo.jpg"

class VideoRequest(BaseModel):
    video_base64: str          # base64 encoded video
    caption: str = ""
    filename: str = "video.mp4"

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/post/photo")
def post_photo(req: PhotoRequest, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        client = get_client()
        img_data = base64.b64decode(req.image_base64)
        
        with tempfile.NamedTemporaryFile(suffix=Path(req.filename).suffix, delete=False) as f:
            f.write(img_data)
            tmp_path = f.name
        
        media = client.photo_upload(tmp_path, caption=req.caption)
        os.unlink(tmp_path)
        
        return {"success": True, "media_id": str(media.pk), "type": "photo"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/post/video")
def post_video(req: VideoRequest, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        client = get_client()
        vid_data = base64.b64decode(req.video_base64)
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(vid_data)
            tmp_path = f.name
        
        media = client.clip_upload(tmp_path, caption=req.caption)
        os.unlink(tmp_path)
        
        return {"success": True, "media_id": str(media.pk), "type": "reel"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

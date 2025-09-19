import logging
import os, tempfile, shutil, subprocess
from typing import Dict, Any, Optional

from fastapi import FastAPI, Body, HTTPException

try:  # pragma: no cover - exercised via tests with monkeypatching
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

try:  # pragma: no cover - exercised via tests with monkeypatching
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover
    WhisperModel = None  # type: ignore
import shutil as _shutil

from services.common.supabase import insert_segments

app = FastAPI(title="FFmpeg+Whisper (faster-whisper)", version="2.0.0")

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT") or os.environ.get("S3_ENDPOINT") or "minio:9000"
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY") or os.environ.get("AWS_ACCESS_KEY_ID") or "minioadmin"
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY") or "minioadmin"
MINIO_SECURE = (os.environ.get("MINIO_SECURE","false").lower() == "true")
MEDIA_AUDIO_URL = os.environ.get("MEDIA_AUDIO_URL")


logger = logging.getLogger(__name__)


def _coerce_timeout(value: Optional[str]) -> float:
    if not value:
        return 10.0
    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid MEDIA_AUDIO_TIMEOUT value '%s'; using default", value)
        return 10.0


MEDIA_AUDIO_TIMEOUT = _coerce_timeout(os.environ.get("MEDIA_AUDIO_TIMEOUT"))

def s3_client():
    if boto3 is None:  # pragma: no cover - real runtime will have boto3
        raise RuntimeError("boto3 is required but not installed")
    endpoint_url = MINIO_ENDPOINT if "://" in MINIO_ENDPOINT else f"{'https' if MINIO_SECURE else 'http'}://{MINIO_ENDPOINT}"
    return boto3.client("s3", aws_access_key_id=MINIO_ACCESS_KEY, aws_secret_access_key=MINIO_SECRET_KEY, endpoint_url=endpoint_url)

@app.get('/healthz')
def healthz():
    return {'ok': True}

def ffmpeg_extract_audio(src: str, dst: str):
    # Example: convert to m4a AAC
    cmd = ['ffmpeg','-y','-i', src,'-vn','-acodec','aac','-b:a','128k', dst]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _select_device() -> str:
    # Prefer CUDA if available; allow override via WHISPER_DEVICE / USE_CUDA
    dev = os.environ.get("WHISPER_DEVICE")
    if dev:
        return dev
    if os.environ.get("USE_CUDA","false").lower() == "true":
        return "cuda"
    if _shutil.which("nvidia-smi"):
        return "cuda"
    return "cpu"


def _forward_to_audio_service(payload: Dict[str, Any]) -> bool:
    """Forward transcription metadata to the media-audio service.

    Returns True when forwarding succeeds, False otherwise. When forwarding is
    disabled (MEDIA_AUDIO_URL unset) or encounters an error, False is returned
    so the caller can fall back to inserting segments locally.
    """

    if not MEDIA_AUDIO_URL:
        return False

    try:
        import requests  # type: ignore
    except ImportError:  # pragma: no cover - should not happen in production
        logger.warning("requests is unavailable; skipping media-audio forwarding")
        return False

    try:
        resp = requests.post(MEDIA_AUDIO_URL, json=payload, timeout=MEDIA_AUDIO_TIMEOUT)
    except Exception as exc:  # pragma: no cover - network failures are rare in tests
        logger.warning("Failed to forward transcription to media-audio: %s", exc, exc_info=True)
        return False

    if not resp.ok:
        logger.warning(
            "Media-audio forward returned non-success status %s: %s",
            getattr(resp, "status_code", "?"),
            getattr(resp, "text", ""),
        )
        return False

    return True


@app.post('/transcribe')
def transcribe(body: Dict[str,Any] = Body(...)):
    bucket = body.get('bucket'); key = body.get('key'); vid = body.get('video_id')
    if not bucket or not key:
        raise HTTPException(400, 'bucket and key required')
    lang = body.get('language'); model_name = body.get('whisper_model') or 'base'
    out_audio_key = body.get('out_audio_key')
    tmpd = tempfile.mkdtemp(prefix='ffw-')
    s3 = s3_client()
    try:
        # fetch source
        src_path = os.path.join(tmpd, 'raw.mp4')
        with open(src_path, 'wb') as w:
            s3.download_fileobj(bucket, key, w)
        # extract audio
        audio_path = os.path.join(tmpd, 'audio.m4a')
        ffmpeg_extract_audio(src_path, audio_path)
        # upload audio if requested
        s3_uri = None
        if out_audio_key:
            s3.upload_file(audio_path, bucket, out_audio_key)
            scheme = 'https' if MINIO_SECURE else 'http'
            s3_uri = f"{scheme}://{MINIO_ENDPOINT}/{bucket}/{out_audio_key}"
        # faster-whisper (ctranslate2). Uses CUDA if available.
        device = _select_device()
        compute_type = 'float16' if device == 'cuda' else 'int8'
        if WhisperModel is None:
            raise HTTPException(500, 'WhisperModel backend not available')
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        segments_iter, info = model.transcribe(audio_path, language=lang)
        segs = []
        text_parts = []
        for seg in segments_iter:
            try:
                segs.append({
                    'start': float(getattr(seg, 'start', 0.0) or 0.0),
                    'end': float(getattr(seg, 'end', 0.0) or 0.0),
                    'text': (getattr(seg, 'text', '') or '').strip()
                })
                text_parts.append((getattr(seg, 'text', '') or ''))
            except Exception:
                continue
        text = ''.join(text_parts)
        rows = [
            {
                'video_id': vid,
                'ts_start': s['start'],
                'ts_end': s['end'],
                'uri': s3_uri,
                'meta': {'text': s['text']}
            }
            for s in segs
        ]
        payload = {
            'video_id': vid,
            'segments': segs,
            'rows': rows,
            'bucket': bucket,
            'key': key,
            'audio_uri': s3_uri,
            'language': getattr(info, 'language', None) or lang,
            'text': text,
        }
        forwarded = _forward_to_audio_service(payload)
        if not forwarded:
            if MEDIA_AUDIO_URL:
                logger.info("media-audio forwarding unavailable; inserting segments locally for video_id=%s", vid)
            insert_segments(rows)
        return {'ok': True, 'text': text, 'segments': segs, 'language': getattr(info, 'language', None) or lang, 's3_uri': s3_uri, 'device': device}
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"ffmpeg error: {e}")
    except Exception as e:
        raise HTTPException(500, f"transcribe error: {e}")
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

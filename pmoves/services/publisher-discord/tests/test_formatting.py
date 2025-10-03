import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PM = Path(__file__).resolve().parents[4]
for p in (str(ROOT), str(PM)):
    if p not in sys.path:
        sys.path.insert(0, p)

from pmoves.services.publisher_discord import main as discord


def test_format_content_published_embed_minimal():
    name = "content.published.v1"
    payload = {
        "title": "Sample",
        "namespace": "pmoves",
        "published_path": "/library/pmoves/sample.png",
        "artifact_uri": "s3://assets/pmoves/sample.png",
        "public_url": "http://media.local/pmoves/sample.png",
        "meta": {"duration": 12.3},
    }
    out = discord._format_event(name, payload)
    assert out.get("embeds") and isinstance(out["embeds"], list)
    emb = out["embeds"][0]
    assert emb["title"] == "Sample"
    assert any(f.get("name") == "Published Path" for f in emb.get("fields", []))
    assert any(f.get("name") == "Artifact URI" for f in emb.get("fields", []))


def test_format_adds_jellyfin_link_when_id_present():
    name = "content.published.v1"
    payload = {
        "title": "Episode 1",
        "namespace": "shows",
        "jellyfin_item_id": "abc123",
        "meta": {"jellyfin_base_url": "http://jf"},
    }
    out = discord._format_event(name, payload)
    fields = out["embeds"][0].get("fields", [])
    jf = [f for f in fields if f.get("name") == "Jellyfin"]
    assert jf and jf[0]["value"].startswith("http://jf/web/index.html#!/details?id=abc123")

import os, json, re
from typing import Dict, Any, Optional
import requests

from .base import BaseProvider

def _parse_json_from_text(text: str) -> Dict[str, Any]:
    # Try to extract JSON block from text (handles fenced code blocks)
    m = re.search(r"\{[\s\S]*\}\s*$", text.strip())
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    # fallback entire content
    try:
        return json.loads(text)
    except Exception:
        return {"chunks": [], "errors": []}

SYS_PROMPT = (
    "You are a precise information extraction engine. Segment input into a small set of coherent chunks suitable for retrieval (50-300 words each). "
    "Also extract any troubleshooting errors. Return strict JSON with fields: {chunks: [{doc_id, section_id, chunk_id, namespace, text, kind}], errors: [{message, code, service, host, severity, timestamp, stack}]}."
)

USER_TMPL_TEXT = (
    "Namespace: {ns} DocID: {doc}\n\n"
    "Text to segment and analyze:\n"""{content}"""\n"
)

USER_TMPL_XML = (
    "Namespace: {ns} DocID: {doc}\n\n"
    "XML to segment and analyze for IT errors:\n"""{content}"""\n"
)

class OpenAIChatProvider(BaseProvider):
    def __init__(self):
        self.base = os.environ.get("OPENAI_API_BASE") or os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENROUTER_API_BASE", "https://api.openai.com")
        self.key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GROQ_API_KEY")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        if not self.key:
            raise RuntimeError("OpenAI-compatible provider selected but no API key configured")

    def _chat(self, content: str) -> Dict[str, Any]:
        url = f"{self.base.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.key}", "content-type": "application/json"}
        data = {"model": self.model, "response_format": {"type":"json_object"}, "messages": [
            {"role":"system","content": SYS_PROMPT},
            {"role":"user","content": content}
        ]}
        r = requests.post(url, headers=headers, json=data, timeout=60)
        r.raise_for_status()
        txt = r.json()["choices"][0]["message"]["content"]
        return _parse_json_from_text(txt)

    def extract_text(
        self,
        document: str,
        namespace: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body = USER_TMPL_TEXT.format(ns=namespace, doc=doc_id, content=document)
        return self._chat(body)

    def extract_xml(
        self,
        xml: str,
        namespace: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body = USER_TMPL_XML.format(ns=namespace, doc=doc_id, content=xml)
        return self._chat(body)

class GeminiProvider(BaseProvider):
    def __init__(self):
        self.key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        if not self.key:
            raise RuntimeError("Gemini provider selected but no API key configured")

    def _call(self, content: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.key}"
        payload = {"contents": [{"parts": [{"text": SYS_PROMPT + "\n\n" + content}]}]}
        r = requests.post(url, headers={"content-type":"application/json"}, json=payload, timeout=60)
        r.raise_for_status()
        txt = (r.json().get("candidates") or [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
        return _parse_json_from_text(txt)

    def extract_text(
        self,
        document: str,
        namespace: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._call(USER_TMPL_TEXT.format(ns=namespace, doc=doc_id, content=document))

    def extract_xml(
        self,
        xml: str,
        namespace: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._call(USER_TMPL_XML.format(ns=namespace, doc=doc_id, content=xml))


class TensorZeroProvider(BaseProvider):
    def __init__(self):
        self.base = os.environ.get("TENSORZERO_BASE_URL", "http://localhost:3030")
        self.api_key = os.environ.get("TENSORZERO_API_KEY")
        self.model = (
            os.environ.get("TENSORZERO_MODEL")
            or os.environ.get("TENSORZERO_CHAT_MODEL")
            or os.environ.get("TENSORZERO_DEFAULT_MODEL")
            or "openai::gpt-4o-mini"
        )
        self.timeout = int(os.environ.get("TENSORZERO_TIMEOUT_SECONDS", "60"))
        self.static_tags = self._load_static_tags()

    def _load_static_tags(self) -> Dict[str, str]:
        raw = os.environ.get("TENSORZERO_STATIC_TAGS")
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {
                    str(k): str(v)
                    for k, v in parsed.items()
                    if v is not None and str(v).strip()
                }
        except json.JSONDecodeError:
            pass
        tags: Dict[str, str] = {}
        for item in raw.split(","):
            if not item.strip():
                continue
            if "=" in item:
                key, value = item.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    tags[key] = value
        return tags

    def _build_tags(
        self,
        namespace: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, str]:
        tags: Dict[str, str] = {
            "pmoves_namespace": namespace,
            "pmoves_doc_id": doc_id,
        }
        tags.update(self.static_tags)
        if isinstance(metadata, dict):
            extra_tags = metadata.get("tags") if isinstance(metadata.get("tags"), dict) else {}
            for key, value in extra_tags.items():
                if value is None:
                    continue
                tags[str(key)] = str(value)
            for key, value in metadata.items():
                if key == "tags" or value is None:
                    continue
                tags[f"pmoves_{key}"] = str(value)
        return {k: v for k, v in tags.items() if v}

    def _chat(
        self,
        content: str,
        namespace: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        url = f"{self.base.rstrip('/')}/openai/v1/chat/completions"
        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if isinstance(metadata, dict):
            request_id = metadata.get("request_id") or metadata.get("trace_id")
            if request_id:
                headers.setdefault("X-Request-ID", str(request_id))
        payload: Dict[str, Any] = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYS_PROMPT},
                {"role": "user", "content": content},
            ],
        }
        tags = self._build_tags(namespace, doc_id, metadata)
        if tags:
            payload["tensorzero::tags"] = tags
        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        r.raise_for_status()
        txt = r.json()["choices"][0]["message"]["content"]
        return _parse_json_from_text(txt)

    def extract_text(
        self,
        document: str,
        namespace: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body = USER_TMPL_TEXT.format(ns=namespace, doc=doc_id, content=document)
        return self._chat(body, namespace, doc_id, metadata)

    def extract_xml(
        self,
        xml: str,
        namespace: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body = USER_TMPL_XML.format(ns=namespace, doc=doc_id, content=xml)
        return self._chat(body, namespace, doc_id, metadata)


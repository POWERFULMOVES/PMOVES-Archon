"""Deep Research worker utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple


class InvalidResearchRequest(ValueError):
    """Raised when a research request payload cannot be decoded."""


@dataclass(slots=True)
class ResearchRequest:
    """Normalised representation of a deep research job."""

    query: str
    mode: str = "standard"
    max_steps: Optional[int] = None
    context: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    notebook_overrides: Dict[str, Any] = field(default_factory=dict)
    extras: Dict[str, Any] = field(default_factory=dict)


def _normalise_context(raw: Any) -> List[Any]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Iterable) and not isinstance(raw, (bytes, bytearray, dict)):
        return list(raw)
    if isinstance(raw, dict):
        return [raw]
    raise InvalidResearchRequest("context must be a string, mapping, or iterable of items")


def _normalise_metadata(name: str, raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    raise InvalidResearchRequest(f"{name} must be an object when provided")


def _ensure_query(data: Dict[str, Any]) -> str:
    for key in ("query", "prompt", "question", "topic"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise InvalidResearchRequest("request payload must include a non-empty 'query'/'prompt' field")


def _decode_request(payload: Dict[str, Any]) -> ResearchRequest:
    """Validate an incoming envelope and return a :class:`ResearchRequest`."""

    if not isinstance(payload, dict):
        raise InvalidResearchRequest("request envelope must be a dictionary")
    body = payload.get("payload")
    if not isinstance(body, dict):
        raise InvalidResearchRequest("envelope missing payload object")

    query = _ensure_query(body)

    mode = body.get("mode") or "standard"
    if not isinstance(mode, str):
        raise InvalidResearchRequest("mode must be a string")

    max_steps_raw = body.get("max_steps")
    max_steps: Optional[int]
    if max_steps_raw is None:
        max_steps = None
    else:
        if isinstance(max_steps_raw, bool):
            raise InvalidResearchRequest("max_steps must be an integer")
        try:
            max_steps = int(max_steps_raw)
        except (TypeError, ValueError) as exc:
            raise InvalidResearchRequest("max_steps must be an integer") from exc
        if max_steps < 0:
            raise InvalidResearchRequest("max_steps must be >= 0")

    context = _normalise_context(body.get("context"))
    metadata = _normalise_metadata("metadata", body.get("metadata"))
    notebook_overrides = _normalise_metadata("notebook", body.get("notebook"))

    extras = {
        key: value
        for key, value in body.items()
        if key
        not in {
            "query",
            "prompt",
            "question",
            "topic",
            "mode",
            "max_steps",
            "context",
            "metadata",
            "notebook",
        }
    }

    return ResearchRequest(
        query=query,
        mode=mode,
        max_steps=max_steps,
        context=context,
        metadata=metadata,
        notebook_overrides=notebook_overrides,
        extras=extras,
    )


def _handle_request(payload: Dict[str, Any]) -> Tuple[Optional[ResearchRequest], Dict[str, Any]]:
    """Decode the incoming payload, surfacing schema errors in metadata."""

    try:
        request = _decode_request(payload)
    except InvalidResearchRequest as exc:
        return None, {"error": str(exc)}
    return request, dict(request.metadata)

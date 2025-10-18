"""EvoSwarm controller service.

This FastAPI worker periodically fetches recent geometry packets, evaluates fitness
metrics, and publishes updated parameter packs for CGP builders and decoders.
The concrete evolutionary logic will be filled in subsequent iterations; for now
we scaffold configuration, health endpoints, and background scheduling hooks.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI

logger = logging.getLogger("evo-controller")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="PMOVES Evo Controller", version="0.1.0")


@dataclass
class EvoConfig:
    """Runtime configuration for the controller loop."""

    rest_url: Optional[str] = field(default_factory=lambda: os.getenv("SUPA_REST_URL") or os.getenv("SUPABASE_REST_URL"))
    service_key: Optional[str] = field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    poll_seconds: float = float(os.getenv("EVOSWARM_POLL_SECONDS", "300"))
    sample_limit: int = int(os.getenv("EVOSWARM_SAMPLE_LIMIT", "25"))
    namespace: Optional[str] = os.getenv("EVOSWARM_NAMESPACE")


class EvoSwarmController:
    """Background task coordinator for the evolutionary loop."""

    def __init__(self, config: EvoConfig) -> None:
        self.config = config
        self._stop = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self) -> None:
        if self._task is None:
            logger.info("starting EvoSwarm controller loop")
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(20.0))
            self._task = asyncio.create_task(self._run())

    async def shutdown(self) -> None:
        if self._task:
            logger.info("stopping EvoSwarm controller loop")
            self._stop.set()
            await self._task
            self._task = None
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _run(self) -> None:
        while not self._stop.is_set():
            start = time.perf_counter()
            try:
                await self._tick()
            except Exception:  # pragma: no cover - logged for observability
                logger.exception("evoswarm tick failed")
            elapsed = time.perf_counter() - start
            sleep_for = max(5.0, self.config.poll_seconds - elapsed)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                continue

    async def _tick(self) -> None:
        """Single polling iteration (placeholder logic)."""

        if not self.config.rest_url:
            logger.warning("Supabase REST URL not configured; skipping tick")
            return
        # Placeholder: fetch recent CGPs for analysis.
        payload = await self._fetch_recent_cgps()
        logger.debug("fetched %s CGPs for evaluation", len(payload))
        # TODO: insert fitness computation and parameter pack publishing here.

    async def _fetch_recent_cgps(self) -> list[Dict[str, Any]]:
        """Stub for pulling recent CGPs from Supabase/PostgREST."""

        if not self._client or not self.config.rest_url:
            return []
        base_url = self.config.rest_url.rstrip("/")
        url = f"{base_url}/geometry_cgp_v1"
        headers = {"Accept": "application/json"}
        if self.config.service_key:
            headers.update({"apikey": self.config.service_key, "Authorization": f"Bearer {self.config.service_key}"})
        params = {
            "select": "payload,created_at",
            "order": "created_at.desc",
            "limit": str(self.config.sample_limit),
        }
        if self.config.namespace:
            params["payload->>namespace"] = f"eq.{self.config.namespace}"
        try:
            resp = await self._client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            rows = resp.json()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network failure
            logger.error("Supabase fetch failed: %s", exc)
            return []
        except Exception:
            logger.exception("unexpected error pulling CGPs")
            return []
        return [row.get("payload") for row in rows if isinstance(row, dict)]


_controller = EvoSwarmController(EvoConfig())


@app.on_event("startup")
async def _startup() -> None:
    await _controller.start()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await _controller.shutdown()


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Liveness check."""

    return {"ok": True, "loop_running": _controller._task is not None}


@app.get("/config")
async def config() -> Dict[str, Any]:
    """Expose current controller configuration for observability."""

    cfg = _controller.config
    return {
        "poll_seconds": cfg.poll_seconds,
        "sample_limit": cfg.sample_limit,
        "namespace": cfg.namespace,
        "rest_url_configured": bool(cfg.rest_url),
    }

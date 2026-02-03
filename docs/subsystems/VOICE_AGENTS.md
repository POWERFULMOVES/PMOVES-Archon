# Voice Agents Integration Guide

**Purpose:** Complete reference for PMOVES.AI voice agent capabilities including Flute-Gateway, Ultimate-TTS-Studio, and Pipecat integration.

**Last Updated:** 2026-01-31

---

## Overview

PMOVES.AI provides a comprehensive voice agent ecosystem with:

- **Flute-Gateway**: Production voice API with prosodic synthesis
- **Ultimate-TTS-Studio**: Multi-engine TTS playground with 7 engines
- **Pipecat Integration**: Real-time voice conversation framework

```
┌─────────────────────────────────────────────────────────────────┐
│                     PMOVES Voice Layer                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌─────────────────┐      ┌────────────┐ │
│  │   Flute      │──────▶│   Ultimate TTS  │◀─────▶│  Pipecat   │ │
│  │   Gateway    │      │     Studio      │      │  Pipeline  │ │
│  │  (8055/8056) │      │     (7861)      │      │            │ │
│  └──────────────┘      └─────────────────┘      └────────────┘ │
│         │                       │                     │          │
│         └───────────────────────┴─────────────────────┘          │
│                               │                                 │
│                         ┌──────▼──────┐                        │
│                         │    NATS     │                        │
│                         │   Message   │                        │
│                         │    Bus      │                        │
│                         └─────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Flute-Gateway

**Location:** `/pmoves/services/flute-gateway/`

**Purpose:** Production-ready voice API for prosodic text-to-speech synthesis with natural pauses, emphasis, and emotional expression.

**Ports:**
- `8055` - HTTP API
- `8056` - WebSocket (real-time audio streaming)

**Features:**
- **Prosodic TTS**: Natural speech with intelligent phrasing
- **Multiple Voice Providers**: VibeVoice, Whisper, Ultimate-TTS
- **WebSocket Streaming**: Real-time audio I/O
- **NATS Integration**: Voice event publishing
- **Health Monitoring**: `/healthz` endpoint

**Environment Configuration:**

```bash
PORT=8055
NATS_URL=nats://nats:4222
SUPABASE_URL=http://supabase:8000
DEFAULT_VOICE_PROVIDER=vibevoice
FLUTE_API_KEY=your-api-key
```

**API Endpoints:**

#### Prosody Analysis
```http
POST /v1/voice/analyze/prosodic
Content-Type: application/json

{
  "text": "Hello, how are you today?",
  "language": "en"
}

Response:
{
  "phrases": [
    {"text": "Hello,", "pause_ms": 200},
    {"text": "how are you", "pause_ms": 150},
    {"text": "today?", "pause_ms": 500}
  ],
  "total_duration_ms": 850
}
```

#### Text-to-Speech Synthesis
```http
POST /v1/voice/synthesize/prosodic
Content-Type: application/json

{
  "text": "Welcome to PMOVES.AI",
  "voice": "af_sky",
  "speed": 1.0,
  "output_format": "mp3"
}

Response: Audio file (application/octet-stream)
```

#### Session Management
```http
GET /v1/sessions
POST /v1/sessions
DELETE /v1/sessions/{session_id}
GET /v1/sessions/{session_id}/status
```

**Quick Start:**
```bash
# Start Flute-Gateway
docker compose --profile orchestration --profile media up -d flute-gateway

# Verify health
curl http://localhost:8055/healthz

# Synthesize speech
curl -X POST http://localhost:8055/v1/voice/synthesize/prosodic \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello PMOVES", "voice": "af_sky"}' \
  --output hello.mp3
```

---

### 2. Ultimate-TTS-Studio

**Location:** `/PMOVES-Ultimate-TTS-Studio/`

**Purpose:** Multi-engine TTS experimentation platform with Gradio interface supporting 7 different TTS engines.

**Port:**
- `7861` - Gradio web interface

**Supported Engines:**

| Engine | Description | GPU Required | Language Support |
|--------|-------------|--------------|------------------|
| **Kokoro** | High-quality neural TTS | Yes | English |
| **F5-TTS** | Emotional speech synthesis | Yes | Multilingual |
| **KittenTTS** | Fast lightweight TTS | Optional | English |
| **VoxCPM** | Chinese language support | Yes | Chinese |
| **VibeVoice** | Versatile voice synthesis | Yes | Multilingual |
| **IndexTTS** | Low-latency synthesis | Yes | English |
| **Higgs-Audio** | Experimental engine | Yes | English |

**Features:**
- **Voice Cloning**: Custom voice training
- **Batch Processing**: Multiple text synthesis
- **Audiobook Mode**: Long-form content optimization
- **Model Comparison**: Side-by-side engine comparison
- **GPU Acceleration**: CUDA 12.4 support

**Quick Start:**
```bash
# GPU required for most engines
docker compose --profile tts --profile gpu up -d ultimate-tts-studio

# Access Gradio interface
open http://localhost:7861
```

**Gradio Interface Tabs:**
1. **TTS Synthesis** - Single text synthesis
2. **Voice Cloning** - Train custom voices
3. **Batch Processing** - Process multiple texts
4. **Audiobook** - Long-form content
5. **Comparison** - Compare engines

---

### 3. Pipecat Integration

**Purpose:** Real-time conversational AI framework for voice agents with full-duplex communication.

**Features:**
- **Full-duplex audio**: Simultaneous input/output
- **Interruption handling**: Natural conversation flow
- **Multi-modal**: Text + audio + video
- **Transport flexibility**: WebSocket, WebRTC

**Integration Pattern:**

```python
# Example Pipecat pipeline with Flute-Gateway
from pipecat.pipeline import Pipeline
from pipecat.services.flute import FluteTTSService

pipeline = Pipeline([
    # Input processing
    AudioInputTransport(),

    # LLM processing
    LLMService("claude-sonnet-4-5"),

    # TTS output
    FluteTTSService(
        endpoint="http://flute-gateway:8055",
        voice="af_sky",
        prosodic=True
    ),

    # Output transport
    AudioOutputTransport()
])
```

---

## Integration Patterns

### Pattern 1: Simple TTS Request

```bash
curl -X POST http://localhost:8055/v1/voice/synthesize/prosodic \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog.",
    "voice": "af_sky",
    "speed": 1.0
  }' \
  --output speech.mp3
```

### Pattern 2: WebSocket Streaming

```javascript
const ws = new WebSocket('ws://localhost:8056');

ws.onopen = () => {
  // Send text for synthesis
  ws.send(JSON.stringify({
    action: 'synthesize',
    text: 'Hello PMOVES.AI',
    voice: 'af_sky'
  }));
};

ws.onmessage = (event) => {
  if (event.data instanceof Blob) {
    // Audio data received
    const audio = new Audio(URL.createObjectURL(event.data));
    audio.play();
  }
};
```

### Pattern 3: NATS Event Publishing

```python
import nats

nc = await nats.connect("nats://localhost:4222")

# Publish voice synthesis event
await nc.publish("voice.synthesize.request", json.dumps({
    "text": "Welcome to PMOVES",
    "voice": "af_sky",
    "callback_subject": "voice.synthesis.result"
}).encode())
```

---

## Voice Configuration

### Available Voices

| Voice | Language | Gender | Description |
|-------|----------|--------|-------------|
| `af_sky` | English | Female | Natural, clear |
| `af_bubble` | English | Female | Friendly, upbeat |
| `am_michael` | English | Male | Professional, calm |
| `bf_emma` | English | Female | Warm, expressive |
| `bm_george` | English | Male | Deep, authoritative |

### Prosody Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `speed` | 0.5 - 2.0 | 1.0 | Speech rate multiplier |
| `pitch` | -20 - +20 | 0 | Pitch shift in semitones |
| `energy` | 0.1 - 2.0 | 1.0 | Energy/amplitude multiplier |

---

## Architecture

### Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        pmoves_app                              │
│                                                                  │
│  ┌──────────────┐                                               │
│  │ Flute        │◀─────────────────────────────────┐            │
│  │ Gateway      │                                   │            │
│  │ 8055/8056    │                                   │            │
│  └──────┬───────┘                                   │            │
│         │                                           │            │
│         │ NATS                                      │            │
│         ▼                                           │            │
│  ┌──────────────┐                                   │            │
│  │   NATS       │◀──────────────────────────────────┘            │
│  │   Bus        │                                                │
│  │  (4222)      │                                                │
│  └──────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      pmoves_gpu (if available)                   │
│                                                                  │
│  ┌──────────────┐                                               │
│  │ Ultimate TTS │                                               │
│  │   Studio     │                                               │
│  │    7861      │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Service Communication

1. **Client → Flute-Gateway**: HTTP/WebSocket requests
2. **Flute-Gateway → Ultimate-TTS**: Engine fallback (optional)
3. **Flute-Gateway → NATS**: Event publishing
4. **NATS → Subscribers**: Voice event distribution

---

## Troubleshooting

### Common Issues

**No audio output:**
```bash
# Check service health
curl http://localhost:8055/healthz

# Verify TTS engine is running
docker logs pmoves-flute-gateway-1

# Check NATS connectivity
docker exec pmoves-flute-gateway-1 nc -zv nats 4222
```

**GPU not being used:**
```bash
# Check GPU availability
nvidia-smi

# Verify GPU device is passed to container
docker inspect pmoves-ultimate-tts-studio-1 | grep -i device
```

**WebSocket connection failures:**
```bash
# Test WebSocket endpoint
wscat -c ws://localhost:8056

# Check firewall rules
sudo ufw status | grep 8056
```

### Debug Commands

```bash
# View real-time logs
docker logs -f pmoves-flute-gateway-1

# Monitor NATS voice events
nats sub "voice.>" --raw

# Test synthesis directly
curl -X POST http://localhost:8055/v1/voice/synthesize/prosodic \
  -H "Content-Type: application/json" \
  -d '{"text": "Test", "voice": "af_sky"}' \
  -v
```

---

## Performance Considerations

### Resource Requirements

| Service | Memory | CPU | GPU |
|---------|--------|-----|-----|
| Flute-Gateway | 512M - 1G | 1 core | Optional |
| Ultimate-TTS | 4-8G | 2-4 cores | Recommended |
| Pipecat Pipeline | 1-2G | 1-2 cores | Optional |

### Optimization Tips

1. **Use streaming for long text**: WebSocket mode for audiobooks
2. **Cache common phrases**: Pre-generate frequently used responses
3. **Batch processing**: Queue multiple synthesis requests
4. **GPU offloading**: Use Ultimate-TTS with GPU for faster synthesis

---

## References

### Documentation
- `/.claude/context/flute-gateway.md` - Flute-Gateway API reference
- `/PMOVES-Ultimate-TTS-Studio/README.md` - Ultimate-TTS documentation

### External References
- [Pipecat Documentation](https://github.com/pipecat-ai/pipecat)
- [VibeVoice API](https://github.com/ffmikiewicz/vibe-voice)

### Related Services
- `docs/subsystems/SUBSYSTEM_INTEGRATION.md` - Full subsystem guide
- `docs/subsystems/CHIT_GEOMETRY_BUS.md` - Geometry bus integration

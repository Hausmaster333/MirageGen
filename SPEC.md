# Техническая спецификация локального видео-аватара

## Интерфейсы компонентов

### 1. ILLMProvider (Language Model Interface)

**Файл**: `src/avatar/interfaces/llm.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from avatar.schemas.llm_types import LLMResponse, Message

class ILLMProvider(ABC):
    """Абстрактный интерфейс для LLM провайдеров"""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> LLMResponse:
        """Генерация ответа (non-streaming)"""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> AsyncIterator[str]:
        """Потоковая генерация ответа по токенам"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Проверка доступности LLM"""
        pass
```

**Реализации**:
- `OllamaProvider`: Ollama (Mistral/Qwen)
- Future: OpenAI, Anthropic, LocalLlama

**Конфигурация**:
```yaml
llm:
  provider: ollama
  model: mistral:7b-instruct-q4_K_M
  base_url: http://localhost:11434
```

---

### 2. ITTSEngine (Text-to-Speech Interface)

**Файл**: `src/avatar/interfaces/tts.py`

```python
from abc import ABC, abstractmethod
from avatar.schemas.audio_types import AudioSegment

class ITTSEngine(ABC):
    """Абстрактный интерфейс для TTS движков"""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str = "ru",
        speaker_wav: str | None = None
    ) -> AudioSegment:
        """Синтез речи из текста"""
        pass

    @abstractmethod
    async def synthesize_streaming(
        self,
        text: str,
        language: str = "ru"
    ) -> AsyncIterator[AudioSegment]:
        """Потоковый синтез по предложениям"""
        pass

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """Список поддерживаемых языков"""
        pass
```

**Реализации**:
- `XTTSEngine`: XTTS-v2 (16 языков, включая русский)
- `SileroEngine`: Silero TTS (native русский)

**Конфигурация**:
```yaml
tts:
  engine: xtts
  language: ru
  speed: 1.0
  speaker_wav: null
```

---

### 3. ILipSyncGenerator (Lip-Sync Interface)

**Файл**: `src/avatar/interfaces/lipsync.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from avatar.schemas.animation_types import BlendshapeWeights

class ILipSyncGenerator(ABC):
    """Абстрактный интерфейс для lip-sync генераторов"""

    @abstractmethod
    async def generate_blendshapes(
        self,
        audio_path: Path,
        recognizer: str = "pocketSphinx"
    ) -> BlendshapeWeights:
        """Генерация blendshape весов из аудио"""
        pass

    @abstractmethod
    def get_phoneme_mapping(self) -> dict[str, str]:
        """Mapping Rhubarb phonemes → Three.js blendshapes"""
        pass
```

**Реализации**:
- `RhubarbGenerator`: Rhubarb Lip-Sync CLI wrapper

**Конфигурация**:
```yaml
lipsync:
  generator: rhubarb
  rhubarb_path: assets/rhubarb/rhubarb
  recognizer: pocketSphinx
```

---

### 4. IMotionGenerator (Motion/Gesture Interface)

**Файл**: `src/avatar/interfaces/motion.py`

```python
from abc import ABC, abstractmethod
from avatar.schemas.animation_types import MotionKeyframes

class IMotionGenerator(ABC):
    """Абстрактный интерфейс для motion генераторов"""

    @abstractmethod
    async def generate_motion(
        self,
        emotion: str,
        duration: float,
        action_hint: str | None = None
    ) -> MotionKeyframes:
        """Генерация motion анимации"""
        pass

    @abstractmethod
    def get_available_actions(self) -> list[str]:
        """Список доступных preset действий"""
        pass
```

**Реализации**:
- `PresetMotionGenerator`: Preset анимации + sentiment analysis
- Future: T2M-GPT, MotionDiffuse

**Конфигурация**:
```yaml
motion:
  generator: preset
  sentiment_model: blanchefort/rubert-base-cased-sentiment
  animations_dir: assets/animations
```

---

### 5. IPipeline (Orchestration Interface)

**Файл**: `src/avatar/interfaces/pipeline.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from avatar.schemas.api_types import AvatarFrame

class IPipeline(ABC):
    """Абстрактный интерфейс для orchestration пайплайна"""

    @abstractmethod
    async def process(
        self,
        user_input: str,
        conversation_history: list[Message] | None = None
    ) -> AsyncIterator[AvatarFrame]:
        """Полный пайплайн: text → LLM → TTS → lipsync → motion"""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, bool]:
        """Проверка всех компонентов пайплайна"""
        pass
```

**Реализации**:
- `AvatarPipeline`: Главный orchestrator

---

## Форматы данных (Pydantic Models)

### LLM Types (`schemas/llm_types.py`)

```python
from pydantic import BaseModel

class Message(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str

class LLMResponse(BaseModel):
    text: str
    action: str | None = None  # опциональное поле для прямой загрузки анимации
    tokens_count: int
    generation_time: float  # в секундах
```

---

### Audio Types (`schemas/audio_types.py`)

```python
from pydantic import BaseModel

class AudioSegment(BaseModel):
    audio_bytes: bytes
    sample_rate: int = 24000
    format: str = "wav"  # "wav" | "mp3"
    duration: float  # в секундах
```

---

### Animation Types (`schemas/animation_types.py`)

```python
from pydantic import BaseModel

class BlendshapeFrame(BaseModel):
    """Один фрейм blendshape анимации"""
    timestamp: float  # в секундах
    mouth_shapes: dict[str, float]  # {"A": 0.8, "B": 0.2, ...}
    # Rhubarb mouth shapes: A, B, C, D, E, F, G, H, X
    # Mapping в Three.js:
    # A → viseme_aa
    # B → viseme_PP
    # C → viseme_E
    # D → viseme_aa + tongue
    # E → viseme_O
    # F → viseme_FF
    # G → viseme_TH
    # H → viseme_DD
    # X → rest

class BlendshapeWeights(BaseModel):
    """Полная blendshape анимация"""
    frames: list[BlendshapeFrame]
    fps: int = 30
    duration: float

class MotionKeyframe(BaseModel):
    """Keyframe для skeleton анимации"""
    timestamp: float
    bone_rotations: dict[str, tuple[float, float, float, float]]  # quaternions
    bone_positions: dict[str, tuple[float, float, float]]  # world space

class MotionKeyframes(BaseModel):
    """Полная motion анимация"""
    keyframes: list[MotionKeyframe]
    emotion: str  # "happy", "sad", "neutral", "thinking"
    duration: float
```

---

### API Types (`schemas/api_types.py`)

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    conversation_history: list[Message] | None = None

class AvatarFrame(BaseModel):
    """Единый фрейм для отправки в Three.js"""
    timestamp: float
    text_chunk: str | None = None  # частичный текст (для streaming)
    audio_chunk: bytes | None = None
    blendshapes: dict[str, float] | None = None  # текущие веса
    motion: dict[str, tuple[float, float, float, float]] | None = None  # bone rotations

class ChatResponse(BaseModel):
    """Финальный ответ (non-streaming)"""
    full_text: str
    audio: AudioSegment
    blendshapes: BlendshapeWeights
    motion: MotionKeyframes
    processing_time: float
```

---

## API Endpoints

### POST /api/v1/chat

**Описание**: Полный пайплайн (non-streaming)

**Request**:
```json
{
  "message": "Привет, как дела?",
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Response**:
```json
{
  "full_text": "Привет! У меня всё отлично, спасибо!",
  "audio": {
    "audio_bytes": "<base64>",
    "sample_rate": 24000,
    "format": "wav",
    "duration": 2.5
  },
  "blendshapes": {
    "frames": [...],
    "fps": 30,
    "duration": 2.5
  },
  "motion": {
    "keyframes": [...],
    "emotion": "happy",
    "duration": 2.5
  },
  "processing_time": 3.2
}
```

---

### WebSocket /api/v1/stream

**Описание**: Потоковая отдача фреймов

**Client → Server**:
```json
{
  "type": "chat",
  "message": "Расскажи о себе"
}
```

**Server → Client** (множество сообщений):
```json
{
  "type": "frame",
  "timestamp": 0.033,
  "text_chunk": "Привет",
  "blendshapes": {"viseme_aa": 0.8, "viseme_PP": 0.2},
  "motion": {"spine": [0.0, 0.0, 0.0, 1.0]}
}
```

```json
{
  "type": "frame",
  "timestamp": 0.066,
  "audio_chunk": "<base64_chunk>",
  "blendshapes": {"viseme_E": 0.9},
  "motion": {"spine": [0.0, 0.1, 0.0, 0.99]}
}
```

```json
{
  "type": "done",
  "full_text": "Привет! Я виртуальный аватар...",
  "total_duration": 5.2
}
```

---

### GET /api/v1/health

**Описание**: Проверка здоровья всех компонентов

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "llm": true,
    "tts": true,
    "lipsync": true,
    "motion": true
  },
  "vram_usage": {
    "used_mb": 7500,
    "total_mb": 12288
  }
}
```

---

## Внешние зависимости

### Python Packages

| Package | Версия | Назначение |
|---------|--------|-----------|
| `ollama` | >=0.4.0 | LLM (Mistral/Qwen) |
| `TTS` | >=0.22.0 | XTTS-v2 TTS |
| `transformers` | >=4.46.0 | RuBERT sentiment |
| `torch` | >=2.5.0 | PyTorch backend |
| `fastapi` | >=0.115.0 | API framework |
| `websockets` | >=13.0 | WebSocket support |
| `pydantic` | >=2.10.0 | Data validation |
| `librosa` | >=0.10.0 | Audio processing |
| `loguru` | >=0.7.0 | Logging |

### Внешние инструменты

| Инструмент | Тип | Установка |
|------------|-----|-----------|
| **Ollama** | Server | `curl -fsSL https://ollama.com/install.sh \| sh` |
| **Mistral 7B** | Model | `ollama pull mistral:7b-instruct-q4_K_M` |
| **Rhubarb Lip-Sync** | Binary | [GitHub Releases](https://github.com/DanielSWolf/rhubarb-lip-sync/releases) |

### Модели HuggingFace

| Модель | Размер | Назначение |
|--------|--------|-----------|
| `coqui/XTTS-v2` | ~2GB | TTS (русский язык) |
| `blanchefort/rubert-base-cased-sentiment` | ~500MB | Sentiment analysis |

---

## Рабочий процесс (Workflow)

### Streaming Pipeline

```
1. User Input: "Расскажи о себе"
   ↓
2. LLM Stream:
   Token 1: "Привет" → TTS queue
   Token 2: ", я" → TTS queue
   Token 3: " виртуальный" → TTS queue
   ...
   ↓
3. TTS Process (по предложениям):
   Sentence 1: "Привет, я виртуальный аватар."
   → Audio chunk 1
   ↓
4. Rhubarb (параллельно):
   Audio chunk 1 → Blendshapes frames 1-75
   ↓
5. Sentiment Analysis:
   "Привет, я виртуальный аватар." → "neutral"
   → Load preset "idle.json"
   ↓
6. WebSocket Send:
   Frame 1: text="Привет", blendshapes={...}, motion={...}
   Frame 2: audio_chunk=<...>, blendshapes={...}
   Frame 3: ...
   ↓
7. Three.js Render:
   Apply blendshapes to morph targets
   Apply motion to skeleton
   Play audio
```

---

## Performance Benchmarks

### Целевые метрики (RTX 4070 Ti)

| Метрика | Target | Описание |
|---------|--------|----------|
| LLM Latency | <200ms | Первый токен |
| LLM Throughput | >30 tokens/s | Генерация |
| TTS Latency | <500ms | Первое предложение |
| Lipsync Processing | <1s | На 3 секунды аудио |
| Sentiment Analysis | <100ms | На одно предложение |
| Total Pipeline | <3s | От ввода до первого фрейма |

### Fallback стратегии

| Компонент | Fallback | Условие |
|-----------|----------|---------|
| LLM | Cached responses | Ollama недоступен |
| TTS | Silero | XTTS OOM |
| Lipsync | Silent animation | Rhubarb error |
| Motion | Idle animation | Sentiment error |

---

## Security & Validation

### Input Validation

- **Max message length**: 2000 символов
- **Rate limiting**: 10 requests/minute per IP
- **Sanitization**: Удаление HTML/JS инъекций

### Model Safety

- **VRAM monitoring**: Abort если >11GB использовано
- **Timeout protection**: Каждый компонент имеет timeout
- **Graceful shutdown**: Cleanup GPU memory при выходе

---

## Testing Strategy

### Unit Tests

- Каждый интерфейс имеет mock реализацию
- Тестирование Pydantic models валидации
- Audio processing утилиты

### Integration Tests

- Полный пайплайн с mock моделями
- API endpoints (httpx)
- WebSocket потоковая отдача

### Performance Tests

- Benchmark каждого компонента
- VRAM usage profiling
- Latency measurements

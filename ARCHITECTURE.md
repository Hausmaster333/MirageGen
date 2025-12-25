# Архитектура локального видео-аватара (PoC)

## Обзор системы

Система представляет собой модульное Python-приложение для создания интерактивного видео-аватара с диалоговыми возможностями на русском языке. Архитектура построена на принципах Strategy/Factory паттернов для обеспечения гибкой замены компонентов пайплайна.

## Структура проекта

```
hackathon-avatar-poc/
├── pyproject.toml
├── .env.example
├── README.md
├── ARCHITECTURE.md
├── SPEC.md
│
├── src/
│   └── avatar/
│       ├── __init__.py
│       ├── main.py                    # Entry point приложения
│       │
│       ├── interfaces/                # Абстрактные классы
│       │   ├── __init__.py
│       │   ├── llm.py                # ILLMProvider
│       │   ├── tts.py                # ITTSEngine
│       │   ├── lipsync.py            # ILipSyncGenerator
│       │   ├── motion.py             # IMotionGenerator
│       │   └── pipeline.py           # IPipeline
│       │
│       ├── llm/                      # LLM компоненты
│       │   ├── __init__.py
│       │   ├── ollama_provider.py    # Ollama реализация
│       │   └── prompt_templates.py   # Шаблоны промптов (ru)
│       │
│       ├── tts/                      # TTS движки
│       │   ├── __init__.py
│       │   ├── xtts_engine.py        # XTTS-v2 реализация
│       │   ├── silero_engine.py      # Silero альтернатива
│       │   └── audio_utils.py        # Утилиты для аудио
│       │
│       ├── lipsync/                  # Lip-sync генераторы
│       │   ├── __init__.py
│       │   ├── rhubarb_generator.py  # Rhubarb wrapper
│       │   └── blendshape_mapper.py  # Mapping в Three.js формат
│       │
│       ├── motion/                   # Gesture/motion системы
│       │   ├── __init__.py
│       │   ├── preset_loader.py      # Загрузка preset анимаций
│       │   ├── sentiment_analyzer.py # RuBERT sentiment
│       │   └── animation_mixer.py    # Mixing анимаций
│       │
│       ├── pipeline/                 # Orchestration
│       │   ├── __init__.py
│       │   ├── avatar_pipeline.py    # Главный orchestrator
│       │   └── streaming_manager.py  # Потоковая отдача
│       │
│       ├── api/                      # REST/WebSocket API
│       │   ├── __init__.py
│       │   ├── app.py                # FastAPI app
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── chat.py           # POST /chat endpoint
│       │   │   └── stream.py         # WS /stream endpoint
│       │   └── middleware.py         # CORS, logging
│       │
│       ├── config/                   # Конфигурация
│       │   ├── __init__.py
│       │   ├── settings.py           # Pydantic Settings
│       │   └── models_config.yaml    # Конфиг моделей
│       │
│       └── schemas/                  # Pydantic models
│           ├── __init__.py
│           ├── llm_types.py          # LLMResponse, Message
│           ├── audio_types.py        # AudioSegment
│           ├── animation_types.py    # BlendshapeWeights, MotionKeyframes
│           └── api_types.py          # Request/Response models
│
├── assets/                           # Статические ресурсы
│   ├── animations/                   # Preset анимации
│   │   ├── idle.json
│   │   ├── happy_gesture.json
│   │   ├── thinking_gesture.json
│   │   └── sad_gesture.json
│   └── rhubarb/
│       └── rhubarb                   # Rhubarb binary
│
├── tests/                            # Тесты
│   ├── __init__.py
│   ├── test_llm/
│   ├── test_tts/
│   ├── test_lipsync/
│   ├── test_motion/
│   ├── test_pipeline/
│   └── test_api/
│
└── frontend/                         # Three.js клиент (опционально)
    ├── index.html
    ├── avatar.js
    └── websocket_client.js
```

## Граф зависимостей компонентов

```
User Input (Text)
      ↓
[FastAPI /chat endpoint]
      ↓
[AvatarPipeline] ← [Config/Settings]
      ↓
      ├─→ [ILLMProvider] → OllamaProvider (Mistral/Qwen)
      │        ↓
      │   LLMResponse (text + optional action field)
      │        ↓
      ├─→ [ISentimentAnalyzer] → RuBERT Sentiment
      │        ↓
      │   Emotion label (happy/sad/neutral/thinking)
      │        ↓
      ├─→ [ITTSEngine] → XTTS-v2 / Silero
      │        ↓
      │   AudioSegment (wav/mp3 bytes)
      │        ↓
      ├─→ [ILipSyncGenerator] → RhubarbGenerator
      │        ↓
      │   BlendshapeWeights (JSON для Three.js)
      │        ↓
      ├─→ [IMotionGenerator] → PresetLoader + AnimationMixer
      │        ↓
      │   MotionKeyframes (skeleton animation)
      │        ↓
[StreamingManager]
      ↓
[WebSocket /stream] → Three.js Frontend
```

## Точки входа (Entry Points)

### 1. API Server (`src/avatar/main.py`)

```python
# Запуск FastAPI сервера
# uvicorn avatar.main:app --reload --port 8000
```

### 2. CLI Test Mode (`src/avatar/cli.py`)

```python
# Тестирование пайплайна без API
# python -m avatar.cli "Привет, как дела?"
```

## Паттерны проектирования

### Strategy Pattern

Каждый компонент реализует интерфейс, позволяя динамически заменять реализации:

```
ILLMProvider:
  - OllamaProvider (Mistral 7B)
  - OllamaProvider (Qwen)
  - Future: OpenAI, Anthropic

ITTSEngine:
  - XTTSEngine (XTTS-v2)
  - SileroEngine (Silero TTS)

ILipSyncGenerator:
  - RhubarbGenerator
  - Future: Wav2Lip, SadTalker

IMotionGenerator:
  - PresetMotionGenerator (preset + sentiment)
  - Future: T2M-GPT, MotionDiffuse
```

### Factory Pattern

```python
# config/models_config.yaml
llm:
  provider: "ollama"
  model: "mistral:7b-instruct-q4_K_M"

tts:
  engine: "xtts"  # или "silero"
  language: "ru"

# Создание через фабрику
llm = LLMFactory.create(config.llm)
tts = TTSFactory.create(config.tts)
```

### Observer Pattern

Streaming Manager использует observer для отправки фреймов через WebSocket:

```
Pipeline Event → Observer → WebSocket Broadcast
```

## Управление памятью (VRAM)

### Профиль памяти RTX 4070 Ti (12GB)

| Компонент | VRAM | Стратегия загрузки |
|-----------|------|-------------------|
| Ollama (Mistral 7B 4-bit) | ~5GB | Persistent (Ollama server) |
| XTTS-v2 | ~2GB | Lazy load при генерации |
| RuBERT Sentiment | ~500MB | Load on startup |
| Rhubarb | 0GB | CPU-only процесс |
| **Total Peak** | **~7.5GB** | **Buffer: 4.5GB** |

### Оптимизации

1. **Ollama auto-management**: Ollama автоматически выгружает неиспользуемые модели
2. **TTS lazy loading**: XTTS загружается только при первом TTS запросе
3. **Batch processing**: Sentiment анализ батчами для эффективности
4. **Streaming generation**: LLM генерирует текст по токенам, TTS по предложениям

## Конфигурация и замена компонентов

### Файл `config/models_config.yaml`

```yaml
llm:
  provider: ollama
  model: mistral:7b-instruct-q4_K_M  # или qwen:7b
  base_url: http://localhost:11434
  temperature: 0.7
  max_tokens: 512
  system_prompt_ru: "Ты дружелюбный помощник..."

tts:
  engine: xtts  # xtts | silero
  language: ru
  speaker_wav: null  # путь для voice cloning
  speed: 1.0

lipsync:
  generator: rhubarb
  rhubarb_path: assets/rhubarb/rhubarb
  recognizer: pocketSphinx  # pocketSphinx | phonetic

motion:
  generator: preset
  sentiment_model: blanchefort/rubert-base-cased-sentiment
  animations_dir: assets/animations
  fallback_action: idle

api:
  host: 0.0.0.0
  port: 8000
  cors_origins: ["http://localhost:3000"]
```

### Замена компонента через код

```python
from avatar.config import Settings
from avatar.llm import OllamaProvider
from avatar.pipeline import AvatarPipeline

settings = Settings()
settings.llm.model = "qwen:7b"  # Смена модели

pipeline = AvatarPipeline(settings)
```

## Расширяемость

### Добавление нового LLM провайдера

1. Создать `src/avatar/llm/new_provider.py`
2. Реализовать `ILLMProvider` интерфейс
3. Зарегистрировать в `LLMFactory`
4. Указать в `models_config.yaml`

### Добавление нового TTS движка

Аналогично LLM - реализовать `ITTSEngine` и зарегистрировать в фабрике.

## Безопасность и обработка ошибок

- **Rate limiting**: FastAPI Limiter для защиты endpoints
- **Input validation**: Pydantic models для всех входов
- **Graceful degradation**: Fallback на idle анимации при ошибках
- **Timeout handling**: Каждый компонент имеет timeout (30s LLM, 60s TTS)
- **VRAM monitoring**: Проверка доступности GPU перед загрузкой моделей

## Мониторинг и логирование

- **Loguru**: Структурированное логирование всех компонентов
- **Performance metrics**: Время выполнения каждого stage пайплайна
- **Error tracking**: Детальные stack traces при ошибках
- **VRAM usage**: Опциональный мониторинг через `pynvml`

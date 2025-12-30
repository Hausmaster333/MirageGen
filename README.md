# Hackathon Avatar PoC

Локальный видео-аватар с диалоговыми возможностями на русском языке.

## Quick Start

### 1. Установка зависимостей

```bash
# Установить uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# или
powershell -c "irm https://astral.sh/uv/install.ps1 | iex" # для Windows
# Установить Ollama
curl -fsSL https://ollama.com/install.sh | sh # Пока стоят заглушки для тестов, можно сразу писать uv sync без ollama
# или скачать с https://ollama.com/download/

# Скачать Mistral
ollama pull mistral:7b-instruct-q4_K_M # Также пока не надо для sync

# Установить Python зависимости
uv sync
```

### 2. Скачать Rhubarb

Это также пока не требуется для тестов

```bash

# Linux
wget https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.13.0/Rhubarb-Lip-Sync-1.13.0-Linux.zip
unzip Rhubarb-Lip-Sync-1.13.0-Linux.zip -d assets/rhubarb/
mv assets/rhubarb/Rhubarb-Lip-Sync-1.13.0-Linux/rhubarb assets/rhubarb
chmod +x assets/rhubarb/rhubarb
```

### 3. Запуск

```bash
# Запустить Ollama сервер
ollama serve # Пока можно без этого

# Запустить API
uv run avatar-server

# localhost:8000/docs для проверки
```

### 4. Тесты

```bash

# Запустить тесты
uv run pytest

# Мок тест llm
uv run pytest tests/test_llm/test_ollama_provider.py -v
# Интеграционный тест llm
uv run pytest tests/test_llm/test_ollama_integration.py -v -s -m integration

```

## Architecture

См. [ARCHITECTURE.md](ARCHITECTURE.md) и [SPEC.md](SPEC.md)

## Требования

- Python 3.11+
- RTX 4070 Ti (12GB VRAM) или аналог
- Ollama
- Linux/macOS (Windows с WSL2)

## Структура проекта

```
├── ARCHITECTURE.md          # Архитектура системы
├── SPEC.md                  # Техническая спецификация
├── pyproject.toml           # Конфигурация проекта
├── src/avatar/              # Основной код
├── assets/                  # Статические ресурсы
└── tests/                   # Тесты
```

---

## 🧪 Тестирование и разработка

### Pre-commit Hooks

```
uv tool install pre-commit --with pre-commit-uv --force-reinstall
uv tool run pre-commit install
```

### Форматирование кода

Проект использует **just** для автоматизации задач.

**Установка just:**

```
# macOS
brew install just

# Linux
cargo install just

# Windows
scoop install just
```

**Запуск форматирования:**

```
just format
```

**Запуск линтинга и автоисправлений (ruff):**

```
just lint
```

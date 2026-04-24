# 📡 Telegram Channel Intelligence Analyzer

Автоматический LangGraph пайплайн, который анализирует посты Telegram-каналов и выдаёт структурированный Excel-отчёт с классификацией тем, тональности и сводкой по каждому каналу.

## 🚀 Запуск (3 команды)

```bash
pip install -r requirements.txt
python main.py sample_posts.txt
```

API ключ уже зашит в `.env` — ничего настраивать не нужно.

## 🔧 Структура пайплайна

```
[Node 1: Ingest]    — читает посты из файла
        ↓
[Node 2: Classify]  ← LLM Call #1 (Gemini)
  PostAnalysis: topic, sentiment, emotion, is_breaking, keywords
        ↓
[Node 3: Report]    ← LLM Call #2 (Gemini)  
  ChannelReport: top_topic, overall_mood, mood_score, summary, key_themes
        ↓
[Node 4: Export]    — Excel файл с 3 листами
```

## 📊 Выходной файл

`tg_report_YYYYMMDD_HHMMSS.xlsx` — 3 листа:
- **Channel Summary** — сводка по каждому каналу
- **Post Details** — анализ каждого поста
- **Statistics** — распределение тем, настроений, эмоций

## 📁 Структура проекта

```
├── main.py          # Точка входа
├── graph.py         # LangGraph пайплайн (4 ноды)
├── models.py        # Pydantic модели
├── prompts.py       # Все промпты
├── llm_functions.py # LLM вызовы к Gemini
├── ingest.py        # Node 1: загрузка постов
├── export.py        # Node 4: Excel экспорт
├── sample_posts.txt # Тестовые данные (3 канала)
├── requirements.txt
└── .env             # API ключ
```

## 📥 Форматы входных данных

**Текстовый файл** (sample_posts.txt):
```
=== @channelname ===
Текст поста...
---
Ещё один пост...
---
```

**Экспорт Telegram Desktop**: передай путь к папке или к `result.json` / `result.html`.

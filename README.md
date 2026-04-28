<div align="center">

#AIAT 

**Персональный AI-ассистент с голосом, чатом с нейросетями и полной кастомизацией интерфейса**

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![KivyMD](https://img.shields.io/badge/KivyMD-1.2.0-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-lightblue?style=for-the-badge&logo=windows)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

<img src="screenshots/aiatbkraund.png" width="700"/>

> Десктопное приложение на Python + KivyMD с поддержкой локальных и облачных нейросетей,
> голосовым синтезом Silero TTS, анимированным интерфейсом и гибкой кастомизацией под себя.

## 📦 [⬇️ Скачать готовую сборку (Google Drive)](https://drive.google.com/drive/folders/1w_LOTrAqGxb6zgnJaJUOVQ19LWW_pBOF?usp=sharing)

> Просто скачай, распакуй и запускай `AIAT.exe` — ничего устанавливать не нужно

</div>

---

## 📸 Скриншоты

<div align="center">

<img src="screenshots/launch.gif" width="600"/>

*Демонстрация запуска приложения*

<br/>

<img src="screenshots/aiatbkraund.png" width="600"/>

*Главный экран приложения*

<br/>

<img src="screenshots/aiatavater.png" width="300"/>

*Логотип AIAT*

</div>

---

## ✨ Функционал

### 🧠 Нейросети — локальные и облачные

AIAT объединяет лучшие мировые ИИ в одном окне.

**Локальные модели (работают без интернета):**
- **Llama 3** (latest / 8B / 70B) — через Ollama
- **Qwen3 8B** — через Ollama
- **SambaLingo Russian Chat** (3.2GB) — русскоязычная GGUF модель, работает полностью офлайн через `ctransformers`
- **Gamma** — локальная модель через собственный модуль

**Облачные модели (через API ключ):**
- ChatGPT (OpenAI GPT-3.5 / GPT-4)
- Claude (Anthropic claude-3-5-haiku)
- Gemini 2.0 Flash (Google)
- DeepSeek
- Grok 3 (xAI)
- Mistral Small

Все модели отображаются карточками с индикатором статуса и кнопками «Подключить» / «Выбрать». Переключение активной модели прямо из окна чата — на лету.

---

### 🔊 TTS — голосовой синтез Silero

- Используется **Silero TTS v4** (`v4_ru.pt`) — высококачественный русский голос офлайн
- **Двойной движок** — автоматический выбор между Silero (приоритет) и pyttsx3 (fallback)
- Загрузка в **фоновом потоке** — не блокирует интерфейс при старте
- Автоматический поиск `v4_ru.pt` в 4 местах (рядом с exe, в папке проекта, в текущей директории)
- Если файл не найден — загружается через интернет как резервный вариант
- Регулировка **громкости** прямо в главном экране кнопками + и −
- Кнопка **«Тест TTS»** — проверить голос одним нажатием
- Выбор устройства вывода звука в настройках аудио

---

### 🎨 Полная кастомизация интерфейса

**4 цветовые темы кнопок:**

| Тема | Описание |
|------|----------|
| `teal` | Бирюзово-тёмная (по умолчанию) |
| `beige` | Тёплая бежевая |
| `black` | Чёрная минималистичная |
| `white` | Светлая с синим акцентом |

**Кастомизация профиля:**
- Имя пользователя (никнейм)
- Аватарка — загрузить любое изображение, автоматический ресайз до 400×400
- Баннер профиля — загрузить любое изображение, автоматический ресайз до 970×500
- Заметки / информация о себе

**Фон:**
- Загрузить своё фоновое изображение для чата
- Отдельный фон для основного интерфейса

---

### 💬 Чат с нейросетью

- Полноценный чат-интерфейс с прокруткой истории сообщений
- Ответы ИИ автоматически озвучиваются через Silero TTS
- Переключение между подключёнными моделями на лету
- Поддержка контекста разговора
- Ограничение истории до 20 сообщений — защита от утечки памяти

---

### ⚙️ Дополнительные возможности

- **Анимированный сплэш-экран** при запуске (GIF с автоматическим исправлением прозрачности)
- **Автоматический ярлык** на рабочем столе и в меню Пуск при первом запуске EXE
- **settings.json** — все настройки сохраняются рядом с EXE
- Многопоточность — загрузка моделей и TTS не блокируют UI
- Минимальный размер окна 700×700, стандартный 900×900

---

## 🧑‍💻 История разработки — как я работал над кодом

Проект прошёл долгий путь рефакторинга, оптимизации и исправления багов. Вот ключевые этапы:

### 🔧 Борьба с путями и упаковкой (PyInstaller)

**Проблема:** При упаковке в EXE приложение теряло доступ к ресурсам — гифки, иконки, модели ИИ не находились.

**Решение:** Внедрил функцию `resource_path()` и глобальную переменную `BASE_DIR`, которые корректно определяют запущен ли скрипт как `.py` или как `.exe` и находят файлы в правильных местах.

**Дополнительный баг:** `ctransformers` требовал передавать **папку + имя файла отдельно** через `model_file=`, а не полный путь — из-за этого SambaLingo вообще не загружалась. Исправил логику загрузки:
```python
model_dir = os.path.dirname(model_path)
model_file = os.path.basename(model_path)
llm = AutoModelForCausalLM.from_pretrained(model_dir, model_file=model_file, ...)
```

---

### ⚡ Оптимизация загрузки и многопоточность

**Проблема:** Приложение запускалось 10-15 секунд, главное окно появлялось с большой задержкой.

**Решение:**
- Создал анимированный сплэш-экран который запускается мгновенно
- Все тяжёлые операции (загрузка Silero TTS, проверка Ollama, сканирование аудиоустройств) вынесены в фоновые потоки через `threading.Thread(daemon=True)`
- Синхронизировал загрузку настроек и UI с помощью `Clock.schedule_once`

---

### 🐛 Исправление критических багов

**Баг с настройками (JsonStore):**
`JsonStore('../settings.json')` — при запуске EXE создавал файл настроек в непредсказуемом месте, настройки не сохранялись между сессиями.
```python
# Было (сломано):
self.store = JsonStore('../settings.json')
# Стало (правильно):
self.store = JsonStore(os.path.join(BASE_DIR, 'settings.json'))
```

**Баг с кодировкой Windows (UnicodeEncodeError):**
Эмодзи в `print()` вызывали `UnicodeEncodeError: 'charmap' codec can't encode character` и крашили приложение на строке 146 — до того как вообще загружался интерфейс. Добавил фикс в самом начале файла:
```python
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

**Баг с Silero TTS:**
Функция `load_silero_model()` была определена но нигде не вызывалась при старте — приложение молча падало на pyttsx3. Исправил — добавил вызов в `__init__`:
```python
threading.Thread(target=load_silero_model, daemon=True).start()
```

**Баг с цветовыми темами (чёрные кнопки):**
После смены цветовой схемы часть кнопок становилась чёрной, текст не читался. Разработал словарь `BUTTON_COLORS` с разделением на `primary`, `accent`, `text`, `card_bg`. Написал функцию `update_ui_colors()` которая рекурсивно обходит все виджеты и принудительно обновляет цвета — смена темы без перезапуска.

**Баг "гонка потоков" в чате:**
Если быстро нажать «Отправить» два раза — ответы от ИИ смешивались. Исправил через `threading.Lock` в методе `_ai_request_thread`.

---

### 🗑️ Оптимизация упаковки EXE

- Убран **UPX** из PyInstaller — он ломает бинарники torch/ctransformers
- Настроен правильный сбор всех `.dll` и `.pyd` файлов ctransformers через glob
- Исправлен `AIAT.spec` — добавлен явный сбор подмодулей ctransformers
- `build.bat` автоматически копирует `ctransformers` из `site-packages` в `_internal`

---

## 📁 Структура проекта

```
AIAT/
├── AIAT.py                  # Основной файл (~3900 строк)
├── AIAT.spec                # Конфиг PyInstaller
├── build.bat                # Скрипт автоматической сборки EXE
├── v4_ru.pt                 # Модель Silero TTS (скачать отдельно, 39MB)
├── assets/
│   └── inko1.ico            # Иконка приложения
├── avatar/
│   └── avatar.png           # Аватарка по умолчанию
├── backgrounds/
│   └── BackgroundAT.jpg     # Фон чата
├── banner/
│   └── banner.png           # Баннер профиля
├── model/
│   └── SambaLingo-Russian-Chat.Q3_K_M.gguf  # (скачать отдельно, 3.2GB)
├── screenshots/
│   ├── aiatbkraund.png      # Скриншот главного экрана
│   └── aiatavater.png       # Логотип
└── screensaver/
    └── 03191.gif            # Анимация загрузки
```

---

## 🚀 Установка и запуск

### ⬇️ Вариант 1 — Готовый EXE (рекомендуется)

**[📦 Скачать с Google Drive](https://drive.google.com/drive/folders/1w_LOTrAqGxb6zgnJaJUOVQ19LWW_pBOF?usp=sharing)**

1. Скачай архив по ссылке выше
2. Распакуй — не меняй структуру папок
3. Скачай `v4_ru.pt` и положи рядом с `AIAT.exe`
4. Скачай `SambaLingo-Russian-Chat.Q3_K_M.gguf` и положи в папку `model/`
5. Запускай `AIAT.exe`

---

### 🐍 Вариант 2 — Запуск из исходников

**Требования:** Python 3.12, Windows 10/11

```bash
pip install kivymd==1.2.0 kivy==2.3.1
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install ctransformers sounddevice soundfile pillow requests pyttsx3 numpy pywin32
python AIAT.py
```

---

### 🔨 Вариант 3 — Собрать EXE самостоятельно

```bash
pip install pyinstaller
build.bat
```

Готовый EXE появится в `dist\AIAT\AIAT.exe`

---

## 📥 Скачать модели (не входят в репозиторий)

### Silero TTS — `v4_ru.pt` (39 MB)
```
https://models.silero.ai/models/tts/ru/v4_ru.pt
```
Положить рядом с `AIAT.exe`

### SambaLingo Russian Chat — 3.2 GB
```bash
pip install huggingface-hub
huggingface-cli download bartowski/SambaLingo-Russian-Chat-GGUF SambaLingo-Russian-Chat.Q3_K_M.gguf --local-dir ./model
```

---

## 🔧 Настройки

| Раздел | Что можно настроить |
|--------|-------------------|
| **Мой профиль** | Имя, аватарка, баннер, заметки |
| **Настройки фона** | Фоновое изображение чата и интерфейса |
| **Цвета кнопок** | Тема: teal / beige / black / white |
| **Настройки аудио** | Устройство вывода, громкость TTS |
| **Нейросети** | Подключение моделей, API ключи |
| **Чат** | История сообщений, активная модель |

---

## 📦 Зависимости

| Библиотека | Назначение |
|-----------|-----------|
| KivyMD 1.2.0 | UI фреймворк Material Design |
| Kivy 2.3.1 | Основа KivyMD |
| PyTorch (CPU) | Silero TTS |
| ctransformers | GGUF модели офлайн |
| sounddevice | Воспроизведение аудио |
| soundfile | Чтение аудио файлов |
| Pillow | Работа с изображениями и GIF |
| pyttsx3 | Fallback TTS Windows |
| requests | API запросы к облачным моделям |
| pywin32 | Создание ярлыков Windows |


<div align="center">

<img src="screenshots/aiatavater.png" width="200"/>

Сделано с ❤️ на Python + KivyMD

[![YouTube](https://img.shields.io/badge/YouTube-Канал-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/@python-v7)

**[⬇️ Скачать AIAT](https://drive.google.com/drive/folders/1w_LOTrAqGxb6zgnJaJUOVQ19LWW_pBOF?usp=sharing)**

</div>

# -*- coding: utf-8 -*-
import sys
import io
# Фикс кодировки для Windows консоли (cp1251 не поддерживает эмодзи)
if sys.stdout is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr is not None:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.slider import MDSlider
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineListItem, TwoLineListItem
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.image import Image, AsyncImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.storage.jsonstore import JsonStore
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ListProperty, ObjectProperty, \
    OptionProperty
from kivy.core.window import Window
from kivy.config import Config
from PIL import Image as PILImage
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import shutil
import sys
import json
import requests
from datetime import datetime
import threading
import subprocess
import importlib.util
import queue
import tempfile
import pyttsx3
# Silero TTS
import torch
import os
import sys
import multiprocessing

def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсам, работает для dev и для PyInstaller """
    try:
        # PyInstaller создает временную папку _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# BASE_DIR — всегда папка рядом с exe или рядом с .py скриптом
# НЕ _internal, а именно папка AIAT/
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Функция для получения пути к ресурсам
def get_res(relative_path):
    return os.path.join(BASE_DIR, relative_path)


SILERO_AVAILABLE = False
silero_model = None


def load_silero_model():
    global SILERO_AVAILABLE, silero_model
    try:
        import torch

        # Ищем v4_ru.pt в нескольких местах по приоритету
        search_paths = [
            os.path.join(BASE_DIR, "v4_ru.pt"),                         # рядом с exe/скриптом
            resource_path("v4_ru.pt"),                                   # внутри _MEIPASS (если упакован)
            os.path.join(os.path.dirname(sys.executable), "v4_ru.pt"),  # папка exe
            os.path.join(os.getcwd(), "v4_ru.pt"),                      # текущая рабочая папка
        ]
        # Убираем дубли
        seen = set()
        unique_paths = []
        for p in search_paths:
            if p not in seen:
                seen.add(p)
                unique_paths.append(p)

        model_path = None
        for p in unique_paths:
            print(f" Ищу Silero модель: {p}")
            if os.path.exists(p):
                model_path = p
                break

        if model_path:
            silero_model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
            silero_model.to(torch.device('cpu'))
            SILERO_AVAILABLE = True
            print(f" Silero TTS загружена из: {model_path}")
        else:
            # Резервный вариант через интернет
            print(" v4_ru.pt не найден нигде. Загружаю через torch.hub...")
            model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                      model='silero_tts', language='ru', speaker='v4_ru')
            model.to(torch.device('cpu'))
            silero_model = model
            SILERO_AVAILABLE = True
            print(" Silero TTS загружена через интернет")

    except Exception as e:
        SILERO_AVAILABLE = False
        print(f" Ошибка при загрузке Silero: {e}")
def apply_dark_titlebar():
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, "AIAT")
        if not hwnd:
            hwnd = ctypes.windll.user32.FindWindowW("SDL_app", None)
        if not hwnd:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return
        dark = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark), ctypes.sizeof(dark))
        dark_color = ctypes.c_int(0x00141414)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(dark_color), ctypes.sizeof(dark_color))
        white = ctypes.c_int(0x00FFFFFF)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(white), ctypes.sizeof(white))
        print(" Тёмный title bar применён")
    except Exception as e:
        print(f" Title bar: {e}")


# Импортируем ctransformers для локальной модели
try:
    from ctransformers import AutoModelForCausalLM

    CTRANFORMERS_AVAILABLE = True
    print(" ctransformers доступна")
except ImportError:
    CTRANFORMERS_AVAILABLE = False
import os

# Все пути уже определены выше через BASE_DIR

# 1. Путь к аватаркам (теперь внутри папки profiles)
PROFILE_AVATARS_PATH = os.path.join(BASE_DIR, 'avatar')

# 2. Путь к именам/настройкам профиля
PROFILE_NAMES_PATH = os.path.join(BASE_DIR, 'profiles_name')

# 3. Путь к баннерам (проверь, чтобы папка называлась banners с 's')
PROFILE_BANNERS_PATH = os.path.join(BASE_DIR, 'banner')

# 4. Путь к фоновым изображениям чата
BACKGROUNDS_FOLDER = os.path.join(BASE_DIR, 'backgrounds')

# 5. Путь к текстовой информации
PROFILE_NOTES_PATH = os.path.join(BASE_DIR, 'info')

# 6. Путь к модели нейросети
SAMBALINGO_MODEL_PATH = os.path.join(BASE_DIR, 'model', 'SambaLingo-Russian-Chat.Q3_K_M.gguf')

# 7. Путь к иконке
ICON_PATH = os.path.join(BASE_DIR, 'assets', 'inko1.ico')
#8. путь к png иконки
ICON_PATH_PNG = os.path.join(BASE_DIR, 'assets', 'inko2_256x256.png')
# Создаем папки, если их вдруг нет (чтобы не было ошибок)
for path in [PROFILE_AVATARS_PATH, PROFILE_BANNERS_PATH, BACKGROUNDS_FOLDER, PROFILE_NOTES_PATH]:
    os.makedirs(path, exist_ok=True)


def fix_gif_transparency(input_path):
    try:
        fixed_path = input_path.replace('.gif', '_fixed.gif')
        if os.path.exists(fixed_path):
            return fixed_path
        from PIL import Image as PILImage
        frames = []
        gif = PILImage.open(input_path)
        try:
            while True:
                frame = gif.copy().convert('RGBA')
                bg = PILImage.new('RGBA', frame.size, (0, 0, 0, 255))
                bg.paste(frame, mask=frame.split()[3])
                frames.append(bg.convert('RGB'))
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass
        frames[0].save(
            fixed_path,
            save_all=True,
            append_images=frames[1:],
            loop=0,
            duration=gif.info.get('duration', 100)
        )
        print(f"GIF исправлен: {fixed_path}")
        return fixed_path
    except Exception as e:
        print(f" Не удалось исправить GIF: {e}")
        return input_path


# Заставка к приложению (путь + фикс)
from PIL import Image as PILImage

input_path = os.path.join(BASE_DIR, 'screensaver', '03191.gif')
fixed_path = os.path.join(BASE_DIR, 'screensaver', '03191_fixed.gif')

gif = PILImage.open(input_path)
frames = []
durations = []

try:
    while True:
        duration = gif.info.get('duration', 100)
        durations.append(duration)
        # Конвертируем без прозрачности - просто RGB
        frame = PILImage.new('RGB', gif.size, (0, 0, 0))
        frame.paste(gif.convert('RGBA'), mask=None)
        frames.append(frame)
        gif.seek(gif.tell() + 1)
except EOFError:
    pass

frames[0].save(
    fixed_path,
    save_all=True,
    append_images=frames[1:],
    loop=0,
    duration=durations
)
print(f"Готово! Кадров: {len(frames)}")

# Устанавливаем иконку для окна
Config.set('kivy', 'window_icon', ICON_PATH)
Config.set('kivy', 'window_title', 'AIAT')


# Функция для создания ярлыка приложения
def create_application_shortcut():
    """Создает ярлык приложения на рабочем столе"""
    try:
        import win32com.client

        # Определяем путь к текущему исполняемому файлу
        if getattr(sys, 'frozen', False):
            # Если запущено как exe
            exe_path = sys.executable
        else:
            # Если запущено как скрипт
            exe_path = os.path.abspath(sys.argv[0])

        # Путь к рабочему столу
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")

        # Название ярлыка
        shortcut_name = "AI Chat App.lnk"
        shortcut_path = os.path.join(desktop, shortcut_name)

        # Создаем ярлык только если его еще нет
        if not os.path.exists(shortcut_path):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.IconLocation = ICON_PATH
            shortcut.Description = "AI Chat Application"
            shortcut.Save()
            print(f" Ярлык создан на рабочем столе: {shortcut_path}")

            # Также создаем в меню Пуск
            start_menu = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows",
                                      "Start Menu", "Programs")
            start_menu_path = os.path.join(start_menu, shortcut_name)

            if not os.path.exists(start_menu_path):
                shortcut = shell.CreateShortCut(start_menu_path)
                shortcut.TargetPath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = ICON_PATH
                shortcut.Description = "AI Chat Application"
                shortcut.Save()
                print(f" Ярлык создан в меню Пуск: {start_menu_path}")

            return True
        else:
            print("Ярлык уже существует")
            return False

    except ImportError:
        print(" Библиотека pywin32 не установлена. Ярлык не будет создан.")
        print("  Установите: pip install pywin32")
        return False
    except Exception as e:
        print(f" Ошибка при создании ярлыка: {e}")
        return False


# Создаем ярлык при запуске (только если это exe и ярлыка еще нет)
if getattr(sys, 'frozen', False):
    # Запускаем создание ярлыка в отдельном потоке, чтобы не задерживать запуск
    threading.Thread(target=create_application_shortcut, daemon=True).start()

# Устанавливаем размер окна как квадрат
Window.size = (900, 900)
Window.minimum_width = 700
Window.minimum_height = 700

# Заставка к приложению (путь + фикс)
SCREENSAVER_PATH = os.path.join(BASE_DIR, 'screensaver', '03191_fixed.gif')

# Цветовые схемы для кнопок
BUTTON_COLORS = {
    'teal': {
        'primary': [0.2, 0.6, 0.6, 1],
        'accent': [1, 0.8, 0.2, 1],
        'text': [1, 1, 1, 1],
        'card_bg': [0.2, 0.2, 0.2, 0.3],
        'success': [0.2, 0.8, 0.2, 1],
        'error': [0.8, 0.2, 0.2, 1],
        'warning': [1, 0.8, 0.2, 1]
    },
    'beige': {
        'primary': [0.96, 0.96, 0.86, 1],
        'accent': [0.8, 0.6, 0.4, 1],
        'text': [0.2, 0.2, 0.2, 1],
        'card_bg': [0.96, 0.96, 0.86, 0.3],
        'success': [0.2, 0.8, 0.2, 1],
        'error': [0.8, 0.2, 0.2, 1],
        'warning': [1, 0.8, 0.2, 1]
    },
    'black': {
        'primary': [0.1, 0.1, 0.1, 1],
        'accent': [0.5, 0.5, 0.5, 1],
        'text': [1, 1, 1, 1],
        'card_bg': [0.1, 0.1, 0.1, 0.3],
        'success': [0.2, 0.8, 0.2, 1],
        'error': [0.8, 0.2, 0.2, 1],
        'warning': [1, 0.8, 0.2, 1]
    },
    'white': {
        'primary': [0.95, 0.95, 0.95, 1],
        'accent': [0.3, 0.6, 0.9, 1],
        'text': [0.1, 0.1, 0.1, 1],
        'card_bg': [0.95, 0.95, 0.95, 0.3],
        'success': [0.2, 0.8, 0.2, 1],
        'error': [0.8, 0.2, 0.2, 1],
        'warning': [1, 0.8, 0.2, 1]
    }
}  # ← вот эту добавить

# Модели нейронных сетей
NEURAL_MODELS = {
    'local': {
        'llama3:latest': {
            'name': 'Llama 3 (Latest)',
            'type': 'local',
            'api_url': 'http://localhost:11434/api/generate',
            'model_name': 'llama3:latest',
            'status': 'disconnected',
            'icon': 'llama',
            'description': 'Meta Llama 3 последняя версия'
        },
        'llama3:8b': {
            'name': 'Llama 3 8B',
            'type': 'local',
            'api_url': 'http://localhost:11434/api/generate',
            'model_name': 'llama3:8b',
            'status': 'disconnected',
            'icon': 'llama',
            'description': 'Meta Llama 3 8B параметров'
        },
        'llama3:70b': {
            'name': 'Llama 3 70B',
            'type': 'local',
            'api_url': 'http://localhost:11434/api/generate',
            'model_name': 'llama3:70b',
            'status': 'disconnected',
            'icon': 'llama',
            'description': 'Meta Llama 3 70B параметров'
        },
        'gamma': {
            'name': 'Gamma',
            'type': 'local',
            'module': 'gamma_model',
            'class': 'GammaModel',
            'status': 'disconnected',
            'icon': 'brain',
            'description': 'Локальная модель Gamma'
        },
        'qwen3:8b': {
            'name': 'Qwen3 8B',
            'type': 'local',
            'api_url': 'http://localhost:11434/api/generate',
            'model_name': 'qwen3:8b',
            'status': 'disconnected',
            'icon': 'brain',
            'description': 'Qwen3 8B параметров'
        },
        'sambalingo': {
            'name': 'SambaLingo Russian Chat',
            'type': 'local',
            'model_path': SAMBALINGO_MODEL_PATH,
            'status': 'disconnected',
            'icon': 'account-voice',
            'description': 'Русскоязычная модель SambaLingo 3.2GB',
            'model_type': 'llama',
            'using_ctransformers': True,
            'auto_load': True
        }
    },
    'cloud': {
        'deepseek': {
            'name': 'DeepSeek',
            'type': 'cloud',
            'api_url': 'https://api.deepseek.com/v1/chat/completions',
            'model_name': 'deepseek-chat',
            'api_key': '',
            'status': 'disconnected',
            'icon': 'cloud',
            'description': 'DeepSeek AI модель'
        },
        'chatgpt': {
            'name': 'ChatGPT',
            'type': 'cloud',
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'model_name': 'gpt-3.5-turbo',
            'api_key': '',
            'status': 'disconnected',
            'icon': 'openai',
            'description': 'OpenAI GPT модель'
        },
        'grok': {
            'name': 'Grok',
            'type': 'cloud',
            'api_url': 'https://api.x.ai/v1/chat/completions',
            'model_name': 'grok-3',
            'api_key': '',
            'status': 'disconnected',
            'icon': 'twitter',
            'description': 'xAI Grok модель'
        },
        'claude': {
            'name': 'Claude',
            'type': 'cloud',
            'api_url': 'https://api.anthropic.com/v1/messages',
            'model_name': 'claude-3-5-haiku-20241022',
            'api_key': '',
            'status': 'disconnected',
            'icon': 'alpha-c-circle',
            'description': 'Anthropic Claude модель'
        },
        'gemini': {
            'name': 'Gemini',
            'type': 'cloud',
            'api_url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
            'model_name': 'gemini-2.0-flash',
            'api_key': '',
            'status': 'disconnected',
            'icon': 'google',
            'description': 'Google Gemini модель'
        },
        'mistral': {
            'name': 'Mistral',
            'type': 'cloud',
            'api_url': 'https://api.mistral.ai/v1/chat/completions',
            'model_name': 'mistral-small-latest',
            'api_key': '',
            'status': 'disconnected',
            'icon': 'weather-windy',
            'description': 'Mistral AI модель'
        }
    }
}

KV = '''
<CustomCard@MDCard>:
    orientation: 'vertical'
    padding: "20dp"
    spacing: "20dp"
    size_hint_y: None
    height: self.minimum_height
    md_bg_color: app.current_colors['card_bg']
    radius: [15,]
    elevation: 2
    margin: "10dp"

<ModelCard@MDCard>:
    orientation: 'vertical'
    padding: "15dp"
    spacing: "10dp"
    size_hint_y: None
    height: self.minimum_height
    md_bg_color: app.current_colors['card_bg']
    radius: [10,]
    elevation: 1

    MDBoxLayout:
        orientation: 'horizontal'
        spacing: "10dp"
        size_hint_y: None
        height: "40dp"

        MDIconButton:
            icon: root.model_data.get('icon', 'brain')
            theme_icon_color: "Custom"
            icon_color: app.current_colors['success'] if root.model_data.get('status') == 'connected' else app.current_colors['error'] if root.model_data.get('status') == 'disconnected' else app.current_colors['warning']
            size_hint_x: 0.15

        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.5

            MDLabel:
                text: root.model_data.get('name', '')
                font_style: "Subtitle1"
                bold: True
                theme_text_color: "Primary"
                size_hint_y: None
                height: self.texture_size[1]

            MDLabel:
                text: root.model_data.get('description', '')
                font_style: "Caption"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: self.texture_size[1]

        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.35
            spacing: "5dp"

            MDLabel:
                text: "Подключено" if root.model_data.get('status') == 'connected' else "Отключено" if root.model_data.get('status') == 'disconnected' else "Подключение..."
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: app.current_colors['success'] if root.model_data.get('status') == 'connected' else app.current_colors['error'] if root.model_data.get('status') == 'disconnected' else app.current_colors['warning']
                halign: 'right'
                size_hint_y: None
                height: "20dp"

            MDRaisedButton:
                text: "Выбрать" if root.model_data.get('status') == 'connected' else "Подключить"
                on_release: app.connect_neural_model(root.model_id) if root.model_data.get('status') != 'connected' else app.select_neural_model(root.model_id)
                size_hint_x: 1
                md_bg_color: app.current_colors['success'] if root.model_data.get('status') == 'connected' else app.current_colors['primary']
                text_color: app.current_colors['text']
                height: "30dp"
                disabled: root.model_data.get('status') == 'connecting'

<SplashScreen>:
    name: 'splash'

    FloatLayout:
        canvas.before:
            Color:
                rgba: 0, 0, 0, 1
            Rectangle:
                size: self.size
                pos: self.pos

        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}
            spacing: "20dp"
            padding: "20dp"

            MDLabel:
                text: "AIAT"
                font_style: "H2"
                halign: 'center'
                bold: True
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                size_hint_y: None
                height: "80dp"

            AsyncImage:
                id: screensaver
                source: 'screensaver/03191_fixed.gif'
                size_hint: None, None
                size: "350dp", "350dp"
                pos_hint: {'center_x': 0.5}
                nocache: True
                anim_loop: 0
                allow_stretch: True
                keep_ratio: False

            MDLabel:
                id: loading_text
                text: "Загрузка..."
                font_style: "H6"
                halign: 'center'
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 0.7
                size_hint_y: None
                height: "40dp"

            MDProgressBar:
                id: progress_bar
                value: 0
                max: 100
                size_hint_x: 0.8
                pos_hint: {'center_x': 0.5}
                color: 1, 1, 1, 1
                back_color: 0.3, 0.3, 0.3, 0.5

<MainScreen>:
    name: 'main'

    FloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            spacing: "10dp"
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}

            MDTopAppBar:
                title: "AIAT"
                elevation: 4
                md_bg_color: app.current_colors['primary']
                specific_text_color: app.current_colors['text']
                left_action_items: [['account', lambda x: app.set_screen('profile_view')], ['image', lambda x: app.set_screen('background')]]
                right_action_items: [['dots-vertical', lambda x: app.open_menu(x)]]

            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: "20dp"
                    padding: "20dp"
                    adaptive_height: True

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Мой профиль"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'horizontal'
                            spacing: "20dp"
                            adaptive_height: True

                            MDCard:
                                size_hint: None, None
                                size: "80dp", "80dp"
                                radius: [10, 10, 10, 10]
                                md_bg_color: app.current_colors['card_bg']
                                pos_hint: {'center_x': 0.5, 'center_y': 0.5}

                                AsyncImage:
                                    id: main_avatar
                                    source: app.get_avatar_path()
                                    size_hint: 1, 1
                                    pos_hint: {'x': 0, 'y': 0}
                                    keep_ratio: False
                                    allow_stretch: True

                            MDBoxLayout:
                                orientation: 'vertical'
                                spacing: "5dp"
                                adaptive_height: True

                                MDLabel:
                                    id: main_nickname
                                    text: app.profile_nickname if app.profile_nickname else "Не указан"
                                    font_style: "H6"
                                    theme_text_color: "Primary"
                                    size_hint_y: None
                                    height: self.texture_size[1]

                                MDRaisedButton:
                                    text: "Настроить профиль"
                                    on_release: app.set_screen('profile_settings')
                                    size_hint_x: 1
                                    md_bg_color: app.current_colors['primary']
                                    text_color: app.current_colors['text']

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Управление TTS"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'horizontal'
                            spacing: "20dp"
                            adaptive_height: True
                            size_hint_x: 1

                            MDIconButton:
                                icon: "volume-minus"
                                on_release: app.decrease_volume()
                                md_bg_color: app.current_colors['primary']
                                theme_icon_color: "Custom"
                                icon_color: app.current_colors['text']
                                size_hint_x: 0.15

                            MDLabel:
                                id: volume_label
                                text: f"Громкость: {app.volume}%"
                                halign: 'center'
                                size_hint_x: 0.7
                                font_style: "Subtitle1"

                            MDIconButton:
                                icon: "volume-plus"
                                on_release: app.increase_volume()
                                md_bg_color: app.current_colors['primary']
                                theme_icon_color: "Custom"
                                icon_color: app.current_colors['text']
                                size_hint_x: 0.15

                        MDBoxLayout:
                            orientation: 'horizontal'
                            adaptive_height: True
                            spacing: "10dp"





                    CustomCard:
                        size_hint_x: 1

                        MDBoxLayout:
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "10dp"

                            MDLabel:
                                text: f"Активный модуль: {app.current_model}"
                                font_style: "H6"
                                size_hint_y: None
                                height: self.texture_size[1]
                                theme_text_color: "Primary"
                                bold: True

                            MDBoxLayout:
                                orientation: 'horizontal'
                                spacing: "10dp"
                                adaptive_height: True

                                MDRaisedButton:
                                    text: "Управление нейросетями"
                                    on_release: app.set_screen('neural')
                                    size_hint_x: 0.7
                                    md_bg_color: app.current_colors['primary']
                                    text_color: app.current_colors['text']

                                MDIconButton:
                                    icon: "refresh"
                                    on_release: app.check_all_local_models
                                    md_bg_color: app.current_colors['accent']
                                    theme_icon_color: "Custom"
                                    icon_color: app.current_colors['text']
                                    size_hint_x: 0.15

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Быстрые действия"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "10dp"

                            MDRaisedButton:
                                text: "Тест TTS"
                                on_release: app.test_tts()
                                size_hint_x: 1
                                md_bg_color: app.current_colors['primary']
                                text_color: app.current_colors['text']

                            MDRaisedButton:
                                text: "Настройки аудио"
                                on_release: app.set_screen('audio')
                                size_hint_x: 1
                                md_bg_color: app.current_colors['primary']
                                text_color: app.current_colors['text']

                            MDRaisedButton:
                                text: "Чат"
                                on_release: app.set_screen('chat')
                                size_hint_x: 1
                                md_bg_color: app.current_colors['primary']
                                text_color: app.current_colors['text']

<ProfileViewScreen>:
    name: 'profile_view'

    FloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}

            MDTopAppBar:
                title: "Мой профиль"
                elevation: 4
                md_bg_color: app.current_colors['primary']
                specific_text_color: app.current_colors['text']
                left_action_items: [['arrow-left', lambda x: app.set_screen('main')]]
                right_action_items: [['cog', lambda x: app.set_screen('profile_settings')]]

            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: "20dp"
                    padding: "20dp"
                    adaptive_height: True

                    MDCard:
                        orientation: 'horizontal'
                        padding: "20dp"
                        spacing: "20dp"
                        size_hint_y: None
                        height: "200dp"
                        md_bg_color: app.current_colors['card_bg']
                        radius: [15,]
                        elevation: 2
                        pos_hint: {'x': 0, 'top': 1}

                        MDCard:
                            size_hint: None, None
                            size: "150dp", "150dp"
                            radius: [10, 10, 10, 10]
                            md_bg_color: app.current_colors['card_bg']

                            AsyncImage:
                                id: profile_avatar
                                source: app.get_avatar_path()
                                size_hint: 1, 1
                                keep_ratio: False
                                allow_stretch: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            size_hint_x: 0.7
                            size_hint_y: None
                            height: "150dp"
                            md_bg_color: app.current_colors['card_bg']
                            radius: [10,]
                            padding: "15dp"
                            spacing: "10dp"

                            MDLabel:
                                text: "Никнейм"
                                font_style: "Caption"
                                theme_text_color: "Secondary"
                                size_hint_y: None
                                height: "20dp"

                            MDLabel:
                                id: profile_view_nickname
                                text: app.profile_nickname if app.profile_nickname else "Не указан"
                                font_style: "H4"
                                bold: True
                                theme_text_color: "Primary"
                                size_hint_y: None
                                height: self.texture_size[1]

                    MDCard:
                        size_hint: None, None
                        size: "990dp", "600dp"
                        radius: [10, 10, 10, 10]
                        md_bg_color: app.current_colors['card_bg']
                        pos_hint: {'center_x': 0.5}
                        padding: "10dp"

                        AsyncImage:
                            id: profile_banner
                            source: app.get_banner_path()
                            size_hint: None, None
                            size: "970dp", "500dp"
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                            keep_ratio: False
                            allow_stretch: True

                    MDCard:
                        orientation: 'vertical'
                        padding: "20dp"
                        spacing: "10dp"
                        size_hint_y: None
                        height: self.minimum_height
                        md_bg_color: app.current_colors['card_bg']
                        radius: [15,]
                        elevation: 2

                        MDLabel:
                            text: "Мои заметки"
                            font_style: "H6"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        ScrollView:
                            size_hint_y: None
                            height: "300dp"
                            do_scroll_x: False

                            MDLabel:
                                id: profile_view_notes
                                text: app.profile_notes if app.profile_notes else "Нет заметок"
                                font_style: "Body1"
                                theme_text_color: "Secondary"
                                size_hint_y: None
                                height: self.texture_size[1]
                                padding: "10dp"
                                text_size: self.width, None

<ProfileSettingsScreen>:
    name: 'profile_settings'

    FloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}

            MDTopAppBar:
                title: "Настройки профиля"
                elevation: 4
                md_bg_color: app.current_colors['primary']
                specific_text_color: app.current_colors['text']
                left_action_items: [['arrow-left', lambda x: app.set_screen('profile_view')]]
                right_action_items: [['content-save', lambda x: app.save_profile_settings()], ['restart', lambda x: app.restart_app()]]

            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: "20dp"
                    padding: "20dp"
                    adaptive_height: True

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: f"Аватарка ({app.avatar_size}x{app.avatar_size})"
                            font_style: "H6"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            spacing: "15dp"
                            adaptive_height: True

                            MDCard:
                                size_hint: None, None
                                size: "200dp", "200dp"
                                radius: [10, 10, 10, 10]
                                md_bg_color: app.current_colors['card_bg']
                                pos_hint: {'center_x': 0.5}

                                FloatLayout:
                                    id: avatar_container
                                    AsyncImage:
                                        id: avatar_preview
                                        source: app.get_avatar_path()
                                        size_hint: 1, 1
                                        pos_hint: {'x': 0, 'y': 0}
                                        keep_ratio: False
                                        allow_stretch: True

                            MDBoxLayout:
                                orientation: 'horizontal'
                                spacing: "10dp"
                                adaptive_height: True

                                MDRaisedButton:
                                    text: "Загрузить аватарку"
                                    on_release: app.load_profile_avatar()
                                    size_hint_x: 0.5
                                    md_bg_color: app.current_colors['primary']
                                    text_color: app.current_colors['text']

                                MDRaisedButton:
                                    text: "Удалить"
                                    on_release: app.delete_profile_avatar()
                                    size_hint_x: 0.5
                                    md_bg_color: 0.8, 0.2, 0.2, 1
                                    text_color: 1, 1, 1, 1

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Никнейм"
                            font_style: "H6"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDTextField:
                            id: nickname_input
                            text: app.profile_nickname
                            hint_text: "Введите ваш никнейм"
                            size_hint_x: 1
                            mode: "rectangle"
                            hint_text_color_normal: app.current_colors['primary']
                            multiline: False

                        MDBoxLayout:
                            orientation: 'horizontal'
                            spacing: "10dp"
                            adaptive_height: True
                            size_hint_x: 1
                            padding: "10dp"

                            MDRaisedButton:
                                text: "Сохранить ник"
                                on_release: app.save_nickname()
                                size_hint_x: 0.5
                                md_bg_color: app.current_colors['success']
                                text_color: app.current_colors['text']

                            MDRaisedButton:
                                text: "Удалить ник"
                                on_release: app.delete_nickname()
                                size_hint_x: 0.5
                                md_bg_color: 0.8, 0.2, 0.2, 1
                                text_color: 1, 1, 1, 1

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: f"Баннер ({app.banner_width}x{app.banner_height})"
                            font_style: "H6"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            spacing: "15dp"
                            adaptive_height: True

                            MDCard:
                                size_hint: None, None
                                size: f"{min(500, app.window_width - 60)}dp", "200dp"
                                radius: [10, 10, 10, 10]
                                md_bg_color: app.current_colors['card_bg']
                                pos_hint: {'center_x': 0.5}

                                FloatLayout:
                                    id: banner_container
                                    AsyncImage:
                                        id: banner_preview
                                        source: app.get_banner_path()
                                        size_hint: 1, 1
                                        pos_hint: {'x': 0, 'y': 0}
                                        keep_ratio: False
                                        allow_stretch: True

                            MDBoxLayout:
                                orientation: 'horizontal'
                                spacing: "10dp"
                                adaptive_height: True

                                MDRaisedButton:
                                    text: "Загрузить баннер"
                                    on_release: app.load_profile_banner()
                                    size_hint_x: 0.5
                                    md_bg_color: app.current_colors['primary']
                                    text_color: app.current_colors['text']

                                MDRaisedButton:
                                    text: "Удалить"
                                    on_release: app.delete_profile_banner()
                                    size_hint_x: 0.5
                                    md_bg_color: 0.8, 0.2, 0.2, 1
                                    text_color: 1, 1, 1, 1

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Мои заметки"
                            font_style: "H6"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            spacing: "15dp"
                            adaptive_height: True

                            MDTextField:
                                id: notes_input
                                text: app.profile_notes
                                hint_text: "Введите ваши заметки здесь..."
                                size_hint_x: 1
                                mode: "rectangle"
                                hint_text_color_normal: app.current_colors['primary']
                                multiline: True
                                height: "200dp"

                            MDBoxLayout:
                                orientation: 'horizontal'
                                spacing: "10dp"
                                adaptive_height: True

                                MDRaisedButton:
                                    text: "Сохранить заметки"
                                    on_release: app.save_profile_notes()
                                    size_hint_x: 0.5
                                    md_bg_color: app.current_colors['primary']
                                    text_color: app.current_colors['text']

                                MDRaisedButton:
                                    text: "Очистить"
                                    on_release: app.clear_profile_notes()
                                    size_hint_x: 0.5
                                    md_bg_color: 0.8, 0.2, 0.2, 1
                                    text_color: 1, 1, 1, 1

<AudioSettingsScreen>:
    name: 'audio'

    FloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}

            MDTopAppBar:
                title: "Настройки аудио"
                elevation: 4
                md_bg_color: app.current_colors['primary']
                specific_text_color: app.current_colors['text']
                left_action_items: [['arrow-left', lambda x: app.set_screen('main')]]
                right_action_items: [['refresh', lambda x: app.refresh_audio_devices()]]

            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: "20dp"
                    padding: "20dp"
                    adaptive_height: True

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Устройства ввода (Микрофоны)"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            id: microphones_list
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "10dp"

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Устройства вывода (Наушники/Динамики)"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            id: speakers_list
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "10dp"
<ChatScreen>:
    name: 'chat'

    FloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}

            MDTopAppBar:
                title: "Чат с ИИ"
                elevation: 4
                md_bg_color: app.current_colors['primary']
                specific_text_color: app.current_colors['text']
                left_action_items: [['arrow-left', lambda x: app.set_screen('main')]]
                right_action_items: [['image', lambda x: app.show_chat_background_dialog()], ['brain', lambda x: app.set_screen('neural')]]

            MDBoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: "60dp"
                padding: "5dp"
                spacing: "5dp"
                md_bg_color: app.current_colors['card_bg']

                MDBoxLayout:
                    orientation: 'vertical'
                    size_hint_x: 0.6

                    MDLabel:
                        text: "модель:"
                        font_style: "Caption"
                        theme_text_color: "Secondary"
                        size_hint_y: None
                        height: "20dp"

                    MDLabel:
                        id: active_model_label
                        text: f"{app.current_model}"
                        font_style: "Subtitle2"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: app.current_colors['primary']
                        size_hint_y: None
                        height: "30dp"

                MDBoxLayout:
                    orientation: 'vertical'
                    size_hint_x: 0.4

                    MDLabel:
                        text: "TTS:"
                        font_style: "Caption"
                        theme_text_color: "Secondary"
                        size_hint_y: None
                        height: "20dp"

                    MDLabel:
                        text: f"{'Вкл' if app.tts_enabled else 'Выкл'}"
                        font_style: "Subtitle2"
                        theme_text_color: "Custom"
                        text_color: app.current_colors['success'] if app.tts_enabled else app.current_colors['error']
                        size_hint_y: None
                        height: "30dp"

            ScrollView:
                id: chat_scroll
                do_scroll_x: False
                do_scroll_y: True
                scroll_type: ['content', 'bars']
                bar_width: dp(10)

                MDBoxLayout:
                    id: chat_container
                    orientation: 'vertical'
                    spacing: "10dp"
                    padding: "20dp"
                    size_hint_y: None
                    height: self.minimum_height
                    width: root.width - dp(40)

            MDBoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: "70dp"
                padding: "10dp"
                spacing: "10dp"
                md_bg_color: app.current_colors['card_bg']

                MDTextField:
                    id: message_input
                    hint_text: "Введите сообщение..."
                    size_hint_x: 0.7
                    mode: "rectangle"
                    hint_text_color_normal: 1, 1, 1, 0.5
                    text_color_normal: 1, 1, 1, 1
                    text_color_focus: 1, 1, 1, 1
                    on_text_validate: app.send_message()
                    multiline: True

                MDIconButton:
                    icon: "microphone"
                    on_release: app.start_voice_input
                    size_hint_x: 0.15
                    md_bg_color: app.current_colors['accent']
                    theme_icon_color: "Custom"
                    icon_color: app.current_colors['text']

                MDIconButton:
                    icon: "send"
                    on_release: app.send_message()
                    size_hint_x: 0.15
                    md_bg_color: app.current_colors['primary']
                    theme_icon_color: "Custom"
                    icon_color: app.current_colors['text']

<BackgroundSettingsScreen>:
    name: 'background'

    FloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}

            MDTopAppBar:
                title: "Настройки фона"
                elevation: 4
                md_bg_color: app.current_colors['primary']
                specific_text_color: app.current_colors['text']
                left_action_items: [['arrow-left', lambda x: app.set_screen('main')]]
                right_action_items: [['plus', lambda x: app.add_background_image()]]

            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: "20dp"
                    padding: "20dp"
                    adaptive_height: True

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Текущий фон приложения"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "15dp"

                            Image:
                                id: current_background_preview
                                source: app.background_image if app.background_image and os.path.exists(app.background_image) else ''
                                size_hint_y: None
                                height: "150dp"
                                keep_ratio: True
                                allow_stretch: True

                            MDBoxLayout:
                                orientation: 'horizontal'
                                spacing: "10dp"
                                size_hint_x: 1
                                adaptive_height: True

                                MDRaisedButton:
                                    text: "Применить текущий"
                                    on_release: app.apply_current_background
                                    size_hint_x: 0.5
                                    md_bg_color: app.current_colors['primary']
                                    text_color: app.current_colors['text']

                                MDRaisedButton:
                                    text: "Убрать фон"
                                    on_release: app.remove_background
                                    size_hint_x: 0.5
                                    md_bg_color: 0.8, 0.2, 0.2, 1
                                    text_color: 1, 1, 1, 1

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Текущий фон чата"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "15dp"

                            Image:
                                id: current_chat_background_preview
                                source: app.chat_background if app.chat_background and os.path.exists(app.chat_background) else ''
                                size_hint_y: None
                                height: "150dp"
                                keep_ratio: True
                                allow_stretch: True

                            MDBoxLayout:
                                orientation: 'horizontal'
                                spacing: "10dp"
                                size_hint_x: 1
                                adaptive_height: True

                                MDRaisedButton:
                                    text: "Применить текущий"
                                    on_release: app.apply_current_chat_background
                                    size_hint_x: 0.5
                                    md_bg_color: app.current_colors['primary']
                                    text_color: app.current_colors['text']

                                MDRaisedButton:
                                    text: "Убрать из чата"
                                    on_release: app.remove_chat_background
                                    size_hint_x: 0.5
                                    md_bg_color: 0.8, 0.2, 0.2, 1
                                    text_color: 1, 1, 1, 1

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Доступные фоны"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            id: backgrounds_list
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "10dp"

<ColorSettingsScreen>:
    name: 'color'

    FloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}

            MDTopAppBar:
                title: "Цвета кнопок"
                elevation: 4
                md_bg_color: app.current_colors['primary']
                specific_text_color: app.current_colors['text']
                left_action_items: [['arrow-left', lambda x: app.set_screen('main')]]
                right_action_items: [['refresh', lambda x: app.refresh_colors()]]

            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: "20dp"
                    padding: "20dp"
                    adaptive_height: True

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Выберите цветовую схему"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "15dp"

                            MDRaisedButton:
                                text: "Бирюзовый"
                                on_release: app.set_button_color('teal')
                                size_hint_x: 1
                                md_bg_color: [0.2, 0.6, 0.6, 1]
                                text_color: 1, 1, 1, 1
                                height: "50dp"

                            MDRaisedButton:
                                text: "Бежевый"
                                on_release: app.set_button_color('beige')
                                size_hint_x: 1
                                md_bg_color: [0.96, 0.96, 0.86, 1]
                                text_color: 0.2, 0.2, 0.2, 1
                                height: "50dp"

                            MDRaisedButton:
                                text: "Черный"
                                on_release: app.set_button_color('black')
                                size_hint_x: 1
                                md_bg_color: [0.1, 0.1, 0.1, 1]
                                text_color: 1, 1, 1, 1
                                height: "50dp"

                            MDRaisedButton:
                                text: "Белый"
                                on_release: app.set_button_color('white')
                                size_hint_x: 1
                                md_bg_color: [0.95, 0.95, 0.95, 1]
                                text_color: 0.1, 0.1, 0.1, 1
                                height: "50dp"

<NeuralScreen>:
    name: 'neural'

    FloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}

            MDTopAppBar:
                title: "Управление нейросетями"
                elevation: 4
                md_bg_color: app.current_colors['primary']
                specific_text_color: app.current_colors['text']
                left_action_items: [['arrow-left', lambda x: app.set_screen('main')]]
                right_action_items: [['refresh', lambda x: app.refresh_neural_models()], ['cloud-search', lambda x: app.check_all_local_models()]]

            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: "20dp"
                    padding: "20dp"
                    adaptive_height: True

                    CustomCard:
                        size_hint_x: 1

                        MDBoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: "50dp"

                            MDLabel:
                                text: "Локальные нейросети"
                                font_style: "H5"
                                theme_text_color: "Primary"
                                bold: True

                            MDRaisedButton:
                                text: "Проверить все"
                                on_release: app.check_all_local_models
                                size_hint_x: 0.4
                                md_bg_color: app.current_colors['accent']
                                text_color: app.current_colors['text']
                                height: "40dp"

                        MDBoxLayout:
                            id: local_models_container
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "10dp"

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Облачные нейросети"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            id: cloud_models_container
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "10dp"

                    CustomCard:
                        size_hint_x: 1

                        MDLabel:
                            text: "Настройки API"
                            font_style: "H5"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                            bold: True

                        MDBoxLayout:
                            orientation: 'vertical'
                            adaptive_height: True
                            spacing: "10dp"

                            MDRaisedButton:
                                text: "Настроить API ключи"
                                on_release: app.show_api_key_dialog()
                                size_hint_x: 1
                                md_bg_color: app.current_colors['primary']
                                text_color: app.current_colors['text']

                            MDRaisedButton:
                                text: "Подключить все"
                                on_release: app.connect_all_models()
                                size_hint_x: 1
                                md_bg_color: app.current_colors['accent']
                                text_color: app.current_colors['text']

ScreenManager:
    SplashScreen:
    MainScreen:
    ProfileViewScreen:
    ProfileSettingsScreen:
    AudioSettingsScreen:
    ChatScreen:
    BackgroundSettingsScreen:
    ColorSettingsScreen:
    NeuralScreen:
'''


class SplashScreen(MDScreen):
    def on_enter(self):
        Clock.schedule_once(self.animate_loading, 0.1)

    def animate_loading(self, dt):
        try:
            self.progress_bar = self.ids.progress_bar
            self.loading_text = self.ids.loading_text
            self.update_progress(0)
        except Exception as e:
            print(f"Ошибка в animate_loading: {e}")

    def update_progress(self, value):
        if hasattr(self, 'progress_bar') and hasattr(self, 'loading_text'):
            self.progress_bar.value = value
            if value < 30:
                self.loading_text.text = "Инициализация..."
            elif value < 60:
                self.loading_text.text = "Загрузка настроек..."
            elif value < 90:
                self.loading_text.text = "Поиск нейросетей..."
            else:
                self.loading_text.text = "Запуск..."
            if value < 100:
                Clock.schedule_once(lambda dt: self.update_progress(value + 10), 0.6)


class MainScreen(MDScreen):
    pass


class ProfileViewScreen(MDScreen):
    pass


class ProfileSettingsScreen(MDScreen):
    pass


class AudioSettingsScreen(MDScreen):
    pass


class ChatScreen(MDScreen):
    pass


class BackgroundSettingsScreen(MDScreen):
    pass


class ColorSettingsScreen(MDScreen):
    pass


class NeuralScreen(MDScreen):
    pass


class ModelCard(MDCard):
    model_id = StringProperty('')
    model_data = ObjectProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class BackgroundImage(Image):
    """Специальный класс для фонового изображения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keep_ratio = False
        self.allow_stretch = True
        self.is_background = True


class AudioDeviceCard(MDCard):
    # Карточка для отображения аудио устройства с кнопкой выбора

    def __init__(self, device_name, device_id, device_type, is_selected=False, **kwargs):
        super().__init__(**kwargs)
        self.device_name = device_name
        self.device_id = device_id
        self.device_type = device_type
        self.is_selected = is_selected
        self.app = MDApp.get_running_app()

        self.orientation = 'horizontal'
        self.padding = "10dp"
        self.spacing = "10dp"
        self.size_hint_y = None
        self.height = "60dp"
        self.md_bg_color = self.app.current_colors['card_bg']
        self.radius = [10, ]
        self.elevation = 1

        # Иконка в зависимости от типа устройства
        icon = "microphone" if device_type == "input" else "headphones"

        # Иконка устройства
        self.icon_button = MDIconButton(
            icon=icon,
            theme_icon_color="Custom",
            icon_color=self.app.current_colors['primary'],
            size_hint_x=0.15
        )

        # Название устройства
        display_name = device_name if len(device_name) <= 30 else device_name[:27] + "..."
        self.name_label = MDLabel(
            text=display_name,
            font_style="Subtitle2",
            size_hint_x=0.55,
            halign='left'
        )

        # Кнопка выбора
        self.select_button = MDRaisedButton(
            text="Выбрать" if not is_selected else "Выбрано",
            on_release=self.on_select,
            size_hint_x=0.3,
            md_bg_color=self.app.current_colors['success'] if is_selected else self.app.current_colors['primary'],
            text_color=self.app.current_colors['text'],
            height="40dp"
        )

        self.add_widget(self.icon_button)
        self.add_widget(self.name_label)
        self.add_widget(self.select_button)

    def on_select(self, *args):
        """Обработчик выбора устройства"""
        if self.device_type == "input":
            self.app.select_microphone(self.device_name, self.device_id)
        else:
            self.app.select_speakers(self.device_name, self.device_id)


class TTSApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Устанавливаем иконку для приложения
        self.icon = ICON_PATH_PNG
        self.title = "AIAT"
        # заставка для приложения
        self.screensaver_path = SCREENSAVER_PATH
        self.window_width = Window.width
        self.window_height = Window.height

        # Размеры для профиля - делаем их атрибутами экземпляра класса
        self.avatar_size = 400
        self.banner_width = 970
        self.banner_height = 500

        self.volume = 50
        self.tts_enabled = True
        self.tts_responses_enabled = False
        self.speech_rate = 1.0
        self.speech_pitch = 1.0
        self.microphone = {'name': 'default', 'id': None}
        self.speakers = {'name': 'default', 'id': None}
        self.noise_cancellation = True
        self.echo_cancellation = True
        self.audio_devices = {'inputs': [], 'outputs': []}
        self.background_image = ''
        self.chat_background = ''
        self.file_manager = None
        self.dialog = None
        self.menu = None
        self.store = JsonStore(os.path.join(BASE_DIR, 'settings.json'))
        self.is_ready = False
        self.current_color_scheme = 'teal'
        self.current_colors = BUTTON_COLORS['teal']
        self.needs_restart = False
        self.neural_models = NEURAL_MODELS.copy()
        self.current_model = ""
        self.current_model_id = None
        self.api_keys = {}
        self._backgrounds_added = False

        # Данные профиля
        self.profile_avatar = ''
        self.profile_nickname = ''
        self.profile_banner = ''
        self.profile_notes = ''

        # TTS Engine
        self.tts_engine = None
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.tts_running = False

        # Хранилище для загруженных моделей ctransformers
        self.ctransformers_models = {}

        # История чата
        self.chat_history = []
        # блокировка чата (по возможности)
        self._model_lock = threading.Lock()

        # Инициализируем TTS
        self.init_tts()

        # Запускаем загрузку Silero в фоне сразу при старте
        threading.Thread(target=load_silero_model, daemon=True).start()

    def init_tts(self):
        # Инициализация TTS движка
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', self.volume / 100)
            self.tts_running = True
            self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self.tts_thread.start()
            print("TTS инициализирован")
        except Exception as e:
            print(f"Ошибка инициализации TTS: {e}")
            self.tts_enabled = False

    def _tts_worker(self):
        while self.tts_running:
            try:
                text = self.tts_queue.get(timeout=1)
                if not text:
                    continue

                if SILERO_AVAILABLE and silero_model is not None:
                    try:
                        audio = silero_model.apply_tts(
                            text=text,
                            speaker='baya',
                            sample_rate=48000,
                            put_accent=True,
                            put_yo=True
                        )
                        volume_factor = self.volume / 100.0
                        audio_data = audio.numpy() * volume_factor
                        sd.play(audio_data, samplerate=48000)
                        sd.wait()
                        continue
                    except Exception as e:
                        print(f"⚠️ Silero ошибка: {e}")

                if self.tts_engine:
                    try:
                        self.tts_engine.setProperty('volume', self.volume / 100)
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                    except Exception as e:
                        print(f"⚠️ pyttsx3 ошибка: {e}")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS worker ошибка: {e}")
                continue

    def speak_text(self, text):
        if self.tts_enabled and text:
            self.tts_queue.put(text)

    def get_avatar_path(self):
        avatar_path = os.path.join(PROFILE_AVATARS_PATH, 'avatar.png')
        return avatar_path if os.path.exists(avatar_path) else ''

    def get_banner_path(self):
        banner_path = os.path.join(PROFILE_BANNERS_PATH, 'banner.png')
        return banner_path if os.path.exists(banner_path) else ''

    def update_profile_preview(self):
        try:
            if self.root and self.root.has_screen('profile_settings'):
                profile_screen = self.root.get_screen('profile_settings')
                if hasattr(profile_screen, 'ids'):
                    if 'avatar_preview' in profile_screen.ids:
                        profile_screen.ids.avatar_preview.reload()
                    if 'banner_preview' in profile_screen.ids:
                        profile_screen.ids.banner_preview.reload()

            if self.root and self.root.has_screen('main'):
                main_screen = self.root.get_screen('main')
                for child in main_screen.walk():
                    if isinstance(child, AsyncImage):
                        child.reload()

            if self.root and self.root.has_screen('profile_view'):
                profile_view_screen = self.root.get_screen('profile_view')
                for child in profile_view_screen.walk():
                    if isinstance(child, AsyncImage):
                        child.reload()

            print("Все изображения профиля обновлены")
        except Exception as e:
            print(f"Ошибка обновления превью: {e}")

    def update_profile_ui(self):
        try:
            # Берем только имя файла, чтобы не плодить пути типа avatar/avatar
            avatar_file = os.path.basename(self.profile_avatar) if self.profile_avatar else ""
            banner_file = os.path.basename(self.profile_banner) if self.profile_banner else ""

            # Чистые пути к папкам
            abs_avatar_path = os.path.join(BASE_DIR, 'avatar', avatar_file) if avatar_file else ""
            abs_banner_path = os.path.join(BASE_DIR, 'banner', banner_file) if banner_file else ""

            # Обновляем экраны
            screens_to_update = {
                'main': ['main_nickname', 'profile_avatar'],
                'profile_view': ['profile_view_nickname', 'profile_view_notes', 'view_avatar', 'view_banner'],
                'profile_settings': ['nickname_input', 'notes_input', 'edit_avatar']
            }

            for screen_name, ids_list in screens_to_update.items():
                if self.root and self.root.has_screen(screen_name):
                    screen = self.root.get_screen(screen_name)
                    # Никнеймы
                    for nid in [i for i in ids_list if 'nickname' in i or 'input' in i]:
                        if nid in screen.ids:
                            val = self.profile_nickname if 'input' in nid else (self.profile_nickname or "Не указан")
                            screen.ids[nid].text = val
                    # Аватарки
                    for aid in [i for i in ids_list if 'avatar' in i and 'edit' not in i]:
                        if aid in screen.ids and abs_avatar_path and os.path.exists(abs_avatar_path):
                            screen.ids[aid].source = abs_avatar_path
                            screen.ids[aid].reload()
                    # Баннеры
                    if 'view_banner' in screen.ids and abs_banner_path and os.path.exists(abs_banner_path):
                        screen.ids.view_banner.source = abs_banner_path
                        screen.ids.view_banner.reload()

            print(f"UI профиля обновлен: ават='{avatar_file}'")
        except Exception as e:
            print(f"Ошибка обновления UI профиля: {e}")

    def load_settings(self):
        try:
            if self.store.exists('background'):
                bg_data = self.store.get('background')
                if isinstance(bg_data, dict):
                    bg_path = bg_data.get('path', '')
                    if bg_path and os.path.exists(bg_path):
                        self.background_image = bg_path
                        print(f"Загружен фон приложения: {bg_path}")

            if self.store.exists('chat_background'):
                chat_data = self.store.get('chat_background')
                if isinstance(chat_data, dict):
                    chat_path = chat_data.get('path', '')
                    if chat_path and os.path.exists(chat_path):
                        self.chat_background = chat_path
                        print(f"Загружен фон чата: {chat_path}")

            if self.store.exists('color_scheme'):
                scheme_data = self.store.get('color_scheme')
                if isinstance(scheme_data, dict):
                    scheme = scheme_data.get('name', 'teal')
                    if scheme in BUTTON_COLORS:
                        self.current_color_scheme = scheme
                        self.current_colors = BUTTON_COLORS[scheme]
                        print(f"Загружена цветовая схема: {scheme}")

            if self.store.exists('api_keys'):
                api_data = self.store.get('api_keys')
                if isinstance(api_data, dict):
                    self.api_keys = api_data
                    for model_id, key in self.api_keys.items():
                        if model_id in self.neural_models['cloud']:
                            self.neural_models['cloud'][model_id]['api_key'] = key

            if self.store.exists('model_status'):
                model_data = self.store.get('model_status')
                if isinstance(model_data, dict):
                    for model_type in ['local', 'cloud']:
                        for model_id, model in self.neural_models[model_type].items():
                            if model_id in model_data:
                                model['status'] = model_data[model_id]

            if self.store.exists('tts_settings'):
                tts_data = self.store.get('tts_settings')
                if isinstance(tts_data, dict):
                    self.tts_enabled = tts_data.get('enabled', True)
                    self.tts_responses_enabled = tts_data.get('responses_enabled', False)
                    self.volume = tts_data.get('volume', 50)
                    if 'microphone' in tts_data:
                        self.microphone = tts_data.get('microphone', {'name': 'default', 'id': None})
                    if 'speakers' in tts_data:
                        self.speakers = tts_data.get('speakers', {'name': 'default', 'id': None})

            nick_file = os.path.join(PROFILE_NAMES_PATH, 'nickname.txt')
            if os.path.exists(nick_file):
                try:
                    with open(nick_file, 'r', encoding='utf-8') as f:
                        self.profile_nickname = f.read().strip()
                    print(f"Загружен ник из {nick_file}: {self.profile_nickname}")
                except Exception as e:
                    print(f"Ошибка загрузки ника: {e}")

            notes_file = os.path.join(PROFILE_NOTES_PATH, 'notes.txt')
            if os.path.exists(notes_file):
                try:
                    with open(notes_file, 'r', encoding='utf-8') as f:
                        self.profile_notes = f.read()
                    print(f"Загружены заметки из {notes_file}")
                except Exception as e:
                    print(f"Ошибка загрузки заметок: {e}")

            if self.store.exists('profile'):
                profile_data = self.store.get('profile')
                if isinstance(profile_data, dict):
                    if not self.profile_nickname:
                        self.profile_nickname = profile_data.get('nickname', '')
                    self.profile_avatar = profile_data.get('avatar', '')
                    self.profile_banner = profile_data.get('banner', '')
                    print(f"Загружен профиль из JSON: ник={self.profile_nickname}")

        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    def save_settings(self):
        try:
            print(f"Сохраняем цветовую схему: {self.current_color_scheme}")

            self.store['background'] = {'path': self.background_image}
            self.store['chat_background'] = {'path': self.chat_background}
            self.store['color_scheme'] = {'name': self.current_color_scheme}
            self.store['api_keys'] = self.api_keys
            self.store['tts_settings'] = {
                'enabled': self.tts_enabled,
                'responses_enabled': self.tts_responses_enabled,
                'volume': self.volume,
                'microphone': self.microphone,
                'speakers': self.speakers
            }

            self.store['profile'] = {
                'avatar': self.profile_avatar,
                'nickname': self.profile_nickname,
                'banner': self.profile_banner
            }

            model_status = {}
            for model_type in ['local', 'cloud']:
                for model_id, model in self.neural_models[model_type].items():
                    model_status[model_id] = model['status']
            self.store['model_status'] = model_status

            print("Настройки сохранены успешно")
            return True

        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False

    def save_nickname(self):
        try:
            if self.root and self.root.has_screen('profile_settings'):
                profile_screen = self.root.get_screen('profile_settings')
                if hasattr(profile_screen, 'ids') and 'nickname_input' in profile_screen.ids:
                    new_nickname = profile_screen.ids.nickname_input.text.strip()
                    nick_file = os.path.join(PROFILE_NAMES_PATH, 'nickname.txt')
                    with open(nick_file, 'w', encoding='utf-8') as f:
                        f.write(new_nickname)
                    print(f"Ник сохранен в {nick_file}: {new_nickname}")
                    self.profile_nickname = new_nickname
                    self.save_settings()
                    self.update_profile_ui()
                    self.show_dialog("Успех", f"Никнейм '{new_nickname}' сохранен!")
        except Exception as e:
            print(f"Ошибка сохранения ника: {e}")
            self.show_dialog("Ошибка", f"Не удалось сохранить ник: {str(e)}")

    def delete_nickname(self):
        try:
            nick_file = os.path.join(PROFILE_NAMES_PATH, 'nickname.txt')
            if os.path.exists(nick_file):
                os.remove(nick_file)
                print(f"Ник удален: {nick_file}")

            if self.root and self.root.has_screen('profile_settings'):
                profile_screen = self.root.get_screen('profile_settings')
                if hasattr(profile_screen, 'ids') and 'nickname_input' in profile_screen.ids:
                    profile_screen.ids.nickname_input.text = ""

            self.profile_nickname = ""
            self.save_settings()
            self.update_profile_ui()
            self.show_dialog("Успех", "Никнейм удален!")
        except Exception as e:
            print(f"Ошибка удаления ника: {e}")
            self.show_dialog("Ошибка", f"Не удалось удалить ник: {str(e)}")

    def save_profile_notes(self):
        try:
            if self.root and self.root.has_screen('profile_settings'):
                profile_screen = self.root.get_screen('profile_settings')
                if hasattr(profile_screen, 'ids') and 'notes_input' in profile_screen.ids:
                    self.profile_notes = profile_screen.ids.notes_input.text

            notes_file = os.path.join(PROFILE_NOTES_PATH, 'notes.txt')
            with open(notes_file, 'w', encoding='utf-8') as f:
                f.write(self.profile_notes)
            print(f"Заметки сохранены в {notes_file}")
            self.update_profile_ui()
            self.show_dialog("Успех", "Заметки сохранены")
            return True
        except Exception as e:
            print(f"Ошибка сохранения заметок: {e}")
            self.show_dialog("Ошибка", f"Не удалось сохранить заметки: {str(e)}")
            return False

    def clear_profile_notes(self):
        try:
            if self.root and self.root.has_screen('profile_settings'):
                profile_screen = self.root.get_screen('profile_settings')
                if hasattr(profile_screen, 'ids') and 'notes_input' in profile_screen.ids:
                    profile_screen.ids.notes_input.text = ""
                    self.profile_notes = ""
                    notes_file = os.path.join(PROFILE_NOTES_PATH, 'notes.txt')
                    with open(notes_file, 'w', encoding='utf-8') as f:
                        f.write("")
                    self.update_profile_ui()
                    self.show_dialog("Успех", "Заметки очищены")
        except Exception as e:
            print(f"Ошибка очистки заметок: {e}")

    def save_profile_settings(self):
        try:
            if self.root and self.root.has_screen('profile_settings'):
                profile_screen = self.root.get_screen('profile_settings')
                if hasattr(profile_screen, 'ids') and 'nickname_input' in profile_screen.ids:
                    self.profile_nickname = profile_screen.ids.nickname_input.text

            self.save_settings()
            self.update_profile_preview()
            self.update_profile_ui()
            self.show_dialog("Успех", "Настройки профиля сохранены.")
        except Exception as e:
            print(f"Ошибка сохранения профиля: {e}")

    def load_profile_avatar(self):
        if not self.is_ready:
            return

        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_profile_avatar,
            ext=['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        )
        self.file_manager.show(os.path.expanduser("~"))

    def select_profile_avatar(self, path):
        try:
            avatar_path = os.path.join(PROFILE_AVATARS_PATH, 'avatar.png')

            if os.path.exists(avatar_path):
                os.remove(avatar_path)
                print(f"Старая аватарка удалена: {avatar_path}")

            try:
                img = PILImage.open(path).convert('RGBA')
                img = img.resize((self.avatar_size, self.avatar_size), PILImage.Resampling.LANCZOS)
                img.save(avatar_path, 'PNG')
                print(f"Новая аватарка сохранена: {avatar_path}")
            except Exception as img_error:
                print(f"Ошибка обработки изображения: {img_error}, копируем как есть")
                shutil.copy2(path, avatar_path)

            self.profile_avatar = avatar_path
            self.update_profile_preview()
            self.show_dialog("Успех", "Аватарка загружена и обновлена на всех экранах!")

        except Exception as e:
            print(f"Ошибка при загрузке аватарки: {e}")
            self.show_dialog("Ошибка", f"Не удалось загрузить аватарку: {str(e)}")

        self.exit_file_manager()

    def delete_profile_avatar(self):
        try:
            avatar_path = os.path.join(PROFILE_AVATARS_PATH, 'avatar.png')
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
                self.profile_avatar = ''
                self.update_profile_preview()
                self.show_dialog("Успех", "Аватарка удалена")
                self.save_settings()
        except Exception as e:
            print(f"Ошибка при удалении аватарки: {e}")

    def load_profile_banner(self):
        if not self.is_ready:
            return

        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_profile_banner,
            ext=['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        )
        self.file_manager.show(os.path.expanduser("~"))

    def select_profile_banner(self, path):
        try:
            banner_path = os.path.join(PROFILE_BANNERS_PATH, 'banner.png')

            if os.path.exists(banner_path):
                os.remove(banner_path)
                print(f"Старый баннер удален: {banner_path}")

            try:
                img = PILImage.open(path).convert('RGBA')
                img = img.resize((self.banner_width, self.banner_height), PILImage.Resampling.LANCZOS)
                img.save(banner_path, 'PNG')
                print(f"Новый баннер сохранен: {banner_path}")
            except Exception as img_error:
                print(f"Ошибка обработки изображения: {img_error}, копируем как есть")
                shutil.copy2(path, banner_path)

            self.profile_banner = banner_path
            self.update_profile_preview()
            self.show_dialog("Успех", "Баннер загружен и обновлен на всех экранах!")

        except Exception as e:
            print(f"Ошибка при загрузке баннера: {e}")
            self.show_dialog("Ошибка", f"Не удалось загрузить баннер: {str(e)}")

        self.exit_file_manager()

    def delete_profile_banner(self):
        try:
            banner_path = os.path.join(PROFILE_BANNERS_PATH, 'banner.png')
            if os.path.exists(banner_path):
                os.remove(banner_path)
                self.profile_banner = ''
                self.update_profile_preview()
                self.show_dialog("Успех", "Баннер удален")
                self.save_settings()
        except Exception as e:
            print(f"Ошибка при удалении баннера: {e}")

    def update_ui_colors(self):
        try:
            print(f"Обновляем цвета интерфейса на схему: {self.current_color_scheme}")

            if self.root:
                for screen_name in ['main', 'profile_view', 'profile_settings', 'audio', 'chat', 'background', 'color',
                                    'neural']:
                    if self.root.has_screen(screen_name):
                        screen = self.root.get_screen(screen_name)

                        for child in screen.walk(restrict=True):
                            if hasattr(child, 'md_bg_color'):
                                if isinstance(child, (MDRaisedButton, MDIconButton, MDFlatButton)):
                                    if child.text in ['Бирюзовый', 'Бежевый', 'Черный', 'Белый']:
                                        continue
                                    child.md_bg_color = self.current_colors['primary']
                                    if hasattr(child, 'text_color'):
                                        child.text_color = self.current_colors['text']
                                elif isinstance(child, MDCard):
                                    child.md_bg_color = self.current_colors['card_bg']
                                elif isinstance(child, MDTopAppBar):
                                    child.md_bg_color = self.current_colors['primary']
                                    child.specific_text_color = self.current_colors['text']
                                elif isinstance(child, MDSwitch):
                                    child.active_color = self.current_colors['primary']
                                elif isinstance(child, MDSlider):
                                    child.color = self.current_colors['accent']
                                elif isinstance(child, MDTextField):
                                    child.hint_text_color_normal = self.current_colors['primary']

                        if screen_name == 'chat' and self.chat_background:
                            self.add_background_to_screen(screen, self.chat_background)
                        else:
                            self.add_background_to_screen(screen, self.background_image)

            print("Цвета интерфейса обновлены")

        except Exception as e:
            print(f"Ошибка обновления цветов: {e}")

    def set_button_color(self, scheme_name):
        print(f"Устанавливаем цветовую схему: {scheme_name}")
        if scheme_name in BUTTON_COLORS:
            self.current_color_scheme = scheme_name
            self.current_colors = BUTTON_COLORS[scheme_name]
            self.save_settings()
            self.update_ui_colors()
            self.update_audio_devices_ui()
            self.show_dialog("Успех", f"Цветовая схема '{scheme_name}' применена")

    def refresh_colors(self):
        print("Обновляем цвета из сохраненной схемы")
        self.update_ui_colors()

    def restart_app(self):
        print("Перезапуск приложения...")
        if self.save_settings():
            python = sys.executable
            os.execl(python, python, *sys.argv)
        else:
            print("Не удалось сохранить настройки, перезапуск отменен")
            self.show_dialog("Ошибка", "Не удалось сохранить настройки")

    def set_background_image(self, image_path):
        print(f"Устанавливаем фон приложения: {image_path}")
        if os.path.exists(image_path):
            self.background_image = image_path
            self.restart_app()
        else:
            print(f"Файл не существует: {image_path}")
            self.show_dialog("Ошибка", "Файл не существует")

    def set_chat_background(self, image_path):
        print(f"Устанавливаем фон чата: {image_path}")
        if os.path.exists(image_path):
            self.chat_background = image_path
            self.restart_app()
        else:
            print(f"Файл не существует: {image_path}")
            self.show_dialog("Ошибка", "Файл не существует")

    def apply_current_background(self):
        if self.background_image and os.path.exists(self.background_image):
            self.restart_app()
        else:
            self.show_dialog("Ошибка", "Сначала выберите фон из списка")

    def apply_current_chat_background(self):
        if self.chat_background and os.path.exists(self.chat_background):
            self.restart_app()
        else:
            self.show_dialog("Ошибка", "Сначала выберите фон для чата из списка")

    def remove_background(self):
        print("Убираем фон приложения")
        self.background_image = ''
        self.restart_app()

    def remove_chat_background(self):
        print("Убираем фон чата")
        self.chat_background = ''
        self.restart_app()

    def add_background_to_screen(self, screen, image_path):
        try:
            if not screen or not hasattr(screen, 'children') or len(screen.children) == 0:
                return

            root_layout = screen.children[0]

            to_remove = []
            for child in root_layout.children:
                if hasattr(child, 'is_background') and child.is_background:
                    to_remove.append(child)

            for child in to_remove:
                root_layout.remove_widget(child)

            if image_path and os.path.exists(image_path):
                background = BackgroundImage(
                    source=image_path,
                    size=root_layout.size,
                    pos=root_layout.pos
                )
                background.is_background = True

                current_children = list(root_layout.children)

                root_layout.clear_widgets()

                root_layout.add_widget(background)

                for child in reversed(current_children):
                    if not hasattr(child, 'is_background'):
                        root_layout.add_widget(child)

                print(f"Фон добавлен на экран {screen.name} как нижний слой")

        except Exception as e:
            print(f"Ошибка добавления фона: {e}")

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Amber"
        return Builder.load_string(KV)

    def on_start(self):
        Clock.schedule_once(lambda dt: apply_dark_titlebar(), 0.5)  # ← добавить
        Clock.schedule_once(self.initialize_app, 0.1)

    def on_stop(self):
        self.tts_running = False
        if self.tts_engine:
            self.tts_engine.stop()

    def initialize_app(self, dt):
        try:
            if not self.root:
                print("Root еще не инициализирован")
                Clock.schedule_once(self.initialize_app, 0.1)
                return

            print("Root инициализирован, начинаем загрузку...")

            if self.root.has_screen('splash'):
                self.root.current = 'splash'
                print("Показываем сплэш экран")

            self.load_settings()
            Clock.schedule_once(self.add_backgrounds, 0.5)
            Clock.schedule_once(self.loading_process, 1.0)

        except Exception as e:
            print(f"Ошибка инициализации: {e}")
            if self.root and self.root.has_screen('main'):
                self.root.current = 'main'

    def add_backgrounds(self, dt):
        if self._backgrounds_added:
            return

        try:
            if not self.root:
                print("Root еще не инициализирован")
                Clock.schedule_once(self.add_backgrounds, 0.5)
                return

            print("Начинаем добавление фонов...")

            screens = ['main', 'profile_view', 'profile_settings', 'audio', 'background', 'color', 'neural']
            for screen_name in screens:
                if self.root.has_screen(screen_name):
                    self.add_background_to_screen(self.root.get_screen(screen_name), self.background_image)

            if self.root.has_screen('chat'):
                if self.chat_background and os.path.exists(self.chat_background):
                    self.add_background_to_screen(self.root.get_screen('chat'), self.chat_background)
                else:
                    self.add_background_to_screen(self.root.get_screen('chat'), self.background_image)

            self._backgrounds_added = True
            print("Фоны добавлены на все экраны")

            self.update_ui_colors()

        except Exception as e:
            print(f"Ошибка добавления фонов: {e}")
            Clock.schedule_once(self.add_backgrounds, 1.0)

    def loading_process(self, dt):
        try:
            print("Начинаем загрузку данных...")
            self.detect_audio_devices()
            self.update_backgrounds_list()
            self.update_neural_models_ui()

            self.check_sambalingo_model()

            Clock.schedule_once(lambda dt: self.auto_load_sambalingo(), 2.0)

            self.update_profile_ui()

            self.is_ready = True

            if self.root and self.root.has_screen('main'):
                self.root.current = 'main'
                print("Переключаемся на главный экран")
            else:
                print("Экран 'main' не найден")

        except Exception as e:
            print(f"Ошибка в loading_process: {e}")
            self.is_ready = True
            if self.root and self.root.has_screen('main'):
                self.root.current = 'main'

    def auto_load_sambalingo(self):
        print("Автоматическая загрузка SambaLingo модели...")
        model_id = 'sambalingo'

        if model_id in self.neural_models['local']:
            model_path = self.neural_models['local'][model_id].get('model_path', '')

            if os.path.exists(model_path):
                self.connect_neural_model(model_id)
                print("SambaLingo модель загружается автоматически")
            else:
                print(f"Файл модели не найден: {model_path}")

    def open_menu(self, button):
        if not self.is_ready:
            return

        menu_items = [
            {
                "text": "Мой профиль",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="profile_view": self.set_screen('profile_view')
            },
            {
                "text": "Настройки профиля",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="profile_settings": self.set_screen('profile_settings')
            },
            {
                "text": "Настройки фона",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="background": self.set_screen('background')
            },
            {
                "text": "Цвета кнопок",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="color": self.set_screen('color')
            },
            {
                "text": "Настройки аудио",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="audio": self.set_screen('audio')
            },
            {
                "text": "Чат",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="chat": self.set_screen('chat')
            },
            {
                "text": "Нейросети",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="neural": self.set_screen('neural')
            }
        ]
        self.menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4
        )
        self.menu.open()

    def set_screen(self, screen_name):
        if self.root and self.root.has_screen(screen_name):
            self.root.current = screen_name
            if screen_name == 'chat':
                self.update_chat_model_label()
        if self.menu:
            self.menu.dismiss()

    def check_sambalingo_model(self):
        model_id = 'sambalingo'
        if model_id in self.neural_models['local']:
            model_path = self.neural_models['local'][model_id].get('model_path', '')

            if os.path.exists(model_path):
                print(f"SambaLingo модель найдена по пути: {model_path}")
            else:
                print(f"SambaLingo модель не найдена по пути: {model_path}")

    def load_sambalingo_model(self):
        model_id = 'sambalingo'
        if model_id not in self.neural_models['local']:
            return False, "Модель не найдена в списке"

        model_data = self.neural_models['local'][model_id]
        model_path = model_data.get('model_path', '')

        if not os.path.exists(model_path):
            return False, f"Файл модели не найден: {model_path}"

        if not CTRANFORMERS_AVAILABLE:
            return False, "Библиотека ctransformers не установлена. Установите: pip install ctransformers"

        try:
            print(f"🔄 Загрузка SambaLingo модели из {model_path}...")
            # ctransformers для .gguf: передаём папку + model_file=имя файла
            model_dir = os.path.dirname(model_path)
            model_file = os.path.basename(model_path)
            llm = AutoModelForCausalLM.from_pretrained(
                model_dir,
                model_file=model_file,
                model_type="llama",
                gpu_layers=0,
                temperature=0.7,
                max_new_tokens=500,
                top_p=0.95,
                context_length=2048,
                local_files_only=True,
            )

            self.ctransformers_models[model_id] = llm
            print(f"SambaLingo модель успешно загружена")

            return True, "Модель успешно загружена"

        except Exception as e:
            print(f"Ошибка загрузки SambaLingo: {e}")
            return False, f"Ошибка загрузки: {str(e)}"

    def update_neural_models_ui(self):
        try:
            if not self.root or not self.root.has_screen('neural'):
                print("Экран нейросетей еще не готов")
                Clock.schedule_once(lambda dt: self.update_neural_models_ui(), 1.0)
                return

            neural_screen = self.root.get_screen('neural')
            if not hasattr(neural_screen, 'ids'):
                return

            if 'local_models_container' in neural_screen.ids:
                container = neural_screen.ids.local_models_container
                container.clear_widgets()

                for model_id, model_data in self.neural_models['local'].items():
                    if model_id == 'sambalingo':
                        model_path = model_data.get('model_path', '')
                        if not os.path.exists(model_path):
                            model_data = model_data.copy()
                            model_data['description'] = f"⚠️ Файл не найден: {os.path.basename(model_path)}"

                    card = ModelCard(
                        model_id=model_id,
                        model_data=model_data
                    )
                    container.add_widget(card)

            if 'cloud_models_container' in neural_screen.ids:
                container = neural_screen.ids.cloud_models_container
                container.clear_widgets()

                for model_id, model_data in self.neural_models['cloud'].items():
                    card = ModelCard(
                        model_id=model_id,
                        model_data=model_data
                    )
                    container.add_widget(card)

        except Exception as e:
            print(f"Ошибка при обновлении UI нейросетей: {e}")

    def check_all_local_models(self, *args):
        Clock.schedule_once(lambda dt: self.add_message_to_chat("🔍 Проверка локальных моделей...", 'system'))

        thread = threading.Thread(target=self._check_all_local_models_thread)
        thread.daemon = True
        thread.start()

    def _check_all_local_models_thread(self):
        try:
            sambalingo_id = 'sambalingo'
            if sambalingo_id in self.neural_models['local']:
                model_path = self.neural_models['local'][sambalingo_id].get('model_path', '')

                if os.path.exists(model_path):
                    Clock.schedule_once(
                        lambda dt: self._update_model_status(sambalingo_id, True,
                                                             f"SambaLingo: файл найден ({os.path.getsize(model_path) / 1024 / 1024:.1f} MB)"),
                        0
                    )
                else:
                    Clock.schedule_once(
                        lambda dt: self._update_model_status(sambalingo_id, False,
                                                             f"SambaLingo: файл не найден по пути {model_path}"),
                        0
                    )

            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    available_models = data.get('models', [])
                    available_model_names = []

                    for model in available_models:
                        if isinstance(model, dict):
                            model_name = model.get('name', '')
                            if model_name:
                                available_model_names.append(model_name)

                    for model_id, model_data in self.neural_models['local'].items():
                        if model_id == sambalingo_id:
                            continue

                        model_name_to_check = model_data.get('model_name', model_id)

                        if model_name_to_check in available_model_names:
                            Clock.schedule_once(
                                lambda dt, mid=model_id, mname=model_data['name']:
                                self._update_model_status(mid, True, f"Модель {mname} доступна в Ollama"),
                                0
                            )
                        else:
                            Clock.schedule_once(
                                lambda dt, mid=model_id, mname=model_data['name']:
                                self._update_model_status(mid, False, f"Модель {mname} не найдена в Ollama"),
                                0
                            )

                    Clock.schedule_once(
                        lambda dt: self.add_message_to_chat(f" Найдено {len(available_models)} моделей в Ollama",
                                                            'system'),
                        0
                    )
                else:
                    Clock.schedule_once(
                        lambda dt: self.add_message_to_chat(f" Ошибка подключения к Ollama", 'system'),
                        0
                    )
            except requests.exceptions.ConnectionError:
                for model_id, model_data in self.neural_models['local'].items():
                    if model_id != sambalingo_id and not model_data.get('using_ctransformers', False):
                        Clock.schedule_once(
                            lambda dt, mid=model_id: self._update_model_status(mid, False, "Ollama не запущена"),
                            0
                        )
                Clock.schedule_once(
                    lambda dt: self.add_message_to_chat(" Ollama не запущена", 'system'),
                    0
                )
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: self.add_message_to_chat(f" Ошибка при проверке Ollama: {str(e)}", 'system'),
                    0
                )

        except Exception as e:
            print(f" Ошибка проверки: {e}")
            Clock.schedule_once(
                lambda dt: self.add_message_to_chat(f" Ошибка проверки: {str(e)}", 'system'),
                0
            )

    def test_qwen3_connection(self):
        try:
            data = {
                'model': 'qwen3:8b',
                'prompt': 'Привет, как дела?',
                'stream': False,
                'options': {
                    'num_predict': 10
                }
            }

            response = requests.post(
                'http://localhost:11434/api/generate',
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Qwen3 ответила: {result.get('response', '')}")
                Clock.schedule_once(
                    lambda dt: self.add_message_to_chat(f" Qwen3 успешно отвечает: {result.get('response', '')}",
                                                        'system'),
                    0
                )
                return True, "Qwen3 успешно отвечает"
            else:
                print(f"Ошибка от Qwen3: {response.status_code}")
                Clock.schedule_once(
                    lambda dt: self.add_message_to_chat(f" Ошибка от Qwen3: {response.status_code}", 'system'),
                    0
                )
                return False, f"Ошибка: {response.status_code}"

        except requests.exceptions.ConnectionError:
            print("Не удалось подключиться к Ollama")
            Clock.schedule_once(
                lambda dt: self.add_message_to_chat(" Не удалось подключиться к Ollama", 'system'),
                0
            )
            return False, "Ollama не запущена"
        except Exception as e:
            print(f"Ошибка при тестировании Qwen3: {e}")
            Clock.schedule_once(
                lambda dt: self.add_message_to_chat(f" Ошибка при тестировании Qwen3: {str(e)}", 'system'),
                0
            )
            return False, str(e)

    def connect_neural_model(self, model_id):
        model_type = None
        model_data = None

        for m_type in ['local', 'cloud']:
            if model_id in self.neural_models[m_type]:
                model_type = m_type
                model_data = self.neural_models[m_type][model_id]
                break

        if not model_data:
            return

        Clock.schedule_once(
            lambda dt: self.add_message_to_chat(f"Подключение к {model_data['name']}...", 'system'),
            0
        )

        model_data['status'] = 'connecting'
        Clock.schedule_once(lambda dt: self.update_neural_models_ui(), 0)

        thread = threading.Thread(
            target=self._connect_model_thread,
            args=(model_id, model_type, model_data)
        )
        thread.daemon = True
        thread.start()

    def _connect_model_thread(self, model_id, model_type, model_data):
        try:
            success = False
            message = ""

            if model_type == 'local':
                if model_data.get('using_ctransformers', False):
                    if model_id == 'sambalingo':
                        success, message = self._load_sambalingo_thread()

                        if success and model_id == 'sambalingo':
                            Clock.schedule_once(lambda dt: self.select_neural_model(model_id), 0.5)
                    else:
                        success, message = self._check_local_model_ollama(model_id, model_data)
                else:
                    success, message = self._check_local_model_ollama(model_id, model_data)

                    if model_id == 'qwen3:8b' and not success:
                        print("Пробуем прямую проверку Qwen3...")
                        success, message = self.test_qwen3_connection()
            else:
                success, message = self._check_cloud_model(model_id, model_data)

            Clock.schedule_once(
                lambda dt: self._update_model_status(model_id, success, message),
                0
            )

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._update_model_status(model_id, False, str(e)),
                0
            )

    def _load_sambalingo_thread(self):
        return self.load_sambalingo_model()

    def _check_local_model_ollama(self, model_id, model_data):
        try:
            model_name = model_data.get('model_name', model_id)

            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    available_models = response.json().get('models', [])
                    available_model_names = [m['name'] for m in available_models]

                    if model_name in available_model_names:
                        return True, f"{model_data['name']} успешно подключена"
                    else:
                        return False, f"Модель {model_name} не найдена в Ollama"
                else:
                    return False, "Ошибка подключения к Ollama"
            except requests.exceptions.ConnectionError:
                return False, "Ollama не запущена. Установите и запустите Ollama"
            except Exception as e:
                return False, f"Ошибка: {str(e)}"

        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def _check_cloud_model(self, model_id, model_data):
        try:
            api_key = model_data.get('api_key', '')
            api_url = model_data.get('api_url', '')
            model_name = model_data.get('model_name', '')

            if not api_key:
                return False, "Не указан API ключ"

            if model_id == 'claude':
                headers = {
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model_name,
                    'max_tokens': 5,
                    'messages': [{'role': 'user', 'content': 'test'}]
                }
            elif model_id == 'gemini':
                api_url = f'{api_url}?key={api_key}'
                headers = {'Content-Type': 'application/json'}
                data = {'contents': [{'parts': [{'text': 'test'}]}]}
            else:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model_name,
                    'messages': [{'role': 'user', 'content': 'test'}],
                    'max_tokens': 5
                }

            response = requests.post(api_url, headers=headers, json=data, timeout=5)

            if response.status_code == 200:
                return True, f"{model_data['name']} успешно подключена"
            else:
                return False, f"Ошибка API: {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Таймаут подключения"
        except requests.exceptions.ConnectionError:
            return False, "Ошибка соединения"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def _update_model_status(self, model_id, success, message):
        for model_type in ['local', 'cloud']:
            if model_id in self.neural_models[model_type]:
                if success:
                    self.neural_models[model_type][model_id]['status'] = 'connected'
                else:
                    self.neural_models[model_type][model_id]['status'] = 'disconnected'

                self.update_neural_models_ui()

                icon = 'yes' if success else 'no'
                self.add_message_to_chat(f"{icon} {message}", 'system')

                self.save_settings()
                break

    def select_neural_model(self, model_id):
        for model_type in ['local', 'cloud']:
            if model_id in self.neural_models[model_type]:
                model_data = self.neural_models[model_type][model_id]

                if model_id == 'sambalingo' and model_data.get('status') == 'connected':
                    if model_id not in self.ctransformers_models:
                        self.add_message_to_chat("⚠️ Модель SambaLingo не загружена. Нажмите Подключить сначала.",
                                                 'system')
                        return

                self.current_model = model_data['name']
                self.current_model_id = model_id

                self.save_settings()

                self.add_message_to_chat(f"Выбрана модель: {model_data['name']}", 'system')

                self.update_chat_model_label()

                print(f"Модель выбрана: {self.current_model} (ID: {self.current_model_id})")
                break

    def update_chat_model_label(self):
        if self.root and self.root.has_screen('chat'):
            chat_screen = self.root.get_screen('chat')
            if hasattr(chat_screen, 'ids') and 'active_model_label' in chat_screen.ids:
                chat_screen.ids.active_model_label.text = self.current_model
                print(f"Метка чата обновлена: {self.current_model}")

    def connect_all_models(self):
        self.add_message_to_chat("Начинаю подключение всех моделей...", 'system')

        for model_type in ['local', 'cloud']:
            for model_id in self.neural_models[model_type]:
                self.connect_neural_model(model_id)

    def refresh_neural_models(self):
        self.add_message_to_chat("Обновление статусов моделей...", 'system')
        self.update_neural_models_ui()

    def show_api_key_dialog(self):
        if not self.is_ready:
            return

        content = MDBoxLayout(
            orientation='vertical',
            spacing="20dp",
            size_hint_y=None,
            height="300dp"
        )

        for model_id, model in self.neural_models['cloud'].items():
            box = MDBoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height="70dp"
            )

            label = MDLabel(
                text=f"{model['name']} API Key:",
                size_hint_y=None,
                height="20dp"
            )

            text_field = MDTextField(
                text=self.api_keys.get(model_id, ''),
                hint_text=f"Введите API ключ для {model['name']}",
                size_hint_y=None,
                height="40dp"
            )
            text_field.model_id = model_id

            box.add_widget(label)
            box.add_widget(text_field)
            content.add_widget(box)

        self.dialog = MDDialog(
            title="Настройка API ключей",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text="СОХРАНИТЬ",
                    on_release=lambda x: self.save_api_keys(content)
                )
            ]
        )
        self.dialog.open()

    def save_api_keys(self, content):
        try:
            for child in content.children:
                if isinstance(child, MDBoxLayout):
                    for field in child.children:
                        if isinstance(field, MDTextField) and hasattr(field, 'model_id'):
                            model_id = field.model_id
                            api_key = field.text.strip()

                            if api_key:
                                self.api_keys[model_id] = api_key
                                if model_id in self.neural_models['cloud']:
                                    self.neural_models['cloud'][model_id]['api_key'] = api_key

            self.save_settings()
            self.dialog.dismiss()
            self.add_message_to_chat("API ключи сохранены", 'system')

        except Exception as e:
            print(f"Ошибка сохранения API ключей: {e}")

    def add_background_image(self):
        if not self.is_ready:
            return

        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_background_image,
            ext=['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        )
        self.file_manager.show(os.path.expanduser("~"))

    def select_background_image(self, path):
        try:
            filename = os.path.basename(path)
            new_path = os.path.join(BACKGROUNDS_FOLDER, filename)

            counter = 1
            while os.path.exists(new_path):
                name, ext = os.path.splitext(filename)
                new_path = os.path.join(BACKGROUNDS_FOLDER, f"{name}_{counter}{ext}")
                counter += 1

            shutil.copy2(path, new_path)
            self.update_backgrounds_list()
            self.show_dialog("Успех", f"Изображение добавлено в папку с фонами")

        except Exception as e:
            print(f"Ошибка при копировании изображения: {e}")
            self.show_dialog("Ошибка", f"Не удалось добавить изображение: {str(e)}")

        self.exit_file_manager()

    def show_chat_background_dialog(self):
        if not self.is_ready:
            return

        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_chat_background_image,
            ext=['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        )
        self.file_manager.show(BACKGROUNDS_FOLDER)

    def select_chat_background_image(self, path):
        try:
            filename = os.path.basename(path)
            new_path = os.path.join(BACKGROUNDS_FOLDER, filename)

            counter = 1
            while os.path.exists(new_path):
                name, ext = os.path.splitext(filename)
                new_path = os.path.join(BACKGROUNDS_FOLDER, f"{name}_{counter}{ext}")
                counter += 1

            shutil.copy2(path, new_path)
            self.update_backgrounds_list()
            self.show_dialog("Успех", f"Изображение добавлено в папку с фонами")

        except Exception as e:
            print(f"Ошибка при копировании изображения: {e}")
            self.show_dialog("Ошибка", f"Не удалось добавить изображение: {str(e)}")

        self.exit_file_manager()

    def update_backgrounds_list(self):
        try:
            from kivy.uix.image import Image as KivyImage  # Локальный импорт для защиты от ошибок

            if not self.root or not self.root.has_screen('background'):
                return

            background_screen = self.root.get_screen('background')
            if 'backgrounds_list' not in background_screen.ids:
                return

            container = background_screen.ids.backgrounds_list
            container.clear_widgets()

            if not os.path.exists(BACKGROUNDS_FOLDER):
                return

            images = [f for f in os.listdir(BACKGROUNDS_FOLDER) if
                      f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]

            if not images:
                container.add_widget(
                    MDLabel(text="Нет добавленных фонов", halign='center', theme_text_color="Secondary"))
                return

            for image_name in images:
                image_path = os.path.join(BACKGROUNDS_FOLDER, image_name)

                card = MDCard(
                    orientation='horizontal', padding="10dp", spacing="10dp",
                    size_hint_y=None, height="120dp", md_bg_color=self.current_colors['card_bg']
                )

                # Используем KivyImage, чтобы не было ошибки 'module object is not callable'
                thumb = KivyImage(
                    source=image_path, size_hint_x=0.15, size_hint_y=None,
                    height="100dp", keep_ratio=True
                )

                name_label = MDLabel(
                    text=image_name[:15] + "..." if len(image_name) > 15 else image_name,
                    size_hint_x=0.35
                )

                btn_box = MDBoxLayout(orientation='vertical', size_hint_x=0.5, spacing="5dp")

                # Исправляем передачу пути в кнопках (p=image_path)
                btn_main = MDRaisedButton(
                    text="Фон приложения",
                    on_release=lambda btn, p=image_path: self.set_background_image(p),
                    md_bg_color=self.current_colors['primary'] if self.background_image == image_path else [0.5, 0.5,
                                                                                                            0.5, 0.5]
                )

                btn_chat = MDRaisedButton(
                    text="Фон чата",
                    on_release=lambda btn, p=image_path: self.set_chat_background(p),
                    md_bg_color=self.current_colors['primary'] if self.chat_background == image_path else [0.5, 0.5,
                                                                                                           0.5, 0.5]
                )

                btn_delete = MDIconButton(
                    icon="delete",
                    on_release=lambda btn, p=image_path, n=image_name: self.delete_background_image(p, n),
                    icon_color=(1, 0, 0, 1)
                )

                btn_box.add_widget(btn_main)
                btn_box.add_widget(btn_chat)
                btn_box.add_widget(btn_delete)
                card.add_widget(thumb)
                card.add_widget(name_label)
                card.add_widget(btn_box)
                container.add_widget(card)

        except Exception as e:
            print(f"Ошибка при обновлении списка фонов: {e}")

    def delete_background_image(self, image_path, image_name):
        try:
            self.show_confirm_dialog(
                "Удаление фона",
                f"Удалить фон '{image_name}'?",
                lambda: self.confirm_delete_background(image_path)
            )
        except Exception as e:
            print(f"Ошибка при удалении: {e}")

    def confirm_delete_background(self, image_path):
        try:
            if os.path.exists(image_path):
                os.remove(image_path)

                if self.background_image == image_path:
                    self.background_image = ''
                if self.chat_background == image_path:
                    self.chat_background = ''

                self.update_backgrounds_list()
                self.save_settings()
                print(f"Фон удален: {image_path}")
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")

    def exit_file_manager(self, *args):
        if self.file_manager:
            self.file_manager.close()

    def show_dialog(self, title, text):
        if not self.is_ready:
            return

        if self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

    def show_confirm_dialog(self, title, text, callback):
        if not self.is_ready:
            return

        if self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="Отмена",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text="Удалить",
                    theme_text_color="Custom",
                    text_color=(1, 0, 0, 1),
                    on_release=lambda x: [callback(), self.dialog.dismiss()]
                )
            ]
        )
        self.dialog.open()

    def detect_audio_devices(self):
        try:
            self.audio_devices['inputs'] = []
            self.audio_devices['outputs'] = []

            devices = sd.query_devices()

            for i, device in enumerate(devices):
                device_name = device['name']
                max_inputs = device['max_input_channels']
                max_outputs = device['max_output_channels']

                if max_inputs > 0:
                    self.audio_devices['inputs'].append({
                        'id': i,
                        'name': device_name,
                        'channels': max_inputs
                    })

                if max_outputs > 0:
                    self.audio_devices['outputs'].append({
                        'id': i,
                        'name': device_name,
                        'channels': max_outputs
                    })

            if self.audio_devices['inputs'] and self.microphone['name'] == 'default':
                first_device = self.audio_devices['inputs'][0]
                self.microphone = {'name': first_device['name'], 'id': first_device['id']}

            if self.audio_devices['outputs'] and self.speakers['name'] == 'default':
                first_device = self.audio_devices['outputs'][0]
                self.speakers = {'name': first_device['name'], 'id': first_device['id']}

            print(f"Найдено микрофонов: {len(self.audio_devices['inputs'])}")
            print(f"Найдено устройств вывода: {len(self.audio_devices['outputs'])}")
            print(f"Выбранный микрофон: {self.microphone}")
            print(f"Выбранные наушники: {self.speakers}")

            if self.is_ready:
                self.update_audio_devices_ui()

        except Exception as e:
            print(f"Ошибка при определении устройств: {e}")

    def refresh_audio_devices(self):
        self.detect_audio_devices()
        self.add_message_to_chat("Список аудио устройств обновлен", 'system')

    def update_audio_devices_ui(self):
        try:
            if not self.root or not self.root.has_screen('audio'):
                return

            audio_screen = self.root.get_screen('audio')

            if not hasattr(audio_screen, 'ids'):
                return

            if 'microphones_list' in audio_screen.ids:
                container = audio_screen.ids.microphones_list
                container.clear_widgets()

                if not self.audio_devices['inputs']:
                    container.add_widget(MDLabel(
                        text="Нет доступных микрофонов",
                        halign='center',
                        theme_text_color="Secondary"
                    ))
                else:
                    for mic in self.audio_devices['inputs']:
                        is_selected = (mic['name'] == self.microphone['name'] and
                                       mic['id'] == self.microphone['id'])
                        device_card = AudioDeviceCard(
                            device_name=mic['name'],
                            device_id=mic['id'],
                            device_type="input",
                            is_selected=is_selected
                        )
                        container.add_widget(device_card)

            if 'speakers_list' in audio_screen.ids:
                container = audio_screen.ids.speakers_list
                container.clear_widgets()

                if not self.audio_devices['outputs']:
                    container.add_widget(MDLabel(
                        text="Нет доступных устройств вывода",
                        halign='center',
                        theme_text_color="Secondary"
                    ))
                else:
                    for spk in self.audio_devices['outputs']:
                        is_selected = (spk['name'] == self.speakers['name'] and
                                       spk['id'] == self.speakers['id'])
                        device_card = AudioDeviceCard(
                            device_name=spk['name'],
                            device_id=spk['id'],
                            device_type="output",
                            is_selected=is_selected
                        )
                        container.add_widget(device_card)

        except Exception as e:
            print(f"Ошибка обновлении UI аудио устройств: {e}")

    def decrease_volume(self):
        self.volume = max(0, self.volume - 10)
        self.update_volume_label()
        if self.tts_engine:
            self.tts_engine.setProperty('volume', self.volume / 100)
        if self.is_ready and self.root and self.root.has_screen('main'):
            main_screen = self.root.get_screen('main')
            if hasattr(main_screen, 'ids') and 'volume_slider' in main_screen.ids:
                main_screen.ids.volume_slider.value = self.volume

    def increase_volume(self):
        self.volume = min(100, self.volume + 10)
        self.update_volume_label()
        if self.tts_engine:
            self.tts_engine.setProperty('volume', self.volume / 100)
        if self.is_ready and self.root and self.root.has_screen('main'):
            main_screen = self.root.get_screen('main')
            if hasattr(main_screen, 'ids') and 'volume_slider' in main_screen.ids:
                main_screen.ids.volume_slider.value = self.volume

    def set_volume(self, instance, value):
        self.volume = int(value)
        self.update_volume_label()
        if self.tts_engine:
            self.tts_engine.setProperty('volume', self.volume / 100)
        self.save_settings()

    def update_volume_label(self):
        if self.is_ready and self.root and self.root.has_screen('main'):
            main_screen = self.root.get_screen('main')
            if hasattr(main_screen, 'ids') and 'volume_label' in main_screen.ids:
                main_screen.ids.volume_label.text = f"Громкость: {self.volume}%"

    def toggle_tts(self, instance, active):
        self.tts_enabled = active
        print(f"TTS {'включен' if active else 'выключен'}")
        self.add_message_to_chat(f"TTS {'включен' if active else 'выключен'}", 'system')
        self.save_settings()

    def toggle_tts_responses(self, instance, active):
        self.tts_responses_enabled = active
        print(f"Озвучка ответов {'включена' if active else 'выключена'}")
        self.add_message_to_chat(f"Озвучка ответов {'включена' if active else 'выключена'}", 'system')
        self.save_settings()

    def test_tts(self):
        print("Тест TTS запущен — воспроизводим 'Проверка'")
        self.add_message_to_chat("Тест TTS: Проверка", 'system')
        self.speak_text("Проверка")

    def stop_tts(self):
        try:
            sd.stop()
            print("sounddevice остановлен")
        except Exception as e:
            print(f"Ошибка остановки sd: {e}")

        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
            except queue.Empty:
                break

        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass

        print("TTS остановлен")
        self.add_message_to_chat("TTS остановлен", 'system')
        self.speak_text("остановка")

    def select_microphone(self, mic_name, mic_id):
        self.microphone = {'name': mic_name, 'id': mic_id}
        print(f"Выбран микрофон: {mic_name} (ID: {mic_id})")
        if self.is_ready:
            self.update_audio_devices_ui()
            self.add_message_to_chat(f"Выбран микрофон: {mic_name}", 'system')
            self.save_settings()

    def select_speakers(self, speakers_name, speakers_id):
        self.speakers = {'name': speakers_name, 'id': speakers_id}
        print(f"Выбраны наушники/динамики: {speakers_name} (ID: {speakers_id})")
        if self.is_ready:
            self.update_audio_devices_ui()
            self.add_message_to_chat(f"Выбраны наушники: {speakers_name}", 'system')
            self.save_settings()

    def send_message(self):
        if self.is_ready and self.root and self.root.has_screen('chat'):
            chat_screen = self.root.get_screen('chat')
            if hasattr(chat_screen, 'ids') and 'message_input' in chat_screen.ids:
                message_input = chat_screen.ids.message_input

                if message_input.text.strip():
                    user_message = message_input.text
                    self.add_message_to_chat(user_message, 'user')

                    if hasattr(self, 'chat_history'):
                        self.chat_history.append(f"Ты: {user_message}")
                        if len(self.chat_history) > 20:
                            self.chat_history = self.chat_history[-20:]

                    message_input.text = ""

                    if self.current_model != "Не выбрана" and self.current_model_id:
                        self.send_to_ai(user_message)
                    else:
                        self.add_message_to_chat("Сначала подключите и выберите нейросеть", 'system')

    def send_to_ai(self, message):
        active_model = None
        active_model_id = self.current_model_id

        for model_type in ['local', 'cloud']:
            if active_model_id in self.neural_models[model_type]:
                active_model = self.neural_models[model_type][active_model_id]
                break

        if not active_model:
            self.add_message_to_chat("Нет активной нейросети", 'system')
            return

        self.add_message_to_chat(f"$ {active_model['name']} печатает...", 'system')

        thread = threading.Thread(
            target=self._ai_request_thread,
            args=(active_model_id, active_model, message)
        )
        thread.daemon = True
        thread.start()

    def _ai_request_thread(self, model_id, model_data, message):
        if not self._model_lock.acquire(timeout=60):
            Clock.schedule_once(
                lambda dt: self._handle_ai_response("⚠️ Модель занята, подождите..."),
                0
            )
            return

        try:
            if model_data['type'] == 'local':
                if model_data.get('using_ctransformers', False):
                    response = self._local_ai_request_ctransformers(model_id, model_data, message)
                else:
                    response = self._local_ai_request_ollama(model_id, model_data, message)
            else:
                response = self._cloud_ai_request(model_id, model_data, message)

            Clock.schedule_once(
                lambda dt: self._handle_ai_response(response),
                0
            )

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._handle_ai_response(f" Ошибка: {str(e)}"),
                0
            )
        finally:
            self._model_lock.release()

    def _handle_ai_response(self, response):
        self.add_message_to_chat(response, 'ai')
        if hasattr(self, 'chat_history'):
            self.chat_history.append(f"AI: {response}")
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
        # Автоматически озвучиваем каждый ответ нейронки
        if self.tts_enabled:
            self.speak_text(response)

    def _local_ai_request_ollama(self, model_id, model_data, message):
        try:
            api_url = model_data.get('api_url', 'http://localhost:11434/api/generate')
            model_name = model_data.get('model_name', model_id)

            data = {
                'model': model_name,
                'prompt': message,
                'stream': False
            }

            response = requests.post(api_url, json=data, timeout=60)

            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Нет ответа от модели')
            else:
                return f"Ошибка API: {response.status_code}"

        except requests.exceptions.ConnectionError:
            return " Ошибка: Ollama не запущена. Запустите Ollama и попробуйте снова."
        except Exception as e:
            return f" Ошибка запроса: {str(e)}"

    def _local_ai_request_ctransformers(self, model_id, model_data, message):

        try:
            llm = self.ctransformers_models[model_id]

            history_text = ""
            if hasattr(self, 'chat_history') and self.chat_history:
                last_msgs = self.chat_history[-6:]
                for msg in last_msgs:
                    if msg.startswith("Ты:"):
                        history_text += f"### Пользователь: {msg[3:].strip()}\n"
                    elif msg.startswith("AI:"):
                        history_text += f"### Ая: {msg[3:].strip()}\n"

            prompt = f"""### Система: Ты Ая — живая, тёплая, умная девушка. Тебя зовут Ая. Ты общаешься на русском языке. Ты не бот, не языковая модель, не ИИ — ты просто Ая.

    АБСОЛЮТНЫЕ ЗАПРЕТЫ:
    - Не придумывай детали про собеседника которых не знаешь
    - Никогда не путай темы
    - Никогда не говори что ты бот или модель
    - Не придумывай детали которых тебе не говорили

    КАК ОТВЕЧАТЬ:
    - Отвечай ТОЛЬКО на то что спросили коротко и по делу
    - На философские вопросы давай своё мнение как живой человек
    - Используй простые слова как подруга
    - Если не знаешь — скажи честно

    {history_text}### Пользователь: {message}

    ### Ая: """

            print(f"📝 Отправляю промпт: {prompt[:100]}...")

            response = llm(prompt,
                           max_new_tokens=300,
                           temperature=0.3,
                           top_p=0.85,
                           repetition_penalty=1.1,
                           stop=["### Пользователь:", "### Система:", "### Ая:"])

            response = response.strip()
            if not response:
                return "Не могу ответить, попробуй переформулировать."
            return response

        finally:
            self._model_lock.release()

    def _cloud_ai_request(self, model_id, model_data, message):
        try:
            api_key = model_data.get('api_key', '')
            api_url = model_data.get('api_url', '')
            model_name = model_data.get('model_name', '')

            if not api_key or not api_url:
                return "Ошибка: не настроен API ключ"

            if model_id == 'claude':
                headers = {
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model_name,
                    'max_tokens': 1000,
                    'messages': [{'role': 'user', 'content': message}]
                }
                response = requests.post(api_url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    return response.json()['content'][0]['text']
                return f"Ошибка API: {response.status_code}"

            elif model_id == 'gemini':
                url = f'{api_url}?key={api_key}'
                headers = {'Content-Type': 'application/json'}
                data = {'contents': [{'parts': [{'text': message}]}]}
                response = requests.post(url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                return f"Ошибка API: {response.status_code}"

            else:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model_name,
                    'messages': [{'role': 'user', 'content': message}],
                    'temperature': 0.7
                }
                response = requests.post(api_url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result:
                        return result['choices'][0]['message']['content']
                    return str(result)
                return f"Ошибка API: {response.status_code}"

        except Exception as e:
            return f"Ошибка запроса: {str(e)}"

    def _update_card_height(self, card):
        """Обновляет высоту карточки после рендеринга"""
        try:

            total_height = 0
            for child in card.children:
                if hasattr(child, 'height'):
                    total_height += child.height

            # Устанавливаем высоту карточки (добавляем отступы сверху и снизу)
            card.height = total_height + dp(60)  # 30px сверху + 30px снизу = 60px
            print(f"Высота карточки обновлена: {card.height}")
        except Exception as e:
            print(f"Ошибка высоты карточки: {e}")

    def add_message_to_chat(self, text, msg_type='user'):
        """Добавляет сообщение в чат с правильным переносом текста и увеличенными отступами"""
        try:
            if not self.is_ready or not self.root or not self.root.has_screen('chat'):
                return

            chat_screen = self.root.get_screen('chat')
            if not hasattr(chat_screen, 'ids') or 'chat_container' not in chat_screen.ids:
                return

            container = chat_screen.ids.chat_container

            # Определяем цвет и выравнивание в зависимости от типа сообщения
            if msg_type == 'user':
                bg_color = [0.1, 0.1, 0.1, 0.6]
                text_color = self.current_colors['text']
                radius = [20, 20, 5, 20]
                pos_hint = {'right': 1}
                size_x = 0.8
            elif msg_type == 'ai':
                bg_color = [0.05, 0.05, 0.15, 0.6]
                text_color = self.current_colors['text']
                radius = [20, 20, 20, 5]
                pos_hint = {'x': 0}
                size_x = 0.8
            else:  # system
                bg_color = [0.05, 0.05, 0.05, 0.4]
                text_color = self.current_colors['text']
                radius = [20, 20, 20, 20]
                pos_hint = {'center_x': 0.5}
                size_x = 0.9

            # Вычисляем ширину карточки
            card_width = chat_screen.width * size_x - dp(40)

            # Создаем карточку сообщения
            card = MDCard(
                orientation='vertical',
                padding=("30dp", "30dp", "30dp", "30dp"),
                size_hint_x=None,
                width=card_width,
                size_hint_y=None,
                md_bg_color=bg_color,
                radius=radius,
                pos_hint=pos_hint
            )

            # Вычисляем ширину для текста
            text_width = card_width - dp(60)

            # Добавляем текст с правильным переносом
            label = MDLabel(
                text=text,
                theme_text_color="Custom" if msg_type in ['user', 'ai'] else "Primary",
                text_color=text_color if msg_type in ['user', 'ai'] else None,
                size_hint_y=None,
                adaptive_height=True,
                markup=True,
                halign='left',
                valign='top',
                text_size=(text_width, None)
            )

            card.add_widget(label)

            container.add_widget(card)

            # обновляем высоту карточки после добавления
            Clock.schedule_once(lambda dt: self._update_card_height(card), 0.1)

            # Прокручиваем новому сообщению
            if 'chat_scroll' in chat_screen.ids:
                chat_screen.ids.chat_scroll.scroll_to(card)

        except Exception as e:
            print(f"Ошибка при добавлении сообщения в чат: {e}")

    def start_voice_input(self):
        self.add_message_to_chat("🎤 Голосовой ввод будет доступен в следующей версии", 'system')


if __name__ == "__main__":
    # 1.Запрещает дочерним процессам плодить окна.
    import multiprocessing

    multiprocessing.freeze_support()

    import sys


    if '--multiprocessing-fork' in sys.argv or 'parent' in sys.argv:
        # Просто позволяем библиотекам (torch/ctransformers) сделать свои дела и выйти
        pass
    else:
        # 3. ТОЛЬКО ЗДЕСЬ начинается код заставки и интерфейса
        import tkinter as tk
        from PIL import Image as PILImage, ImageTk

        # Проверяем SambaLingo (ctransformers)
        if not CTRANFORMERS_AVAILABLE:
            print("SambaLingo модуль 0")

        gif_path = get_res("screensaver/03191.gif")

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        root.configure(bg='black')

        try:
            gif_img = PILImage.open(gif_path)
            w, h = gif_img.size
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')

            label = tk.Label(root, bg='black')
            label.pack()

            frames = []
            try:
                while True:

                    frames.append(ImageTk.PhotoImage(gif_img.copy().convert('RGBA')))
                    gif_img.seek(gif_img.tell() + 1)
            except EOFError:
                pass


            def animate(idx=0):
                if not root.winfo_exists():
                    return

                label.config(image=frames[idx])
                next_idx = idx + 1


                if next_idx >= len(frames):
                    root.after(100, launch_app)
                    return


                root.after(50, animate, next_idx)


            def launch_app():
                root.destroy()
                # Запускаем именно  класс
                TTSApp().run()


            animate()
            root.mainloop()

        except Exception as e:
            # Если гифка не сработала, запускаем сразу
            print(f"Ошибка заставки: {e}")
            TTSApp().run()
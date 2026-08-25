# -*- coding: cp1251 -*-
import ollama
import paho.mqtt.publish as publish
import argparse

import pygetwindow as gw
import pyautogui

import threading
import time

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from gigachat.models import Function

import json

# Замените строку ниже на ваш реальный ключ авторизации из Сбер Студии
MY_AUTH_KEY = "..."

PROMPT = 'Ты робот. Используя инструменты: выстрели. Опиши, что ты видишь (приложенный файл)' #, потом иди вперед 20 см, потом повернись направо на 90 градусов, шагни назад на 20 см потом обернись назад'
# PROMPT = 'Ты робот. Опиши, что на картинке. Используя инструменты: выстрели'
parser = argparse.ArgumentParser(description="Управление роботом")
parser.add_argument("--command", type=str, default=PROMPT, help="Команда роботу")

args = parser.parse_args()
PROMPT = args.command

# Настройки брокера
MQTT_BROKER = "localhost"  # Публичный тестовый брокер
MQTT_PORT = 1883
MQTT_TOPIC = "nodered/commands"

# Находим окно по части названия (например, 'Notepad' или 'Блокнот')
window_title = "e2eSoft iVCam"
windows = gw.getWindowsWithTitle(window_title)


def camera():
    if windows:
        win = windows[0]
        # Получаем координаты и размеры
        left, top, width, height = win.left, win.top, win.width, win.height
        # Делаем скриншот конкретной области экрана
        screenshot = pyautogui.screenshot(region=(left + 8, top + 31, width - 16, height - 95))
        # Сохраняем файл
        screenshot.save("d:/wificam.jpg")
        # print("Скриншот успешно сохранен!")
    else:
        print(f"Окно с названием '{window_title}' не найдено.")


def repeated_task():
    while True:
        camera()
        time.sleep(1)  # Пауза на 1 секунду

# Создаём и запускаем поток
thread = threading.Thread(target=repeated_task, name="RepeatingThread")
thread.start()


# 1. Объясняем функцию с помощью аннотаций и docstring
def move_forward(cm: int) -> str:
    """Отправляет команду на движение вперед на указанное число сантиметров."""
    publish.single(
        topic=MQTT_TOPIC,
        payload="MOVE_FORWARD " + str(cm),
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
    return f"MOVE_FORWARD {cm}"

def move_backward(cm: int) -> str:
    """Отправляет команду на движение назад на указанное число сантиметров."""
    publish.single(
        topic=MQTT_TOPIC,
        payload="MOVE_BACKWARD " + str(cm),
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
    return f"MOVE_BACKWARD {cm}"

def turn_left(degrees: int) -> str:
    """Отправляет команду на поворот налево на указанное число градусов."""
    publish.single(
        topic=MQTT_TOPIC,
        payload="TURN_LEFT " + str(degrees),
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
    return f"TURN_LEFT {degrees}"

def turn_right(degrees: int) -> str:
    """Отправляет команду на поворот направо на указанное число градусов."""
    publish.single(
        topic=MQTT_TOPIC,
        payload="TURN_RIGHT " + str(degrees),
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
    return f"TURN_RIGHT {degrees}"

def fire() -> str:
    """Отправляет команду на выстрел/действие."""
    publish.single(
        topic=MQTT_TOPIC,
        payload="FIRE",
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
    return "FIRE"

# tools = [move_forward, move_backward, turn_left, turn_right, fire,]
# Описываем функции в формате, который понимает GigaChat SDK
tools = [
    Function(
        name="move_forward",
        description="Отправляет команду на движение вперед на указанное число сантиметров.",
        parameters={
            "type": "object",
            "properties": {
                "cm": {"type": "integer", "description": "Расстояние в сантиметрах"}
            },
            "required": ["cm"]
        }
    ),
    Function(
        name="move_backward",
        description="Отправляет команду на движение назад на указанное число сантиметров.",
        parameters={
            "type": "object",
            "properties": {
                "cm": {"type": "integer", "description": "Расстояние в сантиметрах"}
            },
            "required": ["cm"]
        }
    ),
    Function(
        name="turn_left",
        description="Отправляет команду на поворот налево на указанное число градусов.",
        parameters={
            "type": "object",
            "properties": {
                "degrees": {"type": "integer", "description": "Угол поворота в градусах"}
            },
            "required": ["degrees"]
        }
    ),
    Function(
        name="turn_right",
        description="Отправляет команду на поворот направо на указанное число градусов.",
        parameters={
            "type": "object",
            "properties": {
                "degrees": {"type": "integer", "description": "Угол поворота в градусах"}
            },
            "required": ["degrees"]
        }
    ),
    Function(
        name="fire",
        description="Отправляет команду на выстрел или действие.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
]

tool_map = {
    move_forward.__name__: move_forward,
    move_backward.__name__: move_backward,
    turn_left.__name__: turn_left,
    turn_right.__name__: turn_right,
    fire.__name__: fire,
}

# Инициализируем клиент напрямую через credentials
with GigaChat(credentials=MY_AUTH_KEY, verify_ssl_certs=False) as client:
    # 1. Загружаем изображение
    with open("D:/wificam.jpg", "rb") as f:
        uploaded_file = client.upload_file(f, purpose="general")

    file_id = uploaded_file.id_
    print(f"Файл успешно загружен. ID: {file_id}")

    # 1. Создаем стартовую историю сообщений
    messages_history = [
        Messages(
            role=MessagesRole.USER,
            content=PROMPT,
            attachments=[file_id]  # Прикрепляем ID загруженного фото
        )
    ]

    # Флаг для работы цикла перебора
    continue_execution = True

    while continue_execution:
        # Формируем запрос к нейросети с актуальной историей
        print("PROMPT: ", messages_history)
        payload = Chat(
            model="GigaChat-2-Pro",
            messages=messages_history,
            functions=tools
        )

        # Получаем ответ от GigaChat
        response = client.chat(payload)
        message = response.choices[0].message

        # Обязательно добавляем ответ модели в историю, чтобы она помнила свои действия
        messages_history.append(message)

        # Проверяем, вызвала ли модель инструмент
        if message.function_call:
            name = message.function_call.name
            args = message.function_call.arguments

            # Распаковываем аргументы, если они пришли строкой
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}

            print(f"--- Выполняется инструмент: {name} ({args}) ---")

            if name in tool_map:
                # Вызываем функцию из вашего маппинга
                fn = tool_map[name]
                result = fn(**args)
                print(f"Результат работы функции {name}: {result}")

                json_result = json.dumps({"status": "success", "return_value": result}, ensure_ascii=False)

                # Отправляем результат выполнения обратно модели [3]
                messages_history.append(
                    Messages(
                        role=MessagesRole.FUNCTION,
                        name=name,
                        content=json_result
                    )
                )
            else:
                print(f"Ошибка: Функция {name} отсутствует в tool_map.")
                # Сообщаем модели об ошибке, чтобы она не зациклилась
                messages_history.append(
                    Messages(
                        role=MessagesRole.FUNCTION,
                        name=name,
                        content="Error: function not found"
                    )
                )
        else:
            # Если function_call отсутствует, значит модель закончила перебор инструментов
            # и сформировала финальный текстовый ответ
            print("\n--- Все инструменты успешно выполнены! ---")
            print("Финальный ответ ИИ:", message.content)
            continue_execution = False

    # 4. Удаляем файл из хранилища после завершения всех шагов
    client.delete_file(file_id)
    print(f"Файл {file_id} успешно удален.")
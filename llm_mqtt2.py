# -*- coding: cp1251 -*-
import ollama
import paho.mqtt.publish as publish
import argparse

import pygetwindow as gw
import pyautogui

import threading
import time

#PROMPT = 'выстрели, потом иди вперед 100 см, потом повернись направо на 90 градусов, шагни назад на 20 см потом обернись'
parser = argparse.ArgumentParser(description="Управление роботом")
parser.add_argument("--command", type=str, default="выстрели, потом иди вперед 100 см, потом повернись направо на 90 градусов, шагни назад на 20 см потом обернись", help="Команда роботу")

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

print("PROMPT: ", PROMPT)


# 1. Объясняем функцию с помощью аннотаций и docstring
def move_forward(cm: int) -> str:
    # Отправка одного сообщения на движение вперед на указанное число шагов
    publish.single(
        topic=MQTT_TOPIC,
        payload="MOVE_FORWARD " + str(cm),  # Данные должны быть строкой или байтами
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
#    return f"MOVE_FORWARD {cm}"

def move_backward(cm: int) -> str:
    # Отправка одного сообщения на движение назад на указанное число шагов
    publish.single(
        topic=MQTT_TOPIC,
        payload="MOVE_BACKWARD " + str(cm),  # Данные должны быть строкой или байтами
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
#    return f"MOVE_BACKWARD {cm}"

def turn_left(degrees: int) -> str:
    # Отправка одного сообщения на поворот налево с указанием градусов поворота
    publish.single(
        topic=MQTT_TOPIC,
        payload="TURN_LEFT " + str(degrees),  # Данные должны быть строкой или байтами
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
#    return f"TURN_LEFT {degrees}"

def turn_right(degrees: int) -> str:
    # Отправка одного сообщения на поворот направо с указанием градусов поворота
    publish.single(
        topic=MQTT_TOPIC,
        payload="TURN_RIGHT " + str(degrees),  # Данные должны быть строкой или байтами
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
#    return f"TURN_RIGHT {degrees}"

def fire ():
    # Отправка одного сообщения на поворот направо с указанием градусов поворота
    publish.single(
        topic=MQTT_TOPIC,
        payload="FIRE",  # Данные должны быть строкой или байтами
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
#    return f"TURN_RIGHT {degrees}"

tools = [
    move_forward,
    move_backward,
    turn_left,
    turn_right,
    fire,
]

tool_map = {
    move_forward.__name__: move_forward,
    move_backward.__name__: move_backward,
    turn_left.__name__: turn_left,
    turn_right.__name__: turn_right,
    fire.__name__: fire,
}

# 2. Делаем запрос к модели с передачей инструмента
response = ollama.chat(
    model='qwen3.5:4b', #qwen2.5vl:3b
    messages=[{'role': 'user', 'content': PROMPT}],
    tools=tools, # Ollama автоматически сериализует функцию в схему
)

# 3. Проверяем, захотела ли модель вызвать инструмент
if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        name = tool_call.function.name
        args = tool_call.function.arguments
        fn = tool_map[name]
        result = fn(**args)
        # print("Результат работы функции:", result)
else:
    # Этот блок сработает, если tool_calls пустой (модель ответила текстом)
    print("Инструменты не использовались.")
    print("Ответ модели:", response.message.content)

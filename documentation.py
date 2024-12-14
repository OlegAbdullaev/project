# Импорт необходимых библиотек
import telebot  # Библиотека для работы с Telegram API
import folium  # Библиотека для визуализации карт
import os  # Модуль для работы с файловой системой
import time  # Модуль для работы с временными интервалами
import math  # Модуль для математических операций
import requests  # Библиотека для выполнения HTTP-запросов
from telebot import types  # Импортируем типы сообщений и клавиатур
from googletrans import Translator  # Библиотека для перевода текста
from selenium import webdriver  # Библиотека для управления браузером
from selenium.webdriver.support.ui import WebDriverWait  # Ожидание элементов на странице
from selenium.webdriver.chrome.service import Service  # Управление хром-драйвером
from selenium.webdriver.common.by import By  # Определение методов поиска элементов
from selenium.webdriver.chrome.options import Options  # Настройки для Chrome
from selenium.webdriver.support import expected_conditions as EC  # Ожидания с условиями
from apscheduler.schedulers.background import BackgroundScheduler  # Планировщик задач
from datetime import datetime  # Работа с датами и временем
from telebot.types import ReplyKeyboardMarkup, KeyboardButton  # Импортируем пользовательские клавиатуры



BOT_TOKEN = "___" #Подставить свои API ключи
NASA_API_KEY = "___"
OPENWEATHER_API_KEY = "___"

bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()
user_data = {}


def translate_text(user_id, text):
    """
    Переводит текст на выбранный язык пользователя с использованием Google Translate.

    Args:
        user_id (int): Уникальный идентификатор пользователя. Используется для получения текущего языка из user_data.
        text (str): Текст, который необходимо перевести.

    Returns:
        str: Переведенный текст на язык пользователя. Если язык не задан или ошибка при переводе, возвращает оригинальный текст
        или сообщение об ошибке.

    Примечания:
        Функция использует словарь `user_data`, чтобы определить язык пользователя. По умолчанию предполагается, что язык пользователя - английский ("en").
        Если язык задан, то используется язык, указанный в настройках пользователя.
        В случае возникновения ошибки при переводе, возвращается строка с описанием ошибки.
    """
    language = user_data.get(user_id, {}).get("language", "en")
    if language == "en":
        return text

    try:
        return translator.translate(text, dest=language).text
    except Exception as e:
        return f"Error translating: {str(e)}"

@bot.message_handler(commands=["start"])
def start_bot(message):
    """
    Обрабатывает команду "/start" от пользователя. Инициализирует данные пользователя и предлагает выбрать язык.

    Args:
        message (Message): Сообщение, полученное от пользователя. Содержит информацию о пользователе (chat.id и т.д.).

    Примечания:
        При получении команды "/start" функция создает запись о пользователе в `user_data` с дефолтными значениями:
        - Язык: английский ("en")
        - Город: None
        - Контекст: None
        После этого пользователь получает клавиатуру для выбора языка.
    """
    user_data[message.chat.id] = {"language": "en", "city": None, "context": None}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("English", "Русский")

    bot.send_message(
        message.chat.id,
        "Welcome! Please select your language:",  
        reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["English", "Русский"])
def set_language(message):
    """
    Устанавливает язык пользователя на основе выбора из клавиатуры.

    Args:
        message (Message): Сообщение от пользователя с выбранным языком.

    Примечания:
        Если пользователь выбирает "English", язык устанавливается на английский ("en").
        Если пользователь выбирает "Русский", язык устанавливается на русский ("ru").
        После выбора языка пользователю отправляется главное меню.
    """
 
    user_data[message.chat.id]["language"] = "en" if message.text == "English" else "ru"
    send_menu(message)

def send_menu(message):
    """
    Отправляет пользователю главное меню с доступными опциями.

    Args:
        message (Message): Сообщение от пользователя, используется для получения chat.id.

    Примечания:
        Главное меню содержит следующие кнопки:
        - "Set Location"
        - "Weather"
        - "Disasters"
        - "Safety Tips"
        - "Translator"
        - "Danger Zones"
        - "Change Language"
        
        Названия кнопок переводятся на выбранный пользователем язык с помощью функции `translate_text`.
    """
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(translate_text(user_id, "Set Location"),
               translate_text(user_id, "Weather"))
    markup.add(translate_text(user_id, "Disasters"),
               translate_text(user_id, "Safety Tips"))
    markup.add(translate_text(user_id, "Translator"),
               translate_text(user_id, "Danger Zones"))
    markup.add(translate_text(user_id, "Change Language"))
    
    bot.send_message(user_id, translate_text(user_id, "Choose an option:"), reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Set Location"))
def ask_city(message):
    """
    Запрашивает у пользователя его местоположение или название города для установки текущей локации.

    Args:
        message (Message): Сообщение от пользователя, содержащее информацию о нажатой кнопке "Set Location".

    Примечания:
        Эта функция задает пользователю вопрос о его местоположении или городе:
        - Пользователь может отправить свою геолокацию, используя кнопку "Send Location".
        - Если пользователь не хочет отправить местоположение, он может ввести название города вручную.
        После этого контекст пользователя изменяется на "set_location", чтобы последующие сообщения обрабатывались с учетом контекста.
    """
    user_data[message.chat.id]["context"] = "set_location"
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    location_button = KeyboardButton(translate_text(message.chat.id, "Send Location"), request_location=True)
    markup.add(location_button)
 
    bot.send_message(
        message.chat.id, 
        translate_text(message.chat.id, "Please send your location or type your city name."),
        reply_markup=markup)

@bot.message_handler(content_types=['location'])
def set_location_from_coordinates(message):
    """
    Обрабатывает получение геолокации от пользователя и сохраняет его местоположение.

    Эта функция выполняется, когда пользователь отправляет свою геолокацию. Она сохраняет координаты (широту и долготу) пользователя в `user_data`.
    Если геолокация не была получена, пользователю отправляется сообщение с ошибкой.

    Args:
        message (Message): Сообщение от пользователя, содержащее геолокацию.

    Примечания:
        Если геолокация была получена, сохраняются данные о местоположении (широта и долгота) и сбрасывается информация о городе.
        Затем вызывается основное меню бота с помощью функции `send_menu`.
        Если геолокация не может быть определена, пользователю отправляется сообщение об ошибке.
    """
    user_id = message.chat.id
    if not message.location:
        bot.send_message(user_id, translate_text(user_id, "Unable to detect location. Please try again."))
        return

    lat = message.location.latitude
    lon = message.location.longitude 

    user_data[user_id]["city"] = None  
    user_data[user_id]["location"] = {"latitude": lat, "longitude": lon}
    user_data[user_id]["context"] = None
  
    bot.send_message(user_id, translate_text(user_id, f"Location set: Latitude: {lat}, Longitude: {lon}."))
    send_menu(message)

@bot.message_handler(func=lambda msg: user_data.get(msg.chat.id, {}).get("context") == "set_location")
def set_city_from_text(message):
    """
    Обрабатывает ввод пользователем названия города и сохраняет его в `user_data`.

    Эта функция выполняется, если пользователь находится в контексте "set_location" (устанавливает город вручную).
    Введенный город проверяется на корректность, и если город действителен, сохраняется в данных пользователя.
    В противном случае пользователю отправляется сообщение об ошибке.

    Args:
        message (Message): Сообщение от пользователя, содержащее название города.

    Примечания:
        Если название города валидно, оно сохраняется в `user_data`, и данные о местоположении сбрасываются.
        В случае ошибки (если город неверный) пользователю предлагается попробовать снова или отправить свою геолокацию.
    """
    user_id = message.chat.id
    city = message.text.strip()

    if validate_city(city):
        user_data[user_id]["city"] = city
        user_data[user_id]["location"] = None  
        user_data[user_id]["context"] = None

        bot.send_message(user_id, translate_text(user_id, f"City set: {city}."))
        send_menu(message)
    else:
        bot.send_message(user_id, translate_text(user_id, "Invalid city name. Please try again or send your location."))

def validate_city(city):
    """
    Проверяет, существует ли город, используя API OpenWeather для получения информации о погоде.

    Эта функция отправляет запрос к OpenWeather API для проверки существования города. Если API возвращает успешный ответ, город считается действительным.

    Args:
        city (str): Название города, которое необходимо проверить.

    Returns:
        bool: True, если город существует (API возвращает статус 200), иначе False.
    
    Примечания:
        Если API не может найти город, функция вернет False. В противном случае, если ответ API успешен, возвращается True.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}"
    response = requests.get(url)
    return response.status_code == 200

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Weather"))
def weather_forecast(message):
    """
    Обрабатывает запрос пользователя на получение прогноза погоды.

    Эта функция выполняется, когда пользователь выбирает опцию "Weather". В зависимости от того, есть ли у пользователя
    информация о местоположении или городе, запрашивается прогноз погоды либо по геолокации, либо по названию города.
    Если данные о местоположении или городе отсутствуют, пользователю отправляется сообщение с просьбой указать их.

    Args:
        message (Message): Сообщение от пользователя, содержащее запрос на прогноз погоды.

    Примечания:
        Если пользователь не указал местоположение или город, ему будет предложено это сделать.
        Прогноз погоды предоставляется для ближайших 5 временных точек.
    """
    user_id = message.chat.id

    location = user_data[user_id].get("location")
    city = user_data[user_id].get("city")

    if not city and not location:
        bot.send_message(user_id, translate_text(user_id, "Please set your location or city first."))
        return

    if location:
        lat, lon = location["latitude"], location["longitude"]
        forecast = get_weather_forecast_by_location(lat, lon)
    else:
        forecast = get_weather_forecast(city)

    if forecast:
        bot.send_message(user_id, translate_text(user_id, f"Weather forecast:\n{forecast}"))
    else:
        bot.send_message(user_id, translate_text(user_id, "Unable to fetch forecast data. Please try again."))

def get_weather_forecast_by_location(lat, lon):
    """
    Получает прогноз погоды по координатам (широта и долгота) с использованием OpenWeather API.

    Эта функция отправляет запрос к OpenWeather API для получения прогноза погоды по заданным координатам.
    Прогноз включает температуру и описание погоды для ближайших 5 временных точек.

    Args:
        lat (float): Широта местоположения.
        lon (float): Долгота местоположения.

    Returns:
        str: Прогноз погоды для ближайших 5 временных точек, либо `None`, если данные не были получены.

    Примечания:
        Прогноз погоды формируется для каждого временного интервала с точностью до 3 часов.
        Если запрос не удается выполнить, функция возвращает `None`.
    """
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        forecast = [
            f"{item['dt_txt']}: {item['main']['temp']}°C, {item['weather'][0]['description']}"
            for item in data['list'][:5]
        ]
        return "\n".join(forecast)
    return None

def get_weather_forecast(city):
    """
    Получает прогноз погоды по названию города с использованием OpenWeather API.

    Эта функция отправляет запрос к OpenWeather API для получения прогноза погоды по указанному городу.
    Прогноз включает температуру и описание погоды для ближайших 5 временных точек.

    Args:
        city (str): Название города для получения прогноза погоды.

    Returns:
        str: Прогноз погоды для ближайших 5 временных точек, либо `None`, если данные не были получены.

    Примечания:
        Прогноз погоды формируется для каждого временного интервала с точностью до 3 часов.
        Если запрос не удается выполнить, функция возвращает `None`.
    """
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        forecast = [
            f"{item['dt_txt']}: {item['main']['temp']}°C, {item['weather'][0]['description']}"
            for item in data['list'][:5]
        ]
        return "\n".join(forecast)
    return None

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Disasters"))
def disasters_info(message):
    """
    Обрабатывает запрос пользователя на получение информации о последних катастрофах.

    Эта функция выполняется, когда пользователь выбирает опцию "Disasters". Она запрашивает информацию о последних катастрофах 
    с использованием API NASA и отправляет пользователю список последних катастроф. Если данных нет, отправляется сообщение об ошибке.

    Args:
        message (Message): Сообщение от пользователя, содержащее запрос на информацию о катастрофах.

    Примечания:
        Если запрос к API не удается, пользователю отправляется сообщение об ошибке.
        Отправляется список заголовков последних 5 катастроф.
    """
    disasters = get_disasters()
    if disasters:
        bot.send_message(message.chat.id,
                         translate_text(message.chat.id, "Latest disasters:") + "\n" + "\n".join(disasters))
    else:
        bot.send_message(message.chat.id,
                         translate_text(message.chat.id, "Unable to fetch disaster information."))

def get_disasters():
    """
    Получает информацию о последних катастрофах с использованием NASA API (EONET).

    Эта функция отправляет запрос к API NASA для получения списка катастроф, которые произошли недавно.
    Возвращает список заголовков последних 5 катастроф.

    Returns:
        list: Список заголовков последних 5 катастроф, либо пустой список, если данные не были получены.

    Примечания:
        Если запрос к API не удается выполнить, возвращается пустой список.
    """
    url = f"https://eonet.gsfc.nasa.gov/api/v3/events?api_key={NASA_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        events = response.json().get("events", [])
        return [event["title"] for event in events[:5]]
    return []




@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Safety Tips"))
def safety_tips_menu(message):
    """
    Обрабатывает запрос пользователя на получение советов по безопасности в случае чрезвычайной ситуации.

    Эта функция выполняется, когда пользователь выбирает опцию "Safety Tips". Она отображает меню с вариантами 
    для выбора типа чрезвычайной ситуации (Землетрясение, Пожар, Наводнение) и запрашивает пользователя выбрать один 
    из вариантов.

    Args:
        message (Message): Сообщение от пользователя, содержащее запрос на советы по безопасности.

    Примечания:
        Меню с вариантами для выбора типа чрезвычайной ситуации будет отправлено пользователю.
    """
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        translate_text(user_id, "Earthquake"),
        translate_text(user_id, "Fire"),
        translate_text(user_id, "Flood"))
    
    bot.send_message(user_id, translate_text(user_id, "Select type of emergency:"), reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in [
    translate_text(msg.chat.id, "Earthquake"),
    translate_text(msg.chat.id, "Fire"),
    translate_text(msg.chat.id, "Flood")])

def send_safety_tips(message):
    """
    Отправляет советы по безопасности в зависимости от выбранного типа чрезвычайной ситуации.

    Эта функция выполняется, когда пользователь выбирает тип чрезвычайной ситуации (Землетрясение, Пожар, Наводнение).
    Она вызывает функцию для получения соответствующих советов по безопасности и отправляет их пользователю.

    Args:
        message (Message): Сообщение от пользователя, содержащее выбор типа чрезвычайной ситуации.

    Примечания:
        После отправки советов пользователю, возвращается основное меню.
    """
    user_id = message.chat.id
    if message.text == translate_text(user_id, "Earthquake"):
        disaster_type = "Earthquake"
    elif message.text == translate_text(user_id, "Fire"):
        disaster_type = "Fire"
    elif message.text == translate_text(user_id, "Flood"):
        disaster_type = "Flood"
    else:
        disaster_type = None
    
    tips = get_safety_tips(disaster_type, user_id)
    translated_tips = [translate_text(user_id, tip) for tip in tips]
    
    bot.send_message(user_id, "\n".join(translated_tips))
    send_menu(message)

def get_safety_tips(disaster_type, user_id):
    """
    Получает советы по безопасности для выбранного типа чрезвычайной ситуации.

    Эта функция возвращает список советов по безопасности для различных типов чрезвычайных ситуаций: 
    Землетрясение, Пожар, Наводнение. В случае отсутствия типа ситуации возвращает сообщение о том, что советы недоступны.

    Args:
        disaster_type (str): Тип чрезвычайной ситуации, для которого нужно получить советы. Может быть "Earthquake", "Fire", "Flood".
        user_id (int): Идентификатор пользователя для перевода текста.

    Returns:
        list: Список советов по безопасности в зависимости от типа чрезвычайной ситуации.
    
    Примечания:
        Для каждого типа чрезвычайной ситуации возвращаются заранее подготовленные советы.
    """
    if disaster_type == "Earthquake":
        return [
            "Take cover under sturdy furniture.",
            "Stay away from windows and glass.",
            "Hold on to something stable.",
            "Move away from buildings if outdoors.",
            "Turn off gas to avoid leaks."
        ]
    elif disaster_type == "Fire":
        return [
            "Evacuate the building immediately.",
            "Call emergency services.",
            "Stay low to avoid smoke.",
            "Use fire extinguishers if available.",
            "Avoid elevators."
        ]
    elif disaster_type == "Flood":
        return [
            "Move to higher ground.",
            "Avoid walking in floodwaters.",
            "Do not drive through water.",
            "Turn off utilities if safe.",
            "Monitor weather updates."
        ]
    else:
        return [translate_text(user_id, "No tips available.")]

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Change Language"))
def change_language(message):
    """
    Запрашивает у пользователя выбор нового языка.

    Эта функция выполняется, когда пользователь выбирает опцию "Change Language". Она отображает меню с выбором 
    языков для изменения текущего языка бота.

    Args:
        message (Message): Сообщение от пользователя, содержащее запрос на смену языка.
    
    Примечания:
        После выполнения этой функции пользователь может выбрать новый язык: "English" или "Русский".
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("English", "Русский")
    bot.send_message(message.chat.id,
                     translate_text(message.chat.id, "Please select your language:"), reply_markup=markup)

def get_coordinates_1(city_name):
    """
    Получает координаты города с использованием API OpenWeatherMap.

    Эта функция отправляет запрос к API OpenWeatherMap для получения координат города (широта и долгота) по его названию.

    Args:
        city_name (str): Название города, координаты которого нужно получить.

    Returns:
        tuple: Кортеж с широтой и долготой города (float, float), если запрос успешен. 
               Возвращает (None, None), если город не найден или произошла ошибка.

    Example:
        >>> get_coordinates_1("London")
        (51.5074, -0.1278)
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        lat = data['coord']['lat']
        lon = data['coord']['lon']
        return lat, lon
    return None, None

def get_disasters_1():
    """
    Получает список последних природных катастроф с использованием NASA EONET API.

    Эта функция отправляет запрос к NASA EONET API для получения данных о последних катастрофах (до 5 событий). 
    Возвращает информацию о катастрофах, включая их название и географическое местоположение.

    Returns:
        list: Список словарей, где каждый словарь содержит название катастрофы ("title") и географическое расположение 
              ("geometry") из данных API. Если данные не получены, возвращается пустой список.

    Example:
        >>> get_disasters_1()
        [
            {"title": "Earthquake in Turkey", "geometry": {"coordinates": [37.5, 35.0]}},
            {"title": "Flood in India", "geometry": {"coordinates": [28.6, 77.2]}}
        ]
    """
    url = f"https://eonet.gsfc.nasa.gov/api/v3/events?api_key={NASA_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        disasters = []
        for event in data.get("events", [])[:5]:  
            disaster = {
                "title": event["title"],
                "geometry": event["geometry"]
            }
            disasters.append(disaster)
        return disasters
    return []

def generate_map_with_folium(coordinates, disasters):
    """
    Генерирует карту с помощью Folium, отмечает местоположение города и последние катастрофы, а затем сохраняет скриншот карты.

    Эта функция создает интерактивную карту, добавляет маркер для текущего местоположения пользователя, а также маркеры для катастроф, 
    полученных из NASA EONET API. После этого сохраняет карту как HTML-файл и делает скриншот карты с использованием Selenium.

    Args:
        coordinates (tuple): Кортеж с широтой и долготой текущего местоположения пользователя (float, float).
        disasters (list): Список катастроф, где каждая катастрофа представлена словарем с ключами:
                          - "title" (str): Название катастрофы.
                          - "geometry" (list): Географическая информация о катастрофе, включая координаты.

    Returns:
        str: Абсолютный путь к сохраненному изображению карты.

    Raises:
        Exception: Возможные ошибки во время работы Folium, Selenium или файловой системы.

    Example:
        >>> coordinates = (37.7749, -122.4194)  # Широта и долгота города.
        >>> disasters = [
                {"title": "Earthquake in California", "geometry": [{"type": "Point", "coordinates": [-122.4194, 37.7749]}]},
                {"title": "Flood in Nevada", "geometry": [{"type": "Point", "coordinates": [-119.8138, 39.5296]}]},
            ]
        >>> generate_map_with_folium(coordinates, disasters)
        "/path/to/disaster_map.png"
    """
    lat, lon = coordinates
    disaster_map = folium.Map(location=[lat, lon], zoom_start=15)
 
    folium.Marker(
        [lat, lon],
        popup="City: Your location",
        icon=folium.Icon(color="green", icon="info-sign"),
    ).add_to(disaster_map)
 
    for disaster in disasters:
        for geometry in disaster["geometry"]:
            if geometry["type"] == "Point":
                lat_point = geometry["coordinates"][1]
                lon_point = geometry["coordinates"][0]
                folium.Marker(
                    [lat_point, lon_point],
                    popup=disaster["title"],
                    icon=folium.Icon(color="red", icon="exclamation-sign"),
                ).add_to(disaster_map)
 
    map_file_path = "/home/oleg_hse/проек1/disaster_map.html"
    disaster_map.save(map_file_path)
 
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1000x800")

    service = Service("/home/oleg_hse/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
 
    driver.get("file://" + os.path.abspath(map_file_path))
    print("Ожидаем загрузку карты...")
    time.sleep(30)   
 
    map_image_path = "/home/oleg_hse/проек1/disaster_map.png"
    driver.save_screenshot(map_image_path)
    print(f"Изображение сохранено по пути: {map_image_path}")

    driver.quit()

    return map_image_path

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Вычисляет расстояние между двумя точками на земной поверхности, заданными их широтой и долготой, 
    используя формулу Гарвисайда.

    Args:
        lat1 (float): Широта первой точки в градусах.
        lon1 (float): Долгота первой точки в градусах.
        lat2 (float): Широта второй точки в градусах.
        lon2 (float): Долгота второй точки в градусах.

    Returns:
        float: Расстояние между двумя точками в километрах.

    Формулы:
        - Используется формула Гарвисайда (Haversine formula) для вычисления расстояния по сферической поверхности.
        - Земной радиус принимается равным 6371 км (среднее значение).

    Example:
        >>> lat1, lon1 = 55.7558, 37.6173  # Москва
        >>> lat2, lon2 = 59.9343, 30.3351  # Санкт-Петербург
        >>> calculate_distance(lat1, lon1, lat2, lon2)
        633.1  # Расстояние в километрах
    """
    R = 6371   
 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
 
    a = (
        math.sin(dlat / 2)**2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2)**2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
 
    return R * c

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Danger Zones"))
def danger_zones(message):
    """
    Обрабатывает запрос на отображение опасных зон.
    Определяет местоположение пользователя, получает данные о бедствиях,
    находит ближайшее бедствие и отправляет карту с отмеченными зонами.
    """
    user_id = message.chat.id
 
    user_location = user_data.get(user_id, {}).get("location")
    city_name = user_data.get(user_id, {}).get("city")

    if user_location: 
        lat, lon = user_location["latitude"], user_location["longitude"]
        bot.send_message(message.chat.id, 
                         translate_text(message.chat.id, f"✅ Location set: ({lat}, {lon})."))
    elif city_name: 
        bot.send_message(message.chat.id, 
                         translate_text(message.chat.id, "🔍 Determining city coordinates..."))
        lat, lon = get_coordinates_1(city_name)
        if lat is None or lon is None: 
            bot.send_message(message.chat.id, 
                             translate_text(message.chat.id, "❌ Unable to find coordinates for the specified city."))
            return
        bot.send_message(message.chat.id, 
                         translate_text(message.chat.id, f"✅ City coordinates determined: ({lat}, {lon})."))
    else: 
        bot.send_message(message.chat.id, 
                         translate_text(message.chat.id, "❌ Please set your location or city first using 'Set Location'."))
        return
 
    bot.send_message(message.chat.id, 
                     translate_text(message.chat.id, "🌍 Fetching current disaster data..."))
    disasters = get_disasters_1()
    if not disasters: 
        bot.send_message(message.chat.id, 
                         translate_text(message.chat.id, "ℹ️ No active disasters found."))
        return

    bot.send_message(message.chat.id, 
                     translate_text(message.chat.id, f"✅ Found {len(disasters)} active disasters."))
 
    closest_disaster = None
    closest_distance = float('inf')
    for disaster in disasters:
        for geometry in disaster["geometry"]:
            if geometry["type"] == "Point":   
                disaster_lat = geometry["coordinates"][1]
                disaster_lon = geometry["coordinates"][0]
                distance = calculate_distance(lat, lon, disaster_lat, disaster_lon)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_disaster = disaster
 
    bot.send_message(message.chat.id, 
                     translate_text(message.chat.id, "🗺️ Generating map with disasters..."))
    map_image_path = generate_map_with_folium((lat, lon), disasters)

    bot.send_message(message.chat.id, 
                     translate_text(message.chat.id, "✅ Map successfully created."))
 
    if closest_disaster:
        disaster_info = (f"{translate_text(message.chat.id, 'Closest disaster:')} "
                         f"{closest_disaster['title']} ({closest_distance:.2f} km)")
    else:
        disaster_info = translate_text(message.chat.id, "No disasters in proximity.")
    
    bot.send_message(message.chat.id, disaster_info)
 
    bot.send_message(message.chat.id, 
                     translate_text(message.chat.id, "📤 Sending map..."))
    with open(map_image_path, 'rb') as map_file:
        bot.send_photo(user_id, map_file)

    bot.send_message(message.chat.id, 
                     translate_text(message.chat.id, "✅ Map sent!"))
    send_menu(message)
    
@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Translator"))
def translator_request(message):
    """
    Запрашивает у пользователя текст для перевода.

    Эта функция выполняется, когда пользователь выбирает опцию "Translator". Она изменяет контекст пользователя на 
    "translator" и запрашивает у пользователя текст для перевода.

    Args:
        message (Message): Сообщение от пользователя, которое активирует запрос на перевод текста.
    
    Примечания:
        После выполнения этой функции бот ожидает текст для перевода от пользователя.
    """
    user_data[message.chat.id]["context"] = "translator"
    bot.send_message(message.chat.id,
                     translate_text(message.chat.id, "Please send the text to translate."))

@bot.message_handler(func=lambda msg: user_data[msg.chat.id].get("context") == "translator")
def translate_user_text(message):
    """
    Переводит текст, отправленный пользователем, на выбранный язык.

    Эта функция выполняется, когда пользователь отправляет текст для перевода. Бот определяет язык исходного текста 
    и переводит его на язык, выбранный пользователем. Если текст уже на нужном языке, бот уведомляет пользователя.

    Args:
        message (Message): Сообщение от пользователя, содержащее текст, который нужно перевести.
    
    Примечания:
        После перевода текста бот отправляет переведенный текст пользователю и возвращает в основное меню.
    """
    user_id = message.chat.id
    user_language = user_data[user_id]["language"]
    
    detected_language = translator.detect(message.text).lang
    
    if detected_language == user_language:
        bot.send_message(user_id, 
                         translate_text(user_id, "The text is already in your selected language."))
        send_menu(message)
        return
    
    translated_text = translator.translate(message.text, dest=user_language).text
    
    bot.send_message(user_id,
                     translate_text(user_id, f"Translated text: {translated_text}"))
    send_menu(message)

notified_events = {}   

def start_notification_system():
    """
    Запускает систему уведомлений, которая проверяет новые бедствия каждое
    заданное количество минут (30 минут).
    """
    scheduler = BackgroundScheduler()  
    scheduler.add_job(check_for_new_disasters, 'interval', minutes=30)
    scheduler.start()  

def check_for_new_disasters():
    """
    Проверяет наличие новых бедствий в базе данных и отправляет уведомления пользователям,
    если бедствия находятся в радиусе 100 км от их местоположения или города.
    """
    global notified_events
    disasters = get_disasters_1()  

    for user_id, data in user_data.items():
        user_location = data.get("location")
        city = data.get("city")

        if user_location:
            lat, lon = user_location["latitude"], user_location["longitude"]
        elif city:
            lat, lon = get_coordinates_1(city)   
            if lat is None or lon is None:
                continue   
        else:
            continue   
 
        for disaster in disasters:
            for geometry in disaster["geometry"]:
                if geometry["type"] == "Point":  
                    disaster_lat = geometry["coordinates"][1]
                    disaster_lon = geometry["coordinates"][0]
                    distance = calculate_distance(lat, lon, disaster_lat, disaster_lon)  
 
                    if distance <= 100 and disaster["title"] not in notified_events:
                        notified_events[disaster["title"]] = datetime.now()   
                        send_disaster_notification(user_id, disaster, distance)   

def send_disaster_notification(user_id, disaster, distance):
    """
    Отправляет уведомление пользователю о новом бедствии, если оно находится
    в радиусе 100 км.

    :param user_id: ID пользователя
    :param disaster: Данные о бедствии
    :param distance: Расстояние от пользователя до бедствия
    """
    notification_text = (
        f"{translate_text(user_id, '🚨 New disaster alert!')}\n"
        f"{translate_text(user_id, 'Title:')} {disaster['title']}\n"
        f"{translate_text(user_id, 'Distance:')} {distance:.2f} km\n")
    bot.send_message(user_id, notification_text)  

bot.infinity_polling()   

import telebot , folium, os, time, math, requests
from telebot import types
from googletrans import Translator
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "7715261297:AAEJz86iQMu_0XdgCipspvsaszhXXO1F8qM"
NASA_API_KEY = "nnl9fb1c4HzwYZ6Pi47k8nhrJeRgCR8hEhBC1VJx"
OPENWEATHER_API_KEY = "6a094f28fba1cb3617175cbde57abf60"

bot = telebot.TeleBot(BOT_TOKEN) 
translator = Translator()
  
user_data = {}

#Перевод текста на язык пользователя
def translate_text(user_id, text):
    language = user_data.get(user_id, {}).get("language", "en")
    if language == "en":
        return text
    try:
        return translator.translate(text, dest=language).text
    except Exception as e:
        return f"Error translating: {str(e)}"

@bot.message_handler(commands=["start"])
def start_bot(message):
    user_data[message.chat.id] = {"language": "en", "city": None, "context": None} #начальные данные пользователя
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("English", "Русский")
    bot.send_message(
        message.chat.id,
        "Welcome! Please select your language:",
        reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["English", "Русский"])
def set_language(message):
    user_data[message.chat.id]["language"] = "en" if message.text == "English" else "ru"
    send_menu(message)

def send_menu(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(translate_text(user_id, "Set Location"),translate_text(user_id, "Weather"))
    markup.add(translate_text(user_id, "Disasters"),translate_text(user_id, "Safety Tips"))
    markup.add(translate_text(user_id, "Translator"), translate_text(user_id, "Danger Zones"))
    markup.add(translate_text(user_id, "Change Language"))
    bot.send_message(user_id, translate_text(user_id, "Choose an option:"),reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Set Location"))
def ask_city(message):
    user_data[message.chat.id]["context"] = "set_location"
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    location_button = KeyboardButton(translate_text(message.chat.id, "Send Location"), request_location=True)
    markup.add(location_button)
    bot.send_message(message.chat.id, 
                    translate_text(message.chat.id, "Please send your location or type your city name."),
                    reply_markup=markup)

@bot.message_handler(content_types=['location'])
def set_location_from_coordinates(message):
    user_id = message.chat.id
    if not message.location:
        bot.send_message( user_id,translate_text(user_id, "Unable to detect location. Please try again."))
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
    user_id = message.chat.id
    city = message.text.strip()

    if validate_city(city):
        user_data[user_id]["city"] = city
        user_data[user_id]["location"] = None  
        user_data[user_id]["context"] = None

        bot.send_message(user_id, translate_text(user_id, f"City set: {city}."))
        send_menu(message)
    else:
        bot.send_message( user_id,translate_text(user_id, "Invalid city name. Please try again or send your location."))

#Код создан операясь на документацию о OpenWeatherMap API, requests.
def validate_city(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}"
    response = requests.get(url)
    return response.status_code == 200
#Код создан операясь на документацию о OpenWeatherMap API, requests.

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Weather"))
def weather_forecast(message):
    user_id = message.chat.id

    location = user_data[user_id].get("location")
    city = user_data[user_id].get("city")

    if not city and not location:
        bot.send_message(user_id,translate_text(user_id, "Please set your location or city first."))
        return

    if location:
        lat, lon = location["latitude"], location["longitude"]
        forecast = get_weather_forecast_by_location(lat, lon)
    else:
        forecast = get_weather_forecast(city)

    if forecast:
        bot.send_message(user_id,translate_text(user_id, f"Weather forecast:\n{forecast}"))
    else:
        bot.send_message(user_id,translate_text(user_id, "Unable to fetch forecast data. Please try again."))

#Код создан операясь на документацию о OpenWeatherMap API, requests.
def get_weather_forecast_by_location(lat, lon):
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
#Код создан операясь на документацию о OpenWeatherMap API, requests.

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Disasters"))
def disasters_info(message):
    disasters = get_disasters()
    if disasters:
        bot.send_message(message.chat.id,
                        translate_text(message.chat.id, "Latest disasters:") + "\n" + "\n".join(disasters))
    else:
        bot.send_message(message.chat.id, 
                         translate_text(message.chat.id, "Unable to fetch disaster information."))

#Код создан опираясь на документации о EONET API, requests.
def get_disasters():
    url = f"https://eonet.gsfc.nasa.gov/api/v3/events?api_key={NASA_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        events = response.json().get("events", [])
        return [event["title"] for event in events[:5]]
    return []
#Код создан опираясь на документации о EONET API, requests.

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Safety Tips"))
def safety_tips_menu(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        translate_text(user_id, "Earthquake"),
        translate_text(user_id, "Fire"),
        translate_text(user_id, "Flood"))
    
    bot.send_message(user_id,translate_text(user_id, "Select type of emergency:"),reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in [
    translate_text(msg.chat.id, "Earthquake"),
    translate_text(msg.chat.id, "Fire"),
    translate_text(msg.chat.id, "Flood")])

def send_safety_tips(message):
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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("English", "Русский")
    bot.send_message(message.chat.id,
                     translate_text(message.chat.id, "Please select your language:"), reply_markup=markup)

#Код создан операясь на документацию о OpenWeatherMap API, requests.
def get_coordinates_1(city_name):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        lat = data['coord']['lat']
        lon = data['coord']['lon']
        return lat, lon
    return None, None
#Код создан операясь на документацию о OpenWeatherMap API, requests.

#Код создан опираясь на документации о EONET API, requests.
def get_disasters_1():
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
#Код создан опираясь на документации о EONET API, requests.

def generate_map_with_folium(coordinates, disasters):
    lat, lon = coordinates
    
    disaster_map = folium.Map(location=[lat, lon], zoom_start=15)

    folium.Marker(
        [lat, lon],
        popup="Город: Ваше местоположение",
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
    R = 6371  
    dlat = math.radians(lat2 - lat1) 
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@bot.message_handler(func=lambda msg: msg.text == translate_text(msg.chat.id, "Danger Zones"))
def danger_zones(message):
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
    user_data[message.chat.id]["context"] = "translator"
    bot.send_message(message.chat.id,
                     translate_text(message.chat.id, "Please send the text to translate."))

@bot.message_handler(func=lambda msg: user_data[msg.chat.id].get("context") == "translator")
def translate_user_text(message):
    user_id = message.chat.id
    user_language = user_data[user_id]["language"]
    
    detected_language = translator.detect(message.text).lang
    
    if detected_language == user_language:
        bot.send_message(user_id, 
                         translate_text(user_id, "The text is already in your selected language."))
        send_menu(message)
        return
    
    translated_text = translator.translate(message.text, dest=user_language).text
    
    bot.send_message( user_id,
                     translate_text(user_id, f"Translated text: {translated_text}"))
    send_menu(message)

notified_events = {}

def start_notification_system():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_for_new_disasters, 'interval', minutes=30)  
    scheduler.start()

def check_for_new_disasters():
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
    notification_text = (
        f"{translate_text(user_id, '🚨 New disaster alert!')}\n"
        f"{translate_text(user_id, 'Title:')} {disaster['title']}\n"
        f"{translate_text(user_id, 'Distance:')} {distance:.2f} km\n")
    bot.send_message(user_id, notification_text)

bot.infinity_polling()

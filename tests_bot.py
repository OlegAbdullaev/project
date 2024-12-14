import unittest
from unittest.mock import patch, MagicMock
from bot import (
    validate_city, get_weather_forecast, get_weather_forecast_by_location,
    get_disasters, calculate_distance, get_safety_tips
)

class TestBotFunctions(unittest.TestCase):

    @patch("bot.requests.get")
    def test_validate_city(self, mock_get):
        mock_response = MagicMock()
        city = "London"

        mock_response.status_code = 200
        mock_get.return_value = mock_response
        if mock_response.status_code == 200:
            result = validate_city(city)
            self.assertTrue(result)
        else:
            result = validate_city(city)
            self.assertFalse(result)

    @patch("bot.requests.get")
    def test_get_weather_forecast(self, mock_get):
        mock_response = MagicMock()
        city = "London"

        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": [
                {"dt_txt": "2024-12-14 12:00:00", "main": {"temp": 15}, "weather": [{"description": "clear sky"}]},
                {"dt_txt": "2024-12-14 15:00:00", "main": {"temp": 16}, "weather": [{"description": "partly cloudy"}]}
            ]
        }
        mock_get.return_value = mock_response
        if mock_response.status_code == 200:
            result = get_weather_forecast(city)
            self.assertIn("clear sky", result)
            self.assertIn("2024-12-14 12:00:00", result)
        else:
            result = get_weather_forecast(city)
            self.assertIsNone(result)

    @patch("bot.requests.get")
    def test_get_weather_forecast_by_location(self, mock_get):
        mock_response = MagicMock()
        lat, lon = 40.7128, -74.0060  

        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": [
                {"dt_txt": "2024-12-14 12:00:00", "main": {"temp": 20}, "weather": [{"description": "sunny"}]},
                {"dt_txt": "2024-12-14 18:00:00", "main": {"temp": 18}, "weather": [{"description": "cloudy"}]}
            ]
        }
        mock_get.return_value = mock_response
        if mock_response.status_code == 200:
            result = get_weather_forecast_by_location(lat, lon)
            self.assertIn("sunny", result)
            self.assertIn("2024-12-14 12:00:00", result)
        else:
            result = get_weather_forecast_by_location(lat, lon)
            self.assertIsNone(result)

    def test_calculate_distance(self):
        lat1, lon1 = 51.5074, -0.1278  
        lat2, lon2 = 48.8566, 2.3522   

        distance = calculate_distance(lat1, lon1, lat2, lon2)
        if distance > 0: 
            self.assertAlmostEqual(distance, 343, delta=5)  
        else:  
            self.assertEqual(distance, 0)

    def test_get_safety_tips(self):
        disaster_type = "Earthquake"
        user_id = 1

        tips = get_safety_tips(disaster_type, user_id=user_id)
        if tips:
            self.assertIn("Take cover under sturdy furniture.", tips)
        else:
            self.assertEqual(tips, "No safety tips available.")

    @patch("bot.requests.get")
    def test_get_weather_forecast_negative(self, mock_get):
        mock_response = MagicMock()
        city = "InvalidCity"

        mock_response.status_code = 404
        mock_get.return_value = mock_response
        if mock_response.status_code != 200:
            result = get_weather_forecast(city)
            self.assertIsNone(result)

    @patch("bot.requests.get")
    def test_get_weather_forecast_by_location_negative(self, mock_get):
        mock_response = MagicMock()
        lat, lon = 0.0, 0.0 

        mock_response.status_code = 500
        mock_get.return_value = mock_response
        if mock_response.status_code != 200:
            result = get_weather_forecast_by_location(lat, lon)
            self.assertIsNone(result)

    @patch("bot.requests.get")
    def test_get_disasters_negative(self, mock_get):
        mock_response = MagicMock()

        mock_response.status_code = 404
        mock_get.return_value = mock_response
        if mock_response.status_code != 200:
            result = get_disasters()
            self.assertEqual(result, [])

    @patch("bot.requests.get")
    def test_get_disasters_empty_response(self, mock_get):
        mock_response = MagicMock()

        mock_response.status_code = 200
        mock_response.json.return_value = {"events": []}
        mock_get.return_value = mock_response
        if not mock_response.json()["events"]:
            result = get_disasters()
            self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()




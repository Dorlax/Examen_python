import requests
import click
from loguru import logger
import json
from datetime import datetime
from typing import Dict, List

# Configure logger for clean logs
logger.remove()  # Remove default logger
logger.add("weather_forecast.log", rotation="1 MB", level="INFO")  # Log file
logger.add(lambda msg: print(msg, end=""), level="INFO")  # Console display


class WeatherData:
    """
    Class to store and manipulate weather data for a single day.
    It facilitates cumulative calculations and transition counting.
    """
    def __init__(self, date: str):
        self.date = date
        self.rain_mm = 0.0
        self.snow_mm = 0.0
        self.transitions = 0
        self.samples = []  # List of samples (temp, weather_main) to detect transitions
    
    def add_sample(self, temp: float, weather_main: str, rain: float = 0.0, snow: float = 0.0):
        """
        Adds a weather sample (a forecast at a given time).
        Automatically calculates if there is a major transition.
        """
        # Add precipitation
        self.rain_mm += rain
        self.snow_mm += snow
        
        # Major transition detection
        if self.samples:  # If there's already a previous sample
            prev_temp, prev_weather = self.samples[-1]
            temp_change = abs(temp - prev_temp)
            weather_change = weather_main != prev_weather
            
            # Major transition = category change AND variation > 3°C
            if weather_change and temp_change > 3:
                self.transitions += 1
                logger.debug(f"Transition detected: {prev_weather}->{weather_main}, ΔT={temp_change:.1f}°C")
        
        self.samples.append((temp, weather_main))
    
    def to_dict(self) -> Dict:
        """Converts data to dictionary for final JSON"""
        return {
            "date_local": self.date,
            "rain_cumul_mm": round(self.rain_mm, 1),
            "snow_cumul_mm": round(self.snow_mm, 1),
            "major_transitions_count": self.transitions
        }


class WeatherForecast:
    """
    Main class that handles fetching and processing weather forecasts.
    It orchestrates all operations.
    """
    API_URL = "http://api.openweathermap.org/data/2.5/forecast"
    
    def __init__(self, api_key: str, city: str, country: str):
        self.api_key = api_key
        self.city = city
        self.country = country
        self.daily_data = {}  # Dictionary {date: WeatherData}
        self.max_humidity = 0
        self.location_name = ""
    
    def fetch_data(self) -> bool:
        """
        Fetches data from the OpenWeatherMap API.
        Returns True if successful, False otherwise.
        """
        params = {
            'q': f"{self.city},{self.country}",
            'appid': self.api_key,
            'units': 'metric',  # To get temperatures in Celsius
            'cnt': 40  # 40 forecasts = 5 days * 8 forecasts/day (every 3h)
        }
        
        logger.info(f"Fetching forecasts for {self.city}, {self.country}...")
        
        try:
            response = requests.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()  # Raises exception if HTTP error
            
            data = response.json()
            self.location_name = data['city']['name']
            logger.success(f"Data successfully retrieved for {self.location_name}")
            
            self._process_forecasts(data['list'])
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during API request: {e}")
            return False
        except KeyError as e:
            logger.error(f"Error in received data structure: {e}")
            return False
    
    def _process_forecasts(self, forecasts: List[Dict]):
        """
        Processes each forecast received from the API.
        Groups forecasts by day and calculates statistics.
        Excludes current day to keep only the next 5 days.
        """
        logger.info(f"Processing {len(forecasts)} forecasts...")
        
        # Current date (current day) for filtering
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        for forecast in forecasts:
            # Extract date in YYYY-MM-DD format
            dt = datetime.fromtimestamp(forecast['dt'])
            date_str = dt.strftime('%Y-%m-%d')
            
            # Ignore forecasts for current day
            if date_str == today_str:
                logger.debug(f"Current day forecast ignored: {date_str}")
                continue
            
            # Create a WeatherData object for this day if necessary
            if date_str not in self.daily_data:
                self.daily_data[date_str] = WeatherData(date_str)
            
            # Extract data
            temp = forecast['main']['temp']
            weather_main = forecast['weather'][0]['main']
            humidity = forecast['main']['humidity']
            
            # Precipitation (may not exist in response)
            rain = forecast.get('rain', {}).get('3h', 0.0)
            snow = forecast.get('snow', {}).get('3h', 0.0)
            
            # Update maximum humidity
            self.max_humidity = max(self.max_humidity, humidity)
            
            # Add sample to corresponding day
            self.daily_data[date_str].add_sample(temp, weather_main, rain, snow)
    
    def generate_report(self, output_file: str = "weather_forecast.json"):
        """
        Generates the final JSON file with all statistics.
        """
        # Calculate total cumulative values for the period
        total_rain = sum(day.rain_mm for day in self.daily_data.values())
        total_snow = sum(day.snow_mm for day in self.daily_data.values())
        
        # Build final dictionary
        report = {
            "forecast_location_name": self.location_name,
            "country_code": self.country.upper(),
            "total_rain_period_mm": round(total_rain, 1),
            "total_snow_period_mm": round(total_snow, 1),
            "max_humidity_period": self.max_humidity,
            "forecast_details": [
                day.to_dict() for day in sorted(
                    self.daily_data.values(), 
                    key=lambda x: x.date
                )
            ]
        }
        
        # Write JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        
        logger.success(f"Report generated: {output_file}")
        self._display_summary(report)
    
    def _display_summary(self, report: Dict):
        """Displays a summary of results in the console"""
        logger.info("\n" + "="*50)
        logger.info(f"Location: {report['forecast_location_name']} ({report['country_code']})")
        logger.info(f"Total rain: {report['total_rain_period_mm']} mm")
        logger.info(f"Total snow: {report['total_snow_period_mm']} mm")
        logger.info(f"Max humidity: {report['max_humidity_period']}%")
        logger.info(f"Number of days: {len(report['forecast_details'])}")
        logger.info("="*50)


@click.command()
@click.option('--city', prompt='Ville', help='City name')
@click.option('--country', prompt='Code pays (ex: FR, US)', help='ISO country code (2 letters)')
@click.option('--api-key', 
              envvar='OPENWEATHER_API_KEY',
              prompt='Clé API OpenWeatherMap',
              help='API key (or OPENWEATHER_API_KEY environment variable)')
@click.option('--output', default='weather_forecast.json', help='Output file')
def main(city: str, country: str, api_key: str, output: str):
    """
    5-day weather forecast program.
    
    Fetches data from OpenWeatherMap and generates a detailed report
    with precipitation accumulations and major weather transitions.
    """
    logger.info("Starting weather forecast program")
    
    # Create object that handles forecasts
    forecast = WeatherForecast(api_key, city, country)
    
    # Fetch and process data
    if forecast.fetch_data():
        forecast.generate_report(output)
        logger.success("Processing completed successfully!")
    else:
        logger.error("Processing failed")
        exit(1)


if __name__ == "__main__":
    main()
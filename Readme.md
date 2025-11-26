# Weather Forecast Analyzer

Python program to analyze weather forecasts for the next 5 days via the OpenWeatherMap API.

## Features

- Retrieval of weather forecasts every 3 hours over 5 days
- Calculation of precipitation accumulation (rain and snow) per day
- Detection of major weather transitions
- Generation of a detailed JSON report
- Detailed operation logs
- Interactive command-line interface

## Prerequisites

- Python 3.11 or 3.12 (recommended, Python 3.13 may have compatibility issues)
- An OpenWeatherMap API key (free at [openweathermap.org](https://openweathermap.org/api) you will need to create an account if you don't own one)

## Installation

1. Clone the project (or download the .zip):
```bash
git clone <repo_url>
cd weather-forecast
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive mode
```bash
python weather_forecast.py
```
The program will ask you for:
- City name
- Country code (e.g.: FR, US, GB)
- Your OpenWeatherMap API key

### Command-line mode
```bash
python weather_forecast.py --city Paris --country FR --api-key YOUR_API_KEY
```

### With environment variable
```bash
export OPENWEATHER_API_KEY="your_api_key"
python weather_forecast.py --city Paris --country FR
```

### Available options
- `--city`: City name
- `--country`: ISO country code (2 letters)
- `--api-key`: OpenWeatherMap API key
- `--output`: Output file name (default: weather_forecast.json)

## Output format

The program generates a JSON file with the following structure:

```json
{
    "forecast_location_name": "Paris",
    "country_code": "FR",
    "total_rain_period_mm": 12.5,
    "total_snow_period_mm": 0.0,
    "max_humidity_period": 85,
    "forecast_details": [
        {
            "date_local": "2024-11-25",
            "rain_cumul_mm": 3.2,
            "snow_cumul_mm": 0.0,
            "major_transitions_count": 1
        }
    ]
}
```

## Definition of major transitions

A major transition is detected when **two conditions** are simultaneously met between two consecutive forecasts:
1. Weather category change (e.g.: Clear → Rain, Clouds → Snow)
2. Temperature variation greater than 3°C in absolute value

## Generated files

- `weather_forecast.json`: Forecast report (default)
- `weather_forecast.log`: Detailed log file

## Code structure

The project uses an object-oriented architecture:

- **`WeatherData`**: Class representing data for a single day
- **`WeatherForecast`**: Main class managing the API and processing
- **`main()`**: Entry point with CLI interface (Click)

## Libraries used

- **requests**: HTTP requests to the OpenWeatherMap API
- **click**: Elegant command-line interface
- **loguru**: Advanced logging system

## Troubleshooting

### Imports are underlined in yellow in VSCode
If you're using Python 3.13, try:
1. Downgrade to Python 3.11 or 3.12
2. Or verify that VSCode is using the correct interpreter (`Ctrl+Shift+P` > "Python: Select Interpreter")

### API error
- Check that your API key is valid
- Make sure you've activated the "5 day / 3 hour forecast" API on your OpenWeatherMap account (you can check it if you go into my services)

from datetime import datetime
from zoneinfo import ZoneInfo
from Utilities.utilities import log
import requests
import json


def get_current_time(timezone="America/Los_Angeles"):
    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")

def get_city_weather(city):
    url = f"https://wttr.in/{city}?format=3&m"
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.text

def get_user_city():
    return "Los Angeles"  # Replace with your desired city


# TOOLS = [{}, {}, {}]
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the current date and time for a given IANA timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone name, e.g. 'America/Los_Angeles', 'Europe/London'."
                    }
                },
                "required": ["timezone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_weather",
            "description": "Returns the current weather for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City to get the weather for."
                    }
                },
                "required": ["city"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_city",
            "description": "Returns the user's city. Use this when the user says 'my city', 'my home', 'where I live' or 'my location' without naming the city.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


FUNCTION_NAME_TO_FUNCTION_MAP = {
    "get_current_time": get_current_time,
    "get_city_weather": get_city_weather,
    "get_user_city": get_user_city
}

def run_tool(tool_call):
    func_name = tool_call.function.name
    func_args = {}
    
    try:
        func_args = json.loads(tool_call.function.arguments or "{}")
        log(f"🔧 {func_name}({func_args})") # Debug log for function call
        fn = FUNCTION_NAME_TO_FUNCTION_MAP.get(func_name)
        result = fn(**func_args)
    
    except Exception as e:
        result = f"Error whilie running '{func_name}': {str(e)}"

    log(f"   ↳ {result}")
    return str(result)
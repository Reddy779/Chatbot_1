import os
import numexpr
from langchain_core.tools import tool
import requests
from ddgs import DDGS    

# TOOL 1 [ WEB Search ]
@tool
def web_search_tool(query: str) -> str:
    """
    Searches the web using DuckDuckGo and returns top 4 results.
    Use this when the user asks about current events, news,
    or anything that needs up-to-date information.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
        
        if not results:
            return "No results found from this query."
        
        formatted = []

        for i, r in enumerate(results, 1):
            formatted.append(
                f"{i}. {r.get('title', 'No title')}\n"
                f"   {r.get('body', 'No snippet')}\n"
                f"   Source: {r.get('href', 'No URL')}"
            )
        return "\n\n".join(formatted)

    except Exception as e:
        return f"Search failed: {str(e)}"
    
    
# TOOL 2 [ Calculator ]
@tool
def calculator_tool(expression: str) -> str:
    """
    Safely evaluates a mathematical expression and returns the result.
    Use this for any math calculations, unit conversions, or numerical
    questions. Example: '2 ** 10', '(15 * 8) / 3', 'sqrt(144)'
    Never use this for non-mathematical expressions.
    """
    try:
        result = numexpr.evaluate(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation failed: {str(e)}. Please check the expression."
    

# TOOL 3 [ Weather ]
@tool
def weather_tool(city: str) -> str:
    """
    Gets current weather for a city using OpenWeatherMap API.
    Use this when the user asks about weather in any location.
    Example input: 'Bangalore', 'Kolar', 'Hyderabad'
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather tool is not configured. OPENWEATHER_API_KEY is missing."

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={api_key}&units=metric"
        )
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code != 200:
            return f"Could not get weather for {city}: {data.get('message', 'Unknown error')}"

        temp        = data["main"]["temp"]
        feels_like  = data["main"]["feels_like"]
        humidity    = data["main"]["humidity"]
        description = data["weather"][0]["description"]
        city_name   = data["name"]
        country     = data["sys"]["country"]

        return (
            f"Weather in {city_name}, {country}:\n"
            f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
            f"Conditions: {description.capitalize()}\n"
            f"Humidity: {humidity}%"
        )

    except requests.Timeout:
        return f"Weather request timed out for {city}. Try again."
    except Exception as e:
        return f"Weather lookup failed: {str(e)}"
    

RESEARCH_TOOLS = [web_search_tool]
TOOL_AGENT_TOOLS = [calculator_tool, weather_tool]
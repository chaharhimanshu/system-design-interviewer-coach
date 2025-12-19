"""
Tool Functions
Defines calculator and weather tools wrapped as LangChain Tool objects
"""

import requests
import logging
from langchain_core.tools import Tool

logger = logging.getLogger(__name__)


def calculator_func(expression: str) -> str:
    """
    Calculate a mathematical expression.

    Args:
        expression: A mathematical expression to evaluate (e.g., "2 + 2", "10 * 5 - 3")

    Returns:
        The result of the calculation as a string
    """
    try:
        logger.info(f"Calculator tool invoked with expression: {expression}")

        # Clean the expression
        expression = expression.strip()

        # Safely evaluate the expression
        # Only allow basic math operations
        allowed_chars = set("0123456789+-*/.()")
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "Error: Expression contains invalid characters. Only numbers and basic operators (+, -, *, /, parentheses) are allowed."

        result = eval(expression, {"__builtins__": {}}, {})
        logger.info(f"Calculator result: {result}")
        return str(result)

    except ZeroDivisionError:
        error_msg = "Error: Division by zero"
        logger.error(error_msg)
        return error_msg
    except SyntaxError:
        error_msg = "Error: Invalid mathematical expression"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg


def weather_func(location: str) -> str:
    """
    Get current weather information for a location.

    Args:
        location: City name or location (e.g., "London", "New York", "Tokyo")

    Returns:
        Weather information as a string
    """
    try:
        logger.info(f"Weather tool invoked for location: {location}")

        # Using wttr.in free weather API (no API key required)
        url = f"https://wttr.in/{location}?format=3"

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        weather_info = response.text.strip()
        logger.info(f"Weather result: {weather_info}")
        return weather_info

    except requests.exceptions.Timeout:
        error_msg = "Error: Weather service timeout. Please try again."
        logger.error(error_msg)
        return error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Error: Unable to fetch weather data. {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg


# Create LangChain Tool objects
calculator_tool = Tool(
    name="Calculator",
    func=calculator_func,
    description="""Useful for performing mathematical calculations. 
    Input should be a mathematical expression like '2 + 2' or '10 * 5 - 3'.
    Supports basic arithmetic operations: addition (+), subtraction (-), multiplication (*), division (/), and parentheses.
    Example inputs: '15 * 20', '(100 + 50) / 2', '45 - 12 + 8'""",
)

weather_tool = Tool(
    name="Weather",
    func=weather_func,
    description="""Useful for getting current weather information for any location.
    Input should be a city name or location like 'London', 'New York', 'Tokyo', or 'Paris'.
    Returns current weather conditions including temperature and description.
    Example inputs: 'London', 'New York', 'San Francisco'""",
)

# Export tools list
tools = [calculator_tool, weather_tool]
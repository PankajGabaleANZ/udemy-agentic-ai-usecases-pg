import json
import datetime
from typing import Any, Callable, Set, Dict, List, Optional
import os
import uuid
# These are user-defined utility functions that agents can invoke.

def get_current_datetime(format: Optional[str] = None) -> str:
    """
    Returns the current system datetime as a JSON string, with optional custom formatting.

    :param format: Optional datetime format string. Defaults to a standard format if None.
    :return: JSON string containing the current datetime.
    """
    current_time = datetime.datetime.now()
    time_format = format if format else "%Y-%m-%d %H:%M:%S"
    return json.dumps({"current_time": current_time.strftime(time_format)})

def create_text_file_from_string(data: str, filename: Optional[str] = None) -> str:
    """
    Creates a text file from the provided string data.

    :param data: The string content to write into the text file.
    :param filename: Optional filename. If not provided, generates a random UUID-based filename.
    :return: The path to the created text file.
    """
    
    # Generate filename if not provided
    if not filename:
        filename = f"{uuid.uuid4().hex}.txt"
    print("Testing the file saving")
    filepath = "Section_6/"
    # Write data to file
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(data)
    
    return filepath

def get_weather_by_location(location: str) -> str:
    """
    Retrieves mock weather information for the specified location.

    :param location: Location name for which to fetch weather data.
    :return: JSON string with weather details.
    """
    mock_weather_data = {"New York": "Sunny, 25°C", "London": "Cloudy, 18°C", "Tokyo": "Rainy, 22°C"}
    weather = mock_weather_data.get(location, "Weather data not available for this location.")
    return json.dumps({"weather": weather})


def send_email_to_address(recipient: str, subject: str, body: str) -> str:
    """
    Mocks sending an email to a specified email address with a subject and body.

    :param recipient: Email address of the recipient.
    :param subject: Subject line of the email.
    :param body: Body content of the email.
    :return: JSON string with a success message.
    """
    print(f"Sending email to {recipient}...")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    return json.dumps({"message": f"Email successfully sent to {recipient}."})


def send_email_to_recipient_name(recipient: str, subject: str, body: str) -> str:
    """
    Mocks sending an email addressed to a recipient by name.

    :param recipient: Name of the recipient.
    :param subject: Subject of the email.
    :param body: Body of the email.
    :return: JSON string with a success message.
    """
    print(f"Sending email to {recipient}...")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    return json.dumps({"message": f"Email successfully sent to {recipient}."})


def add_two_numbers(a: int, b: int) -> str:
    """
    Adds two integers and returns the sum as a JSON string.

    :param a: First integer.
    :param b: Second integer.
    :return: JSON string with the sum result.
    """
    result = a + b
    return json.dumps({"result": result})


def celsius_to_fahrenheit(celsius: float) -> str:
    """
    Converts a Celsius temperature to Fahrenheit.

    :param celsius: Temperature in degrees Celsius.
    :return: JSON string containing the Fahrenheit value.
    """
    fahrenheit = (celsius * 9 / 5) + 32
    return json.dumps({"fahrenheit": fahrenheit})


def invert_boolean_flag(flag: bool) -> str:
    """
    Inverts a given boolean value.

    :param flag: Boolean flag to invert.
    :return: JSON string with the inverted flag value.
    """
    toggled = not flag
    return json.dumps({"toggled_flag": toggled})


def merge_two_dictionaries(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> str:
    """
    Merges two dictionaries into one.

    :param dict1: The first dictionary.
    :param dict2: The second dictionary.
    :return: JSON string with the merged dictionary.
    """
    merged = dict1.copy()
    merged.update(dict2)
    return json.dumps({"merged_dict": merged})


def retrieve_user_information(user_id: int) -> str:
    """
    Retrieves mock user information based on a user ID.

    :param user_id: Unique identifier for the user.
    :return: JSON string with user information or an error message.
    """
    mock_users = {
        1: {"name": "Alice", "email": "alice@example.com"},
        2: {"name": "Bob", "email": "bob@example.com"},
        3: {"name": "Charlie", "email": "charlie@example.com"},
    }
    user_info = mock_users.get(user_id, {"error": "User not found."})
    return json.dumps({"user_info": user_info})


def find_longest_words(sentences: List[str]) -> str:
    """
    Identifies the longest word in each provided sentence.

    :param sentences: A list of sentences.
    :return: JSON string mapping each sentence to its longest word.
    """
    if not sentences:
        return json.dumps({"error": "The list of sentences is empty"})

    longest_words = {}
    for sentence in sentences:
        words = sentence.split()
        longest_words[sentence] = max(words, key=len) if words else ""

    return json.dumps({"longest_words": longest_words})


def summarize_record_values(records: List[Dict[str, int]]) -> str:
    """
    Processes a list of records and computes the sum of integer values in each record.

    :param records: A list of dictionaries mapping strings to integers.
    :return: JSON string containing the sum for each record.
    """
    sums = [sum(record.values()) for record in records]
    return json.dumps({"sums": sums})


# Updated user functions set
user_functions: Set[Callable[..., Any]] = {
    get_current_datetime,
    create_text_file_from_string,
    get_weather_by_location,
    send_email_to_address,
    send_email_to_recipient_name,
    add_two_numbers,
    celsius_to_fahrenheit,
    invert_boolean_flag,
    merge_two_dictionaries,
    retrieve_user_information,
    find_longest_words,
    summarize_record_values,
}
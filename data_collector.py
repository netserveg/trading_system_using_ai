"""
data_collector.py

Description:
    This script contains a collection of functions designed to handle the collection, processing, and storage of financial data, including OHLC data, technical indicators, and news data. It integrates with a MySQL database to store and manage this data efficiently. The functions support inserting and updating data related to technical indicators (e.g., RSI, MACD, SMA, Bollinger Bands, EMA, Fibonacci Retracement), fetching and processing news using Selenium, and cleaning raw data before insertion into the database.

    The script also includes routes for receiving OHLC data through HTTP POST requests, as well as background tasks to fetch related news asynchronously using Selenium. These functions provide a robust backend for financial data analysis.

Version: v1.00
"""


from flask import Flask, request, jsonify
from datetime import datetime
import pymysql
import re
import json
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup
import threading
from waitress import serve  # Import Waitress

app = Flask(__name__)

# Suite ID: ts1 - Function to log trade action and its details
# This function records information about each trade action into the MySQL database.
# The data logged includes the type of action, currency pair, indicators used,
# the result of the trade, position size, risk level, and trading strategy applied.
# Required Libraries: pymysql

def connect_db():
    """
    Establishes a connection to the MySQL database.

    This function attempts to connect to a MySQL database using the provided
    connection parameters (host, user, password, and database).
    If the connection is successful, it returns the connection object.
    If the connection fails, an error message is printed, and an exception is raised.

    Returns:
        connection (pymysql.connect): A connection object to interact with the database.

    Raises:
        pymysql.Error: If the connection fails, an exception is raised with the error message.
    """
    try:
        # Attempt to connect to the database with the provided credentials
        connection = pymysql.connect(
            host="localhost",  # Host where the database server is running
            user="root",  # Database username
            password="",  # Database password
            database="trading_data"  # Database name to connect to
        )

        # Return the connection object if successful
        return connection
    except pymysql.Error as err:
        # Print the error if the connection fails and raise the exception
        print(f"Database connection failed: {err}")
        raise
#-------------------------------------------------------------------------------------------------------- 1

# Suite ID: dc2 - Insert OHLC Data into Database
# This function inserts OHLC data (Open, High, Low, Close) along with volume and currency pair into the database.
# It returns the ID of the last inserted row, which corresponds to the OHLC entry.
# Required Libraries: pymysql

def insert_ohlc_data(timestamp, open_price, high, low, close, volume, currency_pair):
    """
    Inserts OHLC data (timestamp, open, high, low, close, volume, currency_pair) into the database.
    If successful, it returns the ID of the inserted OHLC data row.

    Args:
        timestamp (str): The timestamp for the OHLC data.
        open_price (float): The opening price for the OHLC data.
        high (float): The highest price for the OHLC data.
        low (float): The lowest price for the OHLC data.
        close (float): The closing price for the OHLC data.
        volume (float): The volume associated with the OHLC data.
        currency_pair (str): The currency pair associated with the OHLC data.

    Returns:
        int: The ID of the last inserted row (OHLC ID) if successful.
    """
    db = None
    cursor = None
    try:
        # Establish a connection to the database
        db = connect_db()
        cursor = db.cursor()

        # Prepare the query to insert OHLC data
        query = """INSERT INTO ohlc_data (timestamp, open, high, low, close, volume, currency_pair)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""

        # Execute the query with the provided OHLC data
        cursor.execute(query, (timestamp, open_price, high, low, close, volume, currency_pair))
        db.commit()

        print("OHLC Data inserted successfully into the database.")

        # Return the ID of the last inserted row (OHLC ID)
        return cursor.lastrowid

    except pymysql.MySQLError as err:
        # Handle any database-related errors
        print(f"Database error: {err}")
    except Exception as e:
        # Handle any unexpected errors
        print(f"Unexpected error: {e}")
    finally:
        # Ensure the cursor and connection are properly closed
        if cursor:
            cursor.close()
        if db:
            db.close()
#-------------------------------------------------------------------------------------------------------- 2

# Suite ID: dc3 - Insert EMA Data into Database
# This function inserts Exponential Moving Average (EMA) data into the database.
# It stores the OHLC ID, EMA value, and EMA period.
# Required Libraries: pymysql

def insert_ema_data(ohlc_id, ema_value, ema_period):
    """
    Inserts EMA data (OHLC ID, EMA value, and EMA period) into the database.

    Args:
        ohlc_id (int): The ID of the related OHLC data.
        ema_value (float): The computed Exponential Moving Average (EMA) value.
        ema_period (int): The period over which the EMA is calculated.

    Returns:
        None: This function does not return a value. It inserts data into the database.
    """
    db = None
    cursor = None
    try:
        # Establish a connection to the database
        db = connect_db()
        cursor = db.cursor()

        # Prepare the query to insert EMA data
        query = """INSERT INTO ema_data (ohlc_id, ema_value, ema_period)
                   VALUES (%s, %s, %s)"""

        # Execute the query with the provided EMA data
        cursor.execute(query, (ohlc_id, ema_value, ema_period))
        db.commit()

        print("EMA data inserted successfully into the database.")

    except pymysql.MySQLError as err:
        # Handle any database-related errors
        print(f"Database error: {err}")
    except Exception as e:
        # Handle any unexpected errors
        print(f"Unexpected error: {e}")
    finally:
        # Ensure the cursor and connection are properly closed
        if cursor:
            cursor.close()
        if db:
            db.close()
#-------------------------------------------------------------------------------------------------------- 3

# Suite ID: dc4 - Insert Fibonacci Retracement Data into Database
# This function inserts Fibonacci retracement levels (23.6%, 38.2%, 50%, 61.8%, 100%)
# into the database, along with the associated OHLC ID.
# Required Libraries: pymysql

def insert_fibonacci_data(ohlc_id, fib_23_6, fib_38_2, fib_50, fib_61_8, fib_100):
    """
    Inserts Fibonacci retracement data (associated with OHLC data) into the database.

    Args:
        ohlc_id (int): The ID of the related OHLC data.
        fib_23_6 (float): The Fibonacci retracement level at 23.6%.
        fib_38_2 (float): The Fibonacci retracement level at 38.2%.
        fib_50 (float): The Fibonacci retracement level at 50%.
        fib_61_8 (float): The Fibonacci retracement level at 61.8%.
        fib_100 (float): The Fibonacci retracement level at 100%.

    Returns:
        None: This function does not return a value. It inserts data into the database.
    """
    db = None
    cursor = None
    try:
        # Establish a connection to the database
        db = connect_db()
        cursor = db.cursor()

        # Prepare the query to insert Fibonacci retracement data
        query = """INSERT INTO fibonacci_retracement_data (ohlc_id, fib_23_6, fib_38_2, fib_50, fib_61_8, fib_100)
                   VALUES (%s, %s, %s, %s, %s, %s)"""

        # Execute the query with the provided Fibonacci retracement levels
        cursor.execute(query, (ohlc_id, fib_23_6, fib_38_2, fib_50, fib_61_8, fib_100))
        db.commit()

        print("Fibonacci Retracement data inserted successfully into the database.")

    except pymysql.MySQLError as err:
        # Handle any database-related errors
        print(f"Database error: {err}")
    except Exception as e:
        # Handle any unexpected errors
        print(f"Unexpected error: {e}")
    finally:
        # Ensure the cursor and connection are properly closed
        if cursor:
            cursor.close()
        if db:
            db.close()
#-------------------------------------------------------------------------------------------------------- 4

# Suite ID: dc5 - Insert Bollinger Band Data into Database
# This function inserts Bollinger Band data (upper, middle, and lower bands)
# along with the period and deviation into the database, associated with a specific OHLC ID.
# Required Libraries: pymysql

def insert_bollinger_band_data(ohlc_id, upper_band, middle_band, lower_band, bb_period, bb_deviation):
    """
    Inserts Bollinger Band data (upper, middle, lower bands, period, deviation) into the database.

    Args:
        ohlc_id (int): The ID of the related OHLC data.
        upper_band (float): The upper Bollinger Band value.
        middle_band (float): The middle Bollinger Band value (usually the moving average).
        lower_band (float): The lower Bollinger Band value.
        bb_period (int): The period over which the Bollinger Bands are calculated.
        bb_deviation (float): The number of standard deviations used to calculate the bands.

    Returns:
        None: This function does not return a value. It inserts data into the database.
    """
    db = None
    cursor = None
    try:
        # Establish a connection to the database
        db = connect_db()
        cursor = db.cursor()

        # Prepare the query to insert Bollinger Band data
        query = """INSERT INTO bollinger_band_data (ohlc_id, upper_band, middle_band, lower_band, bb_period, bb_deviation)
                   VALUES (%s, %s, %s, %s, %s, %s)"""

        # Execute the query with the provided Bollinger Band data
        cursor.execute(query, (ohlc_id, upper_band, middle_band, lower_band, bb_period, bb_deviation))
        db.commit()

        print("Bollinger Band data inserted successfully into the database.")

    except pymysql.MySQLError as err:
        # Handle any database-related errors
        print(f"Database error: {err}")
    except Exception as e:
        # Handle any unexpected errors
        print(f"Unexpected error: {e}")
    finally:
        # Ensure the cursor and connection are properly closed
        if cursor:
            cursor.close()
        if db:
            db.close()
#-------------------------------------------------------------------------------------------------------- 5

# Suite ID: dc6 - Insert RSI Data into Database
# This function inserts Relative Strength Index (RSI) data into the database, along with the OHLC ID and RSI period.
# Required Libraries: pymysql

def insert_rsi_data(ohlc_id, rsi, rsi_period):
    """
    Inserts RSI data (Relative Strength Index) into the database, associated with an OHLC ID.

    Args:
        ohlc_id (int): The ID of the related OHLC data.
        rsi (float): The computed RSI value.
        rsi_period (int): The period over which the RSI is calculated.

    Returns:
        None: This function does not return a value. It inserts data into the database.
    """
    db = None
    cursor = None
    try:
        # Establish a connection to the database
        db = connect_db()
        cursor = db.cursor()

        # Prepare the query to insert RSI data
        query = """INSERT INTO rsi_data (ohlc_id, rsi, rsi_period)
                   VALUES (%s, %s, %s)"""

        # Execute the query with the provided RSI data
        cursor.execute(query, (ohlc_id, rsi, rsi_period))
        db.commit()

        print("RSI data inserted successfully into the database.")

    except pymysql.MySQLError as err:
        # Handle any database-related errors
        print(f"Database error: {err}")
    except Exception as e:
        # Handle any unexpected errors
        print(f"Unexpected error: {e}")
    finally:
        # Ensure the cursor and connection are properly closed
        if cursor:
            cursor.close()
        if db:
            db.close()
#-------------------------------------------------------------------------------------------------------- 6

# Suite ID: dc7 - Insert MACD Data into Database
# This function inserts MACD (Moving Average Convergence Divergence) data into the database,
# including the MACD value, signal line, and histogram, along with the OHLC ID.
# Required Libraries: pymysql

def insert_macd_data(ohlc_id, macd_value, macd_signal, macd_histogram):
    """
    Inserts MACD data (MACD value, signal line, and histogram) into the database.

    Args:
        ohlc_id (int): The ID of the related OHLC data.
        macd_value (float): The computed MACD value.
        macd_signal (float): The MACD signal line value.
        macd_histogram (float): The MACD histogram value (difference between MACD and signal line).

    Returns:
        None: This function does not return a value. It inserts data into the database.
    """
    db = None
    cursor = None
    try:
        # Establish a connection to the database
        db = connect_db()
        cursor = db.cursor()

        # Prepare the query to insert MACD data
        query = """INSERT INTO macd_data (ohlc_id, macd_value, macd_signal, macd_histogram)
                   VALUES (%s, %s, %s, %s)"""

        # Execute the query with the provided MACD data
        cursor.execute(query, (ohlc_id, macd_value, macd_signal, macd_histogram))
        db.commit()

        print("MACD data inserted successfully into the database.")

    except pymysql.MySQLError as err:
        # Handle any database-related errors
        print(f"Database error: {err}")
    except Exception as e:
        # Handle any unexpected errors
        print(f"Unexpected error: {e}")
    finally:
        # Ensure the cursor and connection are properly closed
        if cursor:
            cursor.close()
        if db:
            db.close()
#-------------------------------------------------------------------------------------------------------- 7

# Suite ID: dc8 - Insert SMA Data into Database
# This function inserts Simple Moving Average (SMA) data into the database, including the SMA value and period,
# along with the OHLC ID.
# Required Libraries: pymysql

def insert_sma_data(ohlc_id, sma_value, sma_period):
    """
    Inserts SMA (Simple Moving Average) data into the database, associated with an OHLC ID.

    Args:
        ohlc_id (int): The ID of the related OHLC data.
        sma_value (float): The computed SMA value.
        sma_period (int): The period over which the SMA is calculated.

    Returns:
        None: This function does not return a value. It inserts data into the database.
    """
    db = None
    cursor = None
    try:
        # Establish a connection to the database
        db = connect_db()
        cursor = db.cursor()

        # Prepare the query to insert SMA data
        query = """INSERT INTO sma_data (ohlc_id, sma_value, sma_period)
                   VALUES (%s, %s, %s)"""

        # Execute the query with the provided SMA data
        cursor.execute(query, (ohlc_id, sma_value, sma_period))
        db.commit()

        print("SMA data inserted successfully into the database.")

    except pymysql.MySQLError as err:
        # Handle any database-related errors
        print(f"Database error: {err}")
    except Exception as e:
        # Handle any unexpected errors
        print(f"Unexpected error: {e}")
    finally:
        # Ensure the cursor and connection are properly closed
        if cursor:
            cursor.close()
        if db:
            db.close()
#-------------------------------------------------------------------------------------------------------- 8

# Suite ID: dc9 - Helper Function to Clean Raw Data
# This function cleans raw data by decoding it, removing non-printable characters, and handling unwanted control characters.
# Required Libraries: re

def clean_raw_data(raw_data):
    """
    Cleans the raw input data by decoding it, removing non-ASCII characters, and cleaning up unwanted control characters.

    Args:
        raw_data (bytes): The raw data in bytes that needs to be cleaned.

    Returns:
        str: The cleaned data as a UTF-8 string.
    """
    # Decode the raw data to UTF-8 while ignoring errors
    decoded_data = raw_data.decode('utf-8', errors='ignore')

    # Remove any non-ASCII characters using regular expressions
    cleaned_data = re.sub(r'[^\x00-\x7F]+', '', decoded_data)

    # Remove specific control characters such as null bytes, carriage returns, and newlines
    cleaned_data = cleaned_data.replace('\x00', '').replace('\r', '').replace('\n', '')

    # Keep only printable characters
    cleaned_data = ''.join(char for char in cleaned_data if char.isprintable())

    # Strip leading and trailing whitespace
    cleaned_data = cleaned_data.strip()

    return cleaned_data
#-------------------------------------------------------------------------------------------------------- 9

# Suite ID: dc10 - Receive OHLC Data via HTTP POST and Insert into Database
# This route receives OHLC data, cleans it, extracts relevant fields, and stores the data
# in the database. Additionally, it triggers a background thread to fetch related news.
# Required Libraries: json, re, datetime, threading, Flask (request, jsonify)

@app.route('/ohlc_data', methods=['POST'])
def receive_ohlc_data():
    """
    Receives OHLC (Open, High, Low, Close) data along with various technical indicators via a POST request.
    The data is cleaned, validated, and inserted into the database. A background thread is initiated to
    fetch related news.

    Returns:
        json: A response indicating the success or failure of the operation.
    """
    try:
        # Get the raw data from the incoming request
        raw_data = request.data

        # Clean the raw data by removing unwanted characters and decoding
        clean_data = clean_raw_data(raw_data)

        try:
            # Parse the cleaned data as JSON
            data = json.loads(clean_data)
        except Exception as e:
            print(f"JSON decoding error: {e}")
            return jsonify({"error": "Invalid JSON format"}), 400

        # Extract fields from the parsed JSON data
        currency_pair = data.get("currency_pair")
        timestamp = data.get('timestamp')
        open_price = data.get('open')
        high = data.get('high')
        low = data.get('low')
        close = data.get('close')
        volume = data.get('volume')
        rsi = data.get('rsi')
        rsi_period = data.get('rsi_period', 14)
        macd_value = data.get('macd_value')
        macd_signal = data.get('macd_signal')
        macd_histogram = data.get('macd_histogram')
        sma = data.get('sma')
        sma_period = data.get('sma_period', 14)
        upper_band = data.get('upper_band')  # Bollinger Bands
        middle_band = data.get('middle_band')
        lower_band = data.get('lower_band')
        bb_period = data.get('bb_period', 20)  # Default period for Bollinger Bands
        bb_deviation = data.get('bb_deviation', 2)  # Default deviation for Bollinger Bands
        ema_value = data.get('ema_value')
        ema_period = data.get('ema_period', 14)

        # Fibonacci retracement levels
        fib_23_6 = data.get('fib_23_6')
        fib_38_2 = data.get('fib_38_2')
        fib_50 = data.get('fib_50')
        fib_61_8 = data.get('fib_61_8')
        fib_100 = data.get('fib_100')

        # Check if all required fields are present
        if not all([currency_pair, timestamp, open_price, high, low, close, volume, rsi, macd_value, macd_signal,
                    macd_histogram, sma, upper_band, middle_band, lower_band, ema_value, fib_23_6, fib_38_2, fib_50,
                    fib_61_8, fib_100]):
            print("Missing or invalid fields in received data.")
            return jsonify({"error": "Invalid data"}), 400

        # Convert the timestamp to a datetime object
        timestamp = datetime.strptime(timestamp, '%Y.%m.%d %H:%M')
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime to string

        # Trim the currency pair to the first six characters
        currency_pair = currency_pair[:6]

        # Insert OHLC data into the database and retrieve the OHLC ID
        ohlc_id = insert_ohlc_data(timestamp_str, open_price, high, low, close, volume, currency_pair)
        if not ohlc_id:
            print("Failed to insert OHLC data.")
            return jsonify({"error": "Database error"}), 500

        # Insert various technical indicators related to the OHLC data
        insert_rsi_data(ohlc_id, rsi, rsi_period)
        insert_macd_data(ohlc_id, macd_value, macd_signal, macd_histogram)
        insert_sma_data(ohlc_id, sma, sma_period)
        insert_bollinger_band_data(ohlc_id, upper_band, middle_band, lower_band, bb_period, bb_deviation)
        insert_ema_data(ohlc_id, ema_value, ema_period)
        insert_fibonacci_data(ohlc_id, fib_23_6, fib_38_2, fib_50, fib_61_8, fib_100)

        # Start a background thread to fetch related news (non-blocking)
        threading.Thread(target=fetch_news_with_selenium_and_store, daemon=True).start()

        # Return a success response
        return jsonify({"status": "success"}), 200

    except Exception as e:
        # Handle unexpected errors and return an internal server error
        print(f"Error processing data: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
#-------------------------------------------------------------------------------------------------------- 10

# Suite ID: dc11 - Fetch News Using Selenium WebDriver and Store in Database
# This function fetches news from the Forex Factory calendar, processes it, and stores it in the database.
# Required Libraries: selenium, datetime, time, re, BeautifulSoup, threading

edge_driver_path = "msedgedriver.exe"  # Update with the correct path to the Edge WebDriver

def fetch_news_with_selenium():
    # Set up Edge options for Selenium WebDriver
    options = webdriver.EdgeOptions()
    options.add_argument("--headless")  # Run browser in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )  # Add user-agent string

    # Set up the Edge WebDriver
    service = Service(edge_driver_path)
    driver = webdriver.Edge(service=service, options=options)

    try:
        # Load the Forex Factory calendar page
        driver.get("https://www.forexfactory.com/calendar.php")

        # Wait for the calendar table or an event to load
        WebDriverWait(driver, 60).until(
            ec.presence_of_element_located((By.CLASS_NAME, "calendar__row"))
        )

        # Fetch the page source
        page_source = driver.page_source

        # Save HTML locally for debugging
        with open("page_source_debug.html", "w", encoding="utf-8") as file:
            file.write(page_source)

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")

        # Find all rows in the calendar table
        news_rows = soup.find_all("tr", class_="calendar__row")

        if not news_rows:
            print("Could not find any news events in the page source.")
            return []

        news_data = []
        current_date = None  # Initialize variable to track the current date
        current_time = "00:00"  # Default time

        for row in news_rows:
            try:
                # Extract the date if it exists in this row (or reuse previous date)
                date_cell = row.find("td", class_="calendar__date")
                if date_cell and date_cell.get_text(strip=True):
                    current_date = date_cell.get_text(strip=True)

                # If no date is found, reuse the last known date
                if not current_date:
                    # Skip the row due to missing date
                    continue

                # Extract the time if it exists (or reuse the last known time)
                time_cell = row.find("td", class_="calendar__time")
                raw_time = time_cell.get_text(strip=True) if time_cell else ""

                # If the time is missing, use the previous time (current_time)
                if not raw_time:
                    raw_time = current_time

                # Update current_time with the latest time
                current_time = raw_time

                # If raw_time is a special case (like "Day 1", "Day 2", "Tentative", "All Day"), set it to "00:00"
                if raw_time in ["Day 1", "Day 2", "Tentative", "All Day"]:
                    raw_time = "00:00"

                # Handle time parsing to account for both 12-hour and 24-hour formats
                try:
                    # Try to parse time in 12-hour format with AM/PM (e.g., 02:30PM)
                    time_obj = datetime.strptime(raw_time, "%I:%M%p")
                except ValueError:
                    try:
                        # If 12-hour format fails, try to parse in 24-hour format (e.g., 14:30)
                        time_obj = datetime.strptime(raw_time, "%H:%M")
                    except ValueError:
                        print(f"Error parsing time '{raw_time}': time data does not match expected format.")
                        continue

                # Convert the time object back to a string in 12-hour format with AM/PM
                formatted_time = time_obj.strftime("%I:%M%p") if time_obj else "00:00"

                # Extract event and other news details
                event_cell = row.find("td", class_="calendar__event")
                event = event_cell.get_text(strip=True) if event_cell else "N/A"

                impact_cell = row.find("td", class_="calendar__impact")
                impact_icon = impact_cell.find("span") if impact_cell else None
                impact = impact_icon.get("title") if impact_icon else "N/A"

                currency_cell = row.find("td", class_="calendar__currency")
                currency = currency_cell.get_text(strip=True) if currency_cell else "N/A"

                actual_cell = row.find("td", class_="calendar__actual")
                actual = actual_cell.get_text(strip=True) if actual_cell else "N/A"

                forecast_cell = row.find("td", class_="calendar__forecast")
                forecast = forecast_cell.get_text(strip=True) if forecast_cell else "N/A"

                previous_cell = row.find("td", class_="calendar__previous")
                previous = previous_cell.get_text(strip=True) if previous_cell else "N/A"

                # Skip records with invalid or missing essential information
                if event in ["Edit", "Copy", "Delete"] or impact == "N/A" or currency == "N/A":
                    continue

                # Append valid news data to the list
                news_data.append({
                    "date": current_date,
                    "time": formatted_time,
                    "event": event,
                    "impact": impact,
                    "currency": currency,
                    "actual": actual,
                    "forecast": forecast,
                    "previous": previous
                })

            except Exception as e:
                print(f"Error processing row: {e}")
                continue

        # Insert the collected news data into the database
        if news_data:
            insert_news_data(news_data)

    except Exception as e:
        print(f"Error during news fetching: {e}")

    finally:
        driver.quit()

#-------------------------------------------------------------------------------------------------------- 11

# Suite ID: dc12 - Fetch News with Selenium and Store in Database
# This helper function fetches news asynchronously using Selenium, processes the data,
# and stores it into the database.
# Required Libraries: threading

def fetch_news_with_selenium_and_store():
    """
    Fetches the latest news using Selenium and stores the data in the database.
    This function is executed in a background thread for non-blocking execution.
    """
    try:
        # Fetch the news data using Selenium
        news_data = fetch_news_with_selenium()

        # If news data was successfully fetched, insert it into the database
        if news_data:
            insert_news_data(news_data)
            print("News data successfully saved to the database.")
    except Exception as e:
        # Handle any errors that may occur during the news fetching process
        print(f"Error fetching news in background: {e}")

#-------------------------------------------------------------------------------------------------------- 12

# Suite ID: dc13 - Insert News Data into the Database
# This function inserts parsed news data into the database, ensuring no duplicates and handling errors.
# Required Libraries: pymysql

def insert_news_data(news_data):
    """
    Inserts parsed news data into the database.
    - Skips records with invalid or missing time values.
    - Avoids duplicate entries by checking against title and news time.
    - Inserts `impact_id = 1` when `impact` is "Low Impact Expected".

    Args:
        news_data (list): List of news items, each containing details like time, date, event, etc.
    """
    db = None
    cursor = None
    try:
        # Establish a connection to the database
        db = connect_db()
        cursor = db.cursor()

        # Iterate through each news item in the provided list
        for news_item in news_data:
            # Extract time and date from the news item
            raw_time = news_item['time']
            current_date = news_item['date']

            # Skip news items with invalid or empty time or date
            if not raw_time or not current_date:
                # Skip invalid news item
                continue

            # Add the current year to the date string
            current_year = datetime.now().year
            date_str = f"{current_year} {current_date}"

            try:
                # Attempt to parse the date and time strings
                date_obj = datetime.strptime(date_str, "%Y %a%b %d")

                # Handle the time string, ensuring it's in the 24-hour format
                if 'AM' in raw_time or 'PM' in raw_time:
                    time_obj = datetime.strptime(raw_time, "%I:%M%p")
                else:
                    time_obj = datetime.strptime(raw_time, "%H:%M")

                # Combine the date and time to get the full datetime
                news_datetime = datetime.combine(date_obj.date(), time_obj.time())
                news_time = news_datetime.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Error combining date and time: {e}")
                continue  # Skip this news item if there's a date/time error

            # Determine the impact_id based on the impact value
            impact_id = None
            if news_item['impact'] == "Low Impact Expected":
                impact_id = 1
            elif news_item['impact'] == "Medium Impact Expected":
                impact_id = 2  # Assuming you want to set a different value for medium impact
            elif news_item['impact'] == "High Impact Expected":
                impact_id = 3  # Assuming you want to set a different value for high impact

            # Check if the news event already exists to avoid duplicates
            cursor.execute("SELECT COUNT(*) FROM news_data WHERE title = %s AND news_time = %s",
                           (news_item['event'], news_time))
            exists = cursor.fetchone()[0]

            # If the news does not exist, insert it
            if exists == 0:
                query = """INSERT INTO news_data (news_time, title, impact, currency, actual, forecast, previous, impact_id)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (news_time, news_item['event'], news_item['impact'],
                                       news_item['currency'], news_item['actual'], news_item['forecast'],
                                       news_item['previous'], impact_id))
                db.commit()
                print(f"News inserted: {news_item['event']}")

    except pymysql.MySQLError as err:
        print(f"Database error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Close the database cursor and connection
        if cursor:
            cursor.close()
        if db:
            db.close()
#-------------------------------------------------------------------------------------------------------- 13

# Suite ID: dc14 - Run the app using waitress with Flask
# This block runs the Flask app using Waitress, which is a production WSGI server.
# Required Libraries: waitress

if __name__ == '__main__':
    # Run the app on 127.0.0.1 at port 80
    serve(app, host='127.0.0.1', port=80)
#-------------------------------------------------------------------------------------------------------- 14
import time
import requests
from plyer import notification
from datetime import datetime

# edit markets to add/remove market pairs for monitoring, optionally adjust check and notification intervals

check_interval = 5  # seconds plus some time to handle all requests in round
notification_interval = 60  # minutes between posible notifications for each market
notification_timers = {}
notifications_enabled = False
continue_looping = True
markets = {  # ticker -> (min, max) inclusive ranges
    "BTCUSDT": (40000, 42000),
    "ETHUSDT": (2000, 2500)
}




def get_last_price_from_binance_api(ticker):    
    apiurl = "https://api.binance.com/api/v3/ticker/price?symbol="
    error_message = None
    try:
        response = requests.get(apiurl + ticker)
        response.raise_for_status()  # raise an HTTPError for 4XX/5XX status codes
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err} - Status code: {response.status_code}"
    except requests.exceptions.ConnectionError as conn_err:
        error_message = f"Connection error occurred: {conn_err}"
    except requests.exceptions.Timeout as timeout_err:
        error_message = f"Timeout error occurred: {timeout_err}"
    except requests.exceptions.RequestException as req_err:
        error_message = f"Request error occurred: {req_err}"
    except Exception as e:
        error_message = f"Unexpected error: {e}"
    
    handle_errors(error_message if error_message else "Unknown error occured")
    return None
        

def check_price(ticker):  # gets and validates data for specific pair and sends them for range check
    response_data = get_last_price_from_binance_api(ticker)
    if response_data and "symbol" in response_data and "price" in response_data:
        if response_data["symbol"] == ticker:
            price = float(response_data["price"])
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"{current_time} - {ticker} price: {price}")  # for in-terminal quick info
            handle_notifications(ticker, price)  # range checks
        else:
            handle_errors(f"Ticker mismatch: expected {ticker}, got {response_data['symbol']}")
    else:
        handle_errors(f"Invalid response structure for {ticker}")


def send_notification(n_title, n_text, n_duration):
    if notifications_enabled:  # sends Windows notification
        notification.notify(
                title = n_title,
                message = n_text,
                timeout = n_duration
        )
    else:  # Prints just to terminal
        print(f"notification sent: {n_title}, {n_text}, {n_duration}")


def handle_notifications(ticker, price):  # checks if price is in range, if not sends notification    
    if price < markets[ticker][0] or price > markets[ticker][1]:
        current_time = time.time()
        if notification_timers[ticker] is None or current_time > notification_timers[ticker] + (notification_interval * 60):  # to prevent notification spam
            notification_timers[ticker] = current_time
            send_notification(f"{ticker} price alert", f"last price of {ticker} is {price}", 60)

            
def handle_errors(error_message):  # barebones implementation, any error sends notification and stop monitoring
    global continue_looping
    continue_looping = False
    send_notification("Price alert error", f"{error_message}, monitoring terminated", 120)


def make_checks():
    for key in markets.keys():  # prepares timers for all monitored pairs
        notification_timers[key] = None
    try:
        while continue_looping:  # main loop
            for ticker in markets.keys():
                check_price(ticker)            
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("Terminated by user (Crtl+C)")


if __name__ == "__main__":
    make_checks()   
    


from tgtg import TgtgClient
from json import load, dump
import requests
import schedule
import time
import os

print("Script execution starts")

try:
    # Credential handling heroku
    tgtg_email = os.environ['TGTG_EMAIL']
    print(f"tgtg_email: {tgtg_email}")
except:
    print("Not loading credentials from Heroku.")


# Credential handling local version
# Load tgtg account credentials from a hidden file
f = open('telegram.json',)
telegram = load(f)
f.close()

# Load tgtg account credentials from a hidden file
f = open('credentials.json',)
credentials = load(f)
f.close()

# Create the tgtg client with my credentials
client = TgtgClient(email=credentials['email'], password=credentials['password'])

# Init the favourites in stock list as a global variable
favourites_in_stock = list()

# Helper function: Send a message with the specified telegram bot on the specified chat
# Follow this article to figure out a specific chatID: https://medium.com/@ManHay_Hong/how-to-create-a-telegram-bot-and-send-messages-with-python-4cf314d9fa3e
def telegram_bot_sendtext(bot_message):

    bot_token = telegram["bot_token"]
    bot_chatID = telegram["bot_chatID"]
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()

def fetch_stock_from_api(api_result):
    """
    For fideling out the view important information out of the api response
    """
    new_api_result = list()
    # Go through all favorites linked to the account,that are returned with the api
    for i in range(len(api_result)):
        current_fav = dict()
        current_fav['item_id'] = api_result[i]['item']['item_id']
        current_fav['store_name'] = api_result[i]['store']['store_name']
        current_fav['items_available'] = api_result[i]['items_available']
        new_api_result.append(current_fav)

    return new_api_result

def routine_check():
    """
    Function that gets called via schedule to get the api numbers and send a telegram message in case of a change
    """

    # Get the global variable of items in stock
    global favourites_in_stock

    # Get all favorite items
    api_response = client.get_items()
    new_api_result = fetch_stock_from_api(api_response)

    # Go through all favourite items and compare the stock
    list_of_item_ids = [fav['item_id'] for fav in new_api_result]
    for item_id in list_of_item_ids:
        try:
            old_stock = [item['items_available'] for item in favourites_in_stock if item['item_id'] == item_id][0]
        except:
            old_stock = 0
            print("An exception occurred: The item_id was not known as a favorite before")

        new_stock = [item['items_available'] for item in new_api_result if item['item_id'] == item_id][0]

        # Check, if the stock has changed. Send a message if so.
        if new_stock != old_stock:
            # Prepare a generic string, but with the important info
            message = f"There was a change in stock for the surprise bags at {[item['store_name'] for item in new_api_result if item['item_id'] == item_id][0] }. The old stock size was {old_stock}, the new stock size is {new_stock}."
            telegram_bot_sendtext(message)

    # Reset the global information with the newest fetch
    favourites_in_stock = new_api_result

    # Print out some maintenance info in the terminal
    print(f"API run at {time.ctime(time.time())} successful. Current stock:")
    for item_id in list_of_item_ids:
        print(f"{[item['store_name'] for item in new_api_result if item['item_id'] == item_id][0]}:\
         {[item['items_available'] for item in new_api_result if item['item_id'] == item_id][0]}")

# Use schedule to set up a recurrent checking
schedule.every(3).minutes.do(routine_check)

while True:
    # run_pending
    schedule.run_pending()
    time.sleep(1)
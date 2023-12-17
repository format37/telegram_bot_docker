import os
import shutil
import time
from datetime import datetime
import logging

# Set logging level info
logging.basicConfig(level=logging.INFO)
# init logger
logger = logging.getLogger(__name__)

# Replace these with your specific paths
parent_directory = '/archive'  # Replace 'B' with your desired directory
file_to_move = '/blocked.csv'  # Replace with the path of your file

while True:
    # Get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    destination_directory = os.path.join(parent_directory, current_date)

    # Create the destination directory if it doesn't exist
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    # Move the file
    if os.path.exists(file_to_move):
        shutil.move(file_to_move, destination_directory)
        # print(f"File moved to {destination_directory}")
        logger.info(f"File moved to {destination_directory}")
        # Save a new empty file
        open(file_to_move, 'a').close()
    else:
        # print("File not found.")
        logger.info("File not found.")

    # Wait for one day (24 hours)
    time.sleep(86400)  # 86400 seconds in a day

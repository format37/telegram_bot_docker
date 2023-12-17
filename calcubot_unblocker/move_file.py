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
    if os.path.exists(file_to_move) and \
        not os.path.exists(os.path.join(destination_directory, file_to_move)):
        logger.info(f"Moving file {file_to_move} to {destination_directory}")
        # shutil.move(file_to_move, destination_directory)
        # Copy the file
        shutil.copy(file_to_move, destination_directory)
        # Write emty string to file to avoid error
        with open(file_to_move, 'w') as f:
            f.write("")
            logger.info(f"File moved to {destination_directory}")
        # print(f"File moved to {destination_directory}")        
    else:
        # print("File not found.")
        logger.info("File not found or destination file already exists.")

    # Wait for one day (24 hours)
    time.sleep(86400)  # 86400 seconds in a day

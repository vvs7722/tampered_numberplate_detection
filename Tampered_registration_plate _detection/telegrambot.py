from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import cv2
from matplotlib import pyplot as plt
import numpy as np
import imutils
import easyocr

data={
    "H982FKL":"Porsche 928",
    "TS08JE6588":"Kia seltos",
    "TS08JE5600":"Kia seltos"
}

def check_by_number(number,name):
    if number.upper() in data.keys():
        if data[number.upper()].upper().replace(" ","")==name.upper():
            return "This is an original number"
        else:
            return "This is a tampered number"
    else:
        return "Data not Available"




def check(image_path):
    
    ## 1. Read in Image, Grayscale and Blur
    #image_path=r"image5.jpg"
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    plt.imshow(cv2.cvtColor(gray, cv2.COLOR_BGR2RGB))


    ## 2. Apply filter and find edges for localization
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17) #Noise reduction
    edged = cv2.Canny(bfilter, 30, 200) #Edge detection
    plt.imshow(cv2.cvtColor(edged, cv2.COLOR_BGR2RGB))
    ## 3. Find Contours and Apply Mask
    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break
    location
    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [location], 0,255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)
    plt.imshow(cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB))
    (x,y) = np.where(mask==255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2+1, y1:y2+1]
    plt.imshow(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
    ## 4. Use Easy OCR To Read Text
    reader = easyocr.Reader(['en'])
    result = reader.readtext(cropped_image)
    text = ""

    for i in result:
        text += i[1]

    if "_" in text:
        text = text.replace("_", "")
    if " " in text:
        text=text.replace(" ","")
    if "." in text:
        text=text.replace(".","")
    if text[0]=="I":
        text="T"+text[1:]
    text=text.upper()
    print(text)

    ## 5. Render Result
    #text = result[0][-2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    res = cv2.putText(img, text=text, org=(approx[0][0][0], approx[1][0][1]+60), fontFace=font, fontScale=1, color=(0,255,0), thickness=2, lineType=cv2.LINE_AA)
    res = cv2.rectangle(img, tuple(approx[0][0]), tuple(approx[2][0]), (0,255,0),3)
    plt.imshow(cv2.cvtColor(res, cv2.COLOR_BGR2RGB))
    ## 6. Removing spaces
    x=text.split(" ")
    text="".join(x)
    print(y)
    #Original data is stored in the form of dictionary
    if text not in data.keys():
        return "Data Not Available"
    #print(data[text])
    ## 7.Azure Custom Vision Api Interaction
    import requests

    endpoint_image = "endpoint"
    prediction_key = "prediction key"
    # Set headers
    headers_image = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/octet-stream",
    }



    # Read the image file as bytes
    image_data = open(image_path, "rb").read()

    # Make the prediction request for image file
    response_image = requests.post(endpoint_image, headers=headers_image, data=image_data)

    # Handle the response
    if response_image.status_code == 200:
        results_image = response_image.json()
        # Process the results as needed
        highest_prediction_image = max(results_image['predictions'], key=lambda x: x['probability'])
        print(f"The highest probability prediction is: {highest_prediction_image['tagName']} with probability {highest_prediction_image['probability']:.2%}")
        if data[text] == highest_prediction_image['tagName']:
            return "This is an Original Vehicle"
        else:
            return "This is a Tampered/Fake Number plate"
    else:
        print(f"Prediction failed with status code {response_image.status_code}")
        print(response_image.text)
# Function to handle the /start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome,click /help to know what you can do")

# Function to handle the /help command
def help(update: Update, context: CallbackContext):
    update.message.reply_text("Please provide the number plate either by typing it or sending a photo.\nEntering the number plate details is recomended\nFor text, use the syntax:\n carnumber carname /check. If you want to check a photo directly, simply send the photo")


# Function to handle the /sendimage command
def send_image(update: Update, context: CallbackContext):
    # Check if the user sent a photo
    if update.message.photo:
        # Get the photo file ID
        photo_id = update.message.photo[-1].file_id
        # Send the same photo as a reply
        update.message.reply_photo(photo=photo_id)
    else:
        update.message.reply_text("Please send a photo to use this command.")

# Function to handle the /menu command
def menu(update: Update, context: CallbackContext):
    menu_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - For syntax\n"
        "/sendimage - Send a predefined image directly\n"
        "/menu - Display this menu"
    )
    update.message.reply_text(menu_text)

# Function to handle incoming photos
def handle_photo(update: Update, context: CallbackContext):
    # Get the photo file ID
    photo_id = update.message.photo[-1].file_id

    # Get file details using the file ID
    file = context.bot.get_file(photo_id)

    # Access file details
    file_id = file.file_id
    file_path = file.file_path
    file_url = file.file_path

    # Print or use the file details as needed
    print(f"File ID: {file_id}")
    print(f"File Path: {file_path}")
    print(f"File URL: {file_url}")
    file.download("file1.jpeg")
    print(True)
    result=check(r"file1.jpeg")

    # You can also download the file if needed
    # file.download('downloaded_photo.jpg')

    update.message.reply_text(result)

# Function to handle unrecognized text messages
def unknown_text(update: Update, context: CallbackContext):
    user_message = update.message.text.lower()
    if "/check" in user_message:
        text=user_message.split(" ")
        car_number=text[0]
        car_name=text[1]
        result=check_by_number(car_number,car_name)
        update.message.reply_text(result)
    else:
        update.message.reply_text("Sorry I can't recognize you, you said '%s'" % update.message.text)

# Function to handle unrecognized commands
def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Sorry '%s' is not a valid command" % update.message.text)



# Token obtained from BotFather
TOKEN = "token of bot father"

# Create an Updater and pass in the bot's token
updater = Updater(TOKEN, use_context=True)

# Command Handlers
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', help))

updater.dispatcher.add_handler(CommandHandler('sendimage', send_image))  # New handler for sending an image
updater.dispatcher.add_handler(CommandHandler('menu', menu))  # New handler for displaying menu

# Message Handler for photos
updater.dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))

# Message Handlers
updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, unknown_text))
updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))

# Start polling
updater.start_polling()
updater.idle()
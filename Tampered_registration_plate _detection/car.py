#azure Custom vision api integration for getting prediction

import requests

# API endpoint and details
endpoint = "Custom vision iteration key"
prediction_key = "Custom vision prediction key"

# Set headers
headers = {
    "Prediction-Key": prediction_key,
    "Content-Type": "application/octet-stream",
}

data={
    "H9A2FKL":"Porsche 928"
}

# Replace with the path to the image file you want to analyze
image_path = r"/image5.jpg"

# Read the image file as bytes
image_data = open(image_path, "rb").read()

# Make the prediction request
response = requests.post(endpoint, headers=headers, data=image_data)

# Handle the response
car=""
if response.status_code == 200:
    results = response.json()

    # Extract the prediction with the highest probability
    highest_prediction = max(results['predictions'], key=lambda x: x['probability'])

    # Display the result with the highest probability
    print(f"The highest probability prediction is: {highest_prediction['tagName']} with probability {highest_prediction['probability']:.2%}")
    print(f"{highest_prediction['tagName']}")
else:
    print(f"Prediction failed with status code {response.status_code}")
    print(response.text)


#azure api integration
import requests

# API endpoint and details
endpoint = "https://cars7722-prediction.cognitiveservices.azure.com/customvision/v3.0/Prediction/eb8bd9ca-ab07-487f-839a-3d716927b4c8/classify/iterations/Iteration1/image"
prediction_key = "fd0e18db3f604ecea766c8f4d029f729"

# Set headers
headers = {
    "Prediction-Key": prediction_key,
    "Content-Type": "application/octet-stream",
}

data={
    "H9A2FKL":"Porsche 928"
}

# Replace with the path to the image file you want to analyze
image_path = r"C:\Users\velpo\OneDrive\Desktop\xl6\7xhrg3a_1573869.jpg"

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


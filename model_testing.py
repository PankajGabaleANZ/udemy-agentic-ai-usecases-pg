import requests
import os
import base64
# Set your API key
AZURE_API_KEY="AMEQEy0aIpAjTe0z6XMO6XuOd9jH5n6U"  # or set it directly as a string


# Endpoint URL
url = "https://Stable-Image-Core-wfpli.eastus2.models.ai.azure.com/images/generations"

# Headers
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {AZURE_API_KEY}"
}

# Payload
payload = {
    "model": "Stable-Image-Core",
    "prompt": "Ghibli style image of three elephants playing",
    "negative_prompt": "",
    "size": "1024x1024",
    "output_format": "png",
    "seed": 0
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload)

# Process the response
if response.status_code == 200:
    print("✅ Image generation request successful.")
    data = response.json()
    
    # Get the base64 image string
    base64_image = data.get('image', None)
    
    if base64_image:
        # Decode the base64 string
        image_data = base64.b64decode(base64_image)
        
        # Save it as a PNG file
        with open('generated_image.png', 'wb') as f:
            f.write(image_data)
        
        print("🎨 Image saved successfully as 'generated_image.png'")
    else:
        print("⚠️ No 'image' field found in response.")
else:
    print(f"❌ Request failed with status code {response.status_code}")
    print(response.text)
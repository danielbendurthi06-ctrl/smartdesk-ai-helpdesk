from pyngrok import ngrok
import time

public_url = ngrok.connect(5000)

print("Public URL:", public_url)

# Keep tunnel alive
while True:
    time.sleep(1)
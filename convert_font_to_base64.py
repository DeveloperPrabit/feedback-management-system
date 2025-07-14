import base64
import os

# Path to the font file
font_path = r"C:\Users\user 2\Desktop\rental_system\src\static\fonts\NotoSansDevanagari-Regular.ttf"

# Verify the font file exists
if not os.path.isfile(font_path):
    raise FileNotFoundError(f"Font file not found at: {font_path}")

# Convert font to Base64
with open(font_path, "rb") as font_file:
    encoded = base64.b64encode(font_file.read()).decode("utf-8")

# Save to a text file
with open("font_base64.txt", "w") as f:
    f.write(encoded)

print("Base64 string saved to font_base64.txt")
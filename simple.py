#for simple element

import cv2
import pytesseract
import numpy as np
import matplotlib.pyplot as plt
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# === Load and Resize the Image ===
image_path = "Images/O2.png"  # 🔁 Change this path
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
resized = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)

# === Canny Edge Detection and Hough Line Detection ===
edges = cv2.Canny(resized, 50, 150)
lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=200, minLineLength=100, maxLineGap=10)

x_axis_y = None
y_axis_x = None

# === Detect Horizontal (X-axis) and Vertical (Y-axis) Lines ===
if lines is not None:
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(y1 - y2) < 10:  # Horizontal line (X-axis)
            if x_axis_y is None or y1 > x_axis_y:
                x_axis_y = y1
        elif abs(x1 - x2) < 10:  # Vertical line (Y-axis)
            if y_axis_x is None or x1 < y_axis_x:
                y_axis_x = x1

# === Fallback Defaults if Axis Not Found ===
h, w = resized.shape
if x_axis_y is None:
    x_axis_y = int(h * 0.9)
if y_axis_x is None:
    y_axis_x = int(w * 0.1)

# === Crop ONLY Inside the Axes ===
cropped = resized[0:x_axis_y, y_axis_x:]

# === OCR on the Cropped Region ===
custom_config = r'--oem 3 --psm 6'
ocr_data = pytesseract.image_to_data(cropped, config=custom_config, output_type=pytesseract.Output.DICT)

# === Extract Only Numeric Values ===
inside_axis_numbers = []
for i in range(len(ocr_data['text'])):
    txt = ocr_data['text'][i].strip()
    if txt.isdigit():
        inside_axis_numbers.append(int(txt))

# === Display Cropped Plot Region ===
plt.figure(figsize=(8, 6))
plt.imshow(cropped, cmap='gray')
plt.title("Cropped First Quadrant (Inside Axis)")
plt.axis('off')
plt.show()

# === Final Output ===
print("✅ Final Detected Numbers Inside Axis Box:")
print(sorted(set(inside_axis_numbers)))
#co2, o2, n2
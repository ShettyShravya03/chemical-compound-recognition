#Tesseract code that gives 100% match for 18 samples.

import cv2
import pytesseract
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update this path if needed

# === Load Database ===
database_path = "SAMPLES.xlsx"  # Update this path with your actual database file
df = pd.read_excel(database_path)

# Ensure "Mass Array" column contains Python lists
df["Numbers"] = df["Mass Array"].apply(eval)


# === Smart Split Function ===
def smart_number_split(ocr_results):
    final_numbers = []

    for entry in ocr_results:
        digits = re.sub(r'\D', '', str(entry))
        if not digits:
            continue

        length = len(digits)

        if length <= 3:
            final_numbers.append(int(digits))
        elif length == 4:
            final_numbers.append(int(digits[:2]))
            final_numbers.append(int(digits[2:]))
        elif length == 5:
            final_numbers.append(int(digits[:3]))
            final_numbers.append(int(digits[3:]))
        elif length == 6:
            final_numbers.append(int(digits[:3]))
            final_numbers.append(int(digits[3:]))
        else:
            for i in range(0, length, 3):
                chunk = digits[i:i+3]
                if chunk:
                    final_numbers.append(int(chunk))
    return final_numbers


# === Number Extraction Function ===
def extract_digits_robust(image_path, min_number=5, max_split=500):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image at: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)

    # === Axis Detection ===
    edges = cv2.Canny(scaled, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=150, minLineLength=80, maxLineGap=10)
    h, w = scaled.shape
    x_axis_y = None
    y_axis_x = int(w * 0.10)

    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            if abs(y1 - y2) < 10 and y1 > 0.8 * h:
                x_axis_y = y1
                break
        for x1, y1, x2, y2 in lines[:, 0]:
            if abs(x1 - x2) < 10 and x1 < w * 0.2:
                y_axis_x = min(y_axis_x, x1)

    if x_axis_y is None:
        x_axis_y = int(h * 0.92)

    # === Crop First Quadrant ===
    cropped = scaled[0:int(x_axis_y * 1.003), y_axis_x - 10:]
    color_cropped = cv2.cvtColor(cropped.copy(), cv2.COLOR_GRAY2BGR)

    # === Preprocess for OCR ===
    blur = cv2.GaussianBlur(cropped, (3, 3), 0)
    sharpen = cv2.addWeighted(cropped, 2.5, blur, -1.3, 0)
    _, bin_img = cv2.threshold(sharpen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bin_img = cv2.dilate(bin_img, np.ones((2, 2), np.uint8), iterations=1)

    # === OCR ===
    config = "--oem 1 --psm 12"
    data = pytesseract.image_to_data(bin_img, config=config, output_type=pytesseract.Output.DICT)

    raw_text_values = []
    for i, text in enumerate(data['text']):
        text = text.strip().replace('O', '0').replace('o', '0').replace('l', '1')
        if not re.search(r'\d', text):
            continue

        x, y, w_box, h_box = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        if x < 10 or y < 5:
            continue

        cv2.rectangle(color_cropped, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)
        cv2.putText(color_cropped, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

        raw_text_values.append(text)

    # === Smart Split + Filter ===
    all_numbers = smart_number_split(raw_text_values)
    final_values = sorted(set([v for v in all_numbers if min_number <= v < max_split]))

    return final_values, color_cropped


# === Species Detection Function ===
def find_species_from_numbers(detected_numbers):
    best_match = None
    best_match_percentage = 0

    for _, row in df.iterrows():
        db_numbers = set(row["Numbers"])
        common_elements = db_numbers.intersection(detected_numbers)
        match_percentage = len(common_elements) / len(db_numbers) * 100

        if match_percentage > best_match_percentage:
            best_match_percentage = match_percentage
            best_match = row["Species Name"]

    if best_match_percentage > 90:
        return f"{best_match} (Match: {best_match_percentage:.2f}%)"
    elif best_match_percentage > 0:
        return f"Partial Match: {best_match} (Match: {best_match_percentage:.2f}%)"
    else:
        return "Species not found (0% match)"


# === Main Processing ===
def process_and_match(image_path):
    try:
        detected_numbers, annotated_image = extract_digits_robust(image_path)
        species_name = find_species_from_numbers(detected_numbers)

        print(f"✅ Detected Numbers: {detected_numbers}")
        print(f"🔍 Species Name: {species_name}")

        # Display the annotated image
        plt.imshow(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
        plt.title("OCR Annotated Numbers in First Quadrant")
        plt.axis("off")
        plt.show()
    except Exception as e:
        print(f"❌ Error: {e}")


# === Example Usage ===
image_path = "Images/22.png"  # Replace with the actual image path
process_and_match(image_path)
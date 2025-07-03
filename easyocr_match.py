#EasyOCR code that takes pdf as input, detects all th numbers within the graph and return the mass array.
#It also matches this mass array with a database and return the name of the samples.

import cv2
import easyocr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from pdf2image import convert_from_path
import os

# === Load Excel Database ===
database_path = "SAMPLES.xlsx"  # Path to your Excel file
df = pd.read_excel(database_path)
df["Numbers"] = df["Mass Array"].apply(eval)

# === Helper: Smart Number Cleaner ===
def smart_clean_numbers(texts):
    results = []
    for text in texts:
        clean = re.sub(r"[^\d]", "", text)
        if not clean:
            continue
        length = len(clean)
        if length == 4:
            results.extend([int(clean[:2]), int(clean[2:])])
        elif length == 5:
            results.extend([int(clean[:2]), int(clean[2:])])
        elif length == 6:
            results.extend([int(clean[:3]), int(clean[3:])])
        elif length > 6 and length % 3 == 0:
            results.extend([int(clean[i:i+3]) for i in range(0, length, 3)])
        elif length > 3:
            results.extend([int(clean[i:i+3]) for i in range(0, length, 3)])
        else:
            results.append(int(clean))
    return sorted(set(results))

# === OCR + Digit Extraction from Image ===
def extract_digits_easyocr(image_path, min_number=5, max_split=500):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image at: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_LINEAR)
    scaled = cv2.convertScaleAbs(scaled, alpha=1.4, beta=20)
    pad = np.ones((50, scaled.shape[1]), dtype=np.uint8) * 255
    scaled = np.vstack([scaled, pad])
    h, w = scaled.shape
    edges = cv2.Canny(scaled, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=150, minLineLength=80, maxLineGap=10)
    x_axis_y = int(h * 0.465)
    y_axis_x = int(w * 0.156)

    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            if abs(y1 - y2) < 10 and y1 > 0.8 * h:
                x_axis_y = y1
            if abs(x1 - x2) < 10 and x1 < w * 0.2:
                y_axis_x = min(y_axis_x, x1)

    cropped = scaled[0:min(h, x_axis_y - 10), max(0, y_axis_x - 50):]
    color_cropped = cv2.cvtColor(cropped.copy(), cv2.COLOR_GRAY2BGR)

    reader = easyocr.Reader(['en'], gpu=True)
    results = reader.readtext(cropped)

    detected_texts = []
    for bbox, text, conf in results:
        if re.search(r'\d', text):
            x_min = int(min([pt[0] for pt in bbox]))
            y_min = int(min([pt[1] for pt in bbox]))
            x_max = int(max([pt[0] for pt in bbox]))
            y_max = int(max([pt[1] for pt in bbox]))
            cv2.rectangle(color_cropped, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.putText(color_cropped, text, (x_min, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            detected_texts.append(text)

    all_numbers = smart_clean_numbers(detected_texts)
    final_values = [v for v in all_numbers if min_number <= v < max_split]
    return sorted(set(final_values)), color_cropped

# === Match to Species from Excel ===
def find_species_from_numbers(detected_numbers):
    best_match = None
    best_match_percentage = 0
    for _, row in df.iterrows():
        db_numbers = set(row["Numbers"])
        common = db_numbers.intersection(detected_numbers)
        match_percent = len(common) / len(db_numbers) * 100 if db_numbers else 0
        if match_percent > best_match_percentage:
            best_match_percentage = match_percent
            best_match = row["Species Name"]
    if best_match_percentage > 90:
        return f"{best_match} (Match: {best_match_percentage:.2f}%)"
    elif best_match_percentage > 0:
        return f"Partial Match: {best_match} (Match: {best_match_percentage:.2f}%)"
    else:
        return "Species not found (0% match)"

# === Main Function for One Image ===
def process_and_match(image_path):
    try:
        detected_numbers, annotated_img = extract_digits_easyocr(image_path)
        species_name = find_species_from_numbers(detected_numbers)
        print(f"✅ Detected Numbers: {detected_numbers}")
        print(f"🔍 Species Match: {species_name}")
        plt.imshow(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB))
        plt.title(f"Result: {os.path.basename(image_path)}")
        plt.axis("off")
        plt.show()
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")

# === Convert PDF to Image and Process Each Page ===
def pdf_to_image_and_process(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300)
    for i, page in enumerate(pages):
        image_path = f"page_{i+1}.png"
        page.save(image_path, "PNG")
        print(f"\n📄 Processing Page {i+1}: {image_path}")
        process_and_match(image_path)

# === Usage ===
pdf_path = "Samples-25/74023A.pdf"  # Replace with your PDF path
pdf_to_image_and_process(pdf_path)
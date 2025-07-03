#FINAL CODE 
#Here the input is a pdf which is a spectra of mixture of Oxygen and Nitrogen in different concentrations or simple elements(O2, N2, CO2).
#First, we extract the actual numbers for the graph.
#Next, we round off that to the nearest whole number.
#Then, we compare that mass array with the database to detect the presence of the element in that mixture.
#If, we are comparing it with the simple elements(O2, N2, CO2) then we use Book.xlsx database.
#If, we are comparing it with complex structure of 25 samples then we use SAMPLES.xlsx database.

import cv2
import easyocr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from pdf2image import convert_from_path
import os

# === Load Excel Database ===
database_path = "Book.xlsx"
df = pd.read_excel(database_path)
df["Numbers"] = df["Mass Array"].apply(eval)

# === Smart OCR Post-Processing for Decimal Numbers ===
def smart_clean_numbers(texts):
    results = []
    for text in texts:
        matches = re.findall(r"\d+\.\d+|\d+", text)  # Accept both floats and ints
        for m in matches:
            try:
                results.append(round(float(m), 4))  # Store as float with 4 decimals
            except:
                continue
    return sorted(set(results))

# === OCR Number Extraction ===
def extract_digits_easyocr(image_path, min_number=1.0, max_split=500.0):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image at: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Improve contrast and resize
    scaled = cv2.resize(gray, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_LINEAR)
    scaled = cv2.convertScaleAbs(scaled, alpha=1.2, beta=0)
    pad = np.ones((50, scaled.shape[1]), dtype=np.uint8) * 255
    scaled = np.vstack([scaled, pad])

    h, w = scaled.shape
    edges = cv2.Canny(scaled, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=150, minLineLength=80, maxLineGap=10)

    # Axis detection
    x_axis_y = int(h * 0.46)
    y_axis_x = int(w * 0.25)

    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            if abs(y1 - y2) < 10 and y1 > 0.8 * h:
                x_axis_y = y1
            if abs(x1 - x2) < 10 and x1 < w * 0.2:
                y_axis_x = min(y_axis_x, x1)

    # Crop region: cut top and left edges
    top_cut = int(0.0455 * h)
    left_margin = max(0, y_axis_x - 90)
    right_margin = int(w * 0.995)
    cropped = scaled[top_cut:min(h, x_axis_y + 90), left_margin:right_margin]
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

            # 🔍 Skip if too close to left margin
            if x_min < int(cropped.shape[1] * 0.03):
                continue

            cv2.rectangle(color_cropped, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.putText(color_cropped, text, (x_min, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            detected_texts.append(text)

    all_numbers = smart_clean_numbers(detected_texts)
    final_values = [v for v in all_numbers if min_number <= v < max_split]
    return sorted(set(final_values)), color_cropped

# === Compare with All Species ===
def find_all_species_matches(detected_numbers):
    results = []
    for _, row in df.iterrows():
        species = row["Species Name"]
        db_numbers = set([round(float(x), 2) for x in row["Numbers"]])
        common = db_numbers.intersection(detected_numbers)
        match_percent = len(common) / len(db_numbers) * 100 if db_numbers else 0
        results.append((species, round(match_percent, 2), list(common)))
    return sorted(results, key=lambda x: x[1], reverse=True)

# === Process and Match ===
def process_and_match(image_path):
    try:
        raw_numbers, annotated_img = extract_digits_easyocr(image_path)
        print(f"\n📌 Raw Decimal Numbers (Before Rounding):\n{raw_numbers}")

        # Custom Rounding
        rounded_numbers = sorted(set([
            int(n) + 1 if (n - int(n)) >= 0.6 else int(n)
            for n in raw_numbers
        ]))
        print(f"🔢 Rounded Integer Numbers (After Custom Rounding):\n{rounded_numbers}")

        all_matches = find_all_species_matches(set(rounded_numbers))

        print("\n🔍 Species Match Results:")
        for species, percent, common in all_matches:
            print(f"- {species}: {percent:.2f}% (Matched: {common})")

        plt.imshow(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB))
        plt.title(f"Result: {os.path.basename(image_path)}")
        plt.axis("off")
        plt.show()
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")

# === Convert PDF to Image and Process FIRST Page ===
def pdf_to_image_and_process(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300)
    if not pages:
        print("❌ No pages found in PDF.")
        return

    image_path = "page_1.png"
    pages[0].save(image_path, "PNG")
    print(f"\n📄 Processing First Page: {image_path}")
    process_and_match(image_path)

# === Run ===
pdf_path = "Spectra 4.pdf"  # Replace with your own path
pdf_to_image_and_process(pdf_path)
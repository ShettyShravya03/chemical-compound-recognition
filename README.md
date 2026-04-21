<!-- BANNER — upload banner.svg to this repo root -->
<p align="center">
  <img src="./banner.svg" width="100%" alt="Mass Spectrometry OCR Pipeline — Chemical Compound Recognition">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/IISc-CGPL%20Lab-0d4f8b?style=for-the-badge&logo=academia&logoColor=white">&nbsp;
  <img src="https://img.shields.io/badge/Extraction%20Accuracy-85%25-16a34a?style=for-the-badge">&nbsp;
  <img src="https://img.shields.io/badge/Spectra%20Types-2-15803d?style=for-the-badge">&nbsp;
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white"></a>&nbsp;
  <img src="https://img.shields.io/badge/OpenCV-EasyOCR-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white">&nbsp;
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge">
</p>

---

## 📋 Table of Contents
- [Overview](#-overview)
- [Key Results](#-key-results)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#️-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Pipeline Details](#-pipeline-details)
- [File Structure](#-file-structure)
- [Dataset & Databases](#-dataset--databases)
- [Contributors](#-contributors)
- [License](#-license)

---

## 🎯 Overview

An OCR-based pipeline built for **IISc's CGPL (Combustion, Gasification & Propulsion Laboratory)** to automate combustion gas composition analysis from mass spectrometry outputs. The system processes PDF or image inputs containing mass spectra, extracts m/z peak labels using computer vision, and identifies the closest matching chemical compound from curated gas databases — returning confidence scores per identified species.

The pipeline handles **two fundamentally different spectra types**:
- **Clean integer references** — standard reference spectra with integer m/z values
- **Noisy instrument decimals** — raw instrument output with values like `27.9012` requiring normalization

This distinction drove the core engineering challenge: designing a rounding and matching strategy robust enough to bridge both formats reliably, **reducing manual peak identification effort** for active gasification experiments.

---

## 📊 Key Results

| Metric | Value |
|--------|-------|
| m/z peak extraction accuracy | **85%** |
| Spectra types handled | **2** (integer reference + noisy instrument) |
| Databases matched against | **2** (pure elements + 25 combustion samples) |
| Output format | Percentage confidence scores per identified gas |

- **Input formats:** PDF spectra files and PNG/image inputs
- **Database coverage:** Pure elemental gases + 25 combustion compound samples

---

## 🧠 Architecture

```
Mass Spectrometry Output (PDF / Image)
          │
          ▼
  ┌───────────────────┐
  │  PDF → Image      │  Convert spectra pages to rasterised images
  │  Preprocessing    │  for downstream vision processing
  └───────────────────┘
          │
          ▼
  ┌───────────────────┐
  │  Hough-Transform  │  Detects X and Y axes from spectrum graph
  │  Axis Detection   │  via OpenCV — adaptive graph cropping
  │  (OpenCV)         │  isolates the m/z peak region
  └───────────────────┘
          │
          ▼
  ┌───────────────────┐
  │  EasyOCR          │  Reads m/z peak labels from the cropped
  │  Peak Extraction  │  spectrogram region
  └───────────────────┘
          │
          ▼
  ┌───────────────────┐
  │  Decimal          │  Custom rounding logic (≥ 0.6 rounds up)
  │  Normalisation    │  normalises instrument noise — bridges
  │                   │  integer references and raw decimals
  └───────────────────┘
          │
     ┌────┴────────────────┐
     ▼                     ▼
  Pure Elements DB    Combustion Samples DB
  (reference gases)   (25 compounds)
     │                     │
     └────────┬────────────┘
              ▼
  ┌───────────────────┐
  │  Confidence Score │  Percentage match score returned
  │  Output           │  per identified gas species
  └───────────────────┘
```

---

## ✨ Features

- **Dual spectra handling** — processes both clean integer references and noisy instrument decimal spectra without configuration changes
- **Hough-transform axis detection** — automatically detects graph axes for adaptive cropping, requiring no manual region annotation
- **EasyOCR peak extraction** — reads m/z values directly from spectrum images, tolerating real-world print quality variation
- **Custom decimal normalisation** — ≥ 0.6 rounds up logic bridges instrument noise to integer references
- **Two-database matching** — matches against pure elements and a curated 25-compound combustion sample library
- **Confidence scores** — returns percentage confidence per identified gas species for downstream analysis
- **PDF and image input support** — accepts raw instrument PDF exports and pre-rasterised images

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| OCR | EasyOCR |
| Computer Vision | OpenCV · Hough Transform |
| Image Processing | PIL / Pillow · NumPy |
| Data Handling | Pandas · openpyxl |
| Input Formats | PDF (via pdf2image / PyMuPDF) · PNG |
| Language | Python |

---

## 🔧 Installation

```bash
git clone https://github.com/ShettyShravya03/chemical-compound-recognition.git
cd chemical-compound-recognition

pip install -r requirements.txt
```

**Key dependencies:** `easyocr` `opencv-python` `numpy` `pandas` `Pillow` `pdf2image` `openpyxl`

> **Note:** EasyOCR downloads model weights on first run (~200 MB). Ensure an internet connection on initial setup.

---

## 🚀 Usage

### Run on a PDF spectrum file

```bash
python easyocr_match.py --input Spectra\ 1.pdf
```

### Run on an image input

```bash
python simple.py --input page_1.png
```

### Compare across all samples

```bash
python final_comparison.py
```

**Sample output:**
```
Extracted m/z values: [28, 32, 44, 14, 16]
Best match: Carbon Dioxide (CO₂)
Confidence: 87.3%

Runner-up: Nitrogen (N₂)
Confidence: 61.4%
```

### Match against a specific database

```python
from easyocr_match import match_spectrum

result = match_spectrum(
    input_path="Spectra 3.pdf",
    database="combustion"   # or "elements"
)

print(result["compound"])     # e.g. "Carbon Monoxide"
print(result["confidence"])   # e.g. 0.83
print(result["matched_peaks"])
```

---

## 🔍 Pipeline Details

### Stage 1 — PDF / Image Ingestion

Input spectra arrive as PDF exports from mass spectrometry instruments or as pre-rasterised images. PDFs are converted page-by-page to high-resolution images for downstream processing.

### Stage 2 — Axis Detection (Hough Transform)

OpenCV's Hough Line Transform detects the X (m/z) and Y (intensity) axes of the spectrum graph. Adaptive graph cropping then isolates only the peak label region, reducing OCR noise from surrounding annotations, titles, and legends.

### Stage 3 — OCR Peak Extraction (EasyOCR)

EasyOCR reads the m/z peak values from the cropped region. This stage handles two spectra types:
- **Integer references:** Standard clean outputs — `28`, `32`, `44`
- **Instrument decimals:** Raw noisy readings — `27.9012`, `31.9867`, `43.9901`

### Stage 4 — Decimal Normalisation

A custom rounding rule (decimal part ≥ 0.6 → round up, otherwise round down) normalises instrument noise to integer m/z values, enabling matching against integer-indexed reference databases without manual correction.

### Stage 5 — Database Matching

Normalised m/z sets are matched against:

| Database | Contents |
|----------|----------|
| Pure elements | Reference spectra for elemental gases |
| Combustion samples (`SAMPLES.xlsx`) | 25 combustion compound spectra |

Match confidence is computed as the percentage of extracted peaks present in the candidate compound's reference spectrum — the highest-scoring compound is returned as the primary identification.

### Scripts Reference

| Script | Purpose |
|--------|---------|
| `easyocr_match.py` | Main OCR extraction + database matching |
| `simple.py` | Lightweight single-image extraction |
| `match_simple.py` | Simplified matching against element DB |
| `final_comparison.py` | Batch comparison across all sample spectra |

---

## 📁 File Structure

```
.
├── Images/                # Reference spectrum images
├── Samples-25/            # 25 combustion compound sample spectra
├── Spectra 1.pdf          # Example instrument spectra (1–5)
├── Spectra 2.pdf
├── Spectra 3.pdf
├── Spectra 4.pdf
├── Spectra 5.pdf
├── Carbondioxide.pdf      # Reference spectra for pure elements
├── Nitrogen.pdf
├── Oxygen.pdf
├── SAMPLES.xlsx           # Combustion samples database
├── ONSpectra.xlsx         # O₂ / N₂ reference spectra
├── Book.xlsx              # Supplementary data
├── page_1.png             # Example rasterised spectrum page
├── easyocr_match.py       # Main OCR + matching pipeline
├── final_comparison.py    # Batch comparison script
├── match_simple.py        # Simplified matching utility
├── simple.py              # Lightweight image extraction
├── requirements.txt
└── README.md
```

---

## 📂 Dataset & Databases

### Instrument Spectra
Five real mass spectrometry outputs (`Spectra 1–5.pdf`) from IISc's CGPL gasification experiments, covering combustion gas mixtures including CO₂, CO, N₂, O₂, and hydrocarbons.

### Reference Databases
| Database | Format | Compounds |
|----------|--------|-----------|
| Pure elements | Individual PDFs (N₂, O₂, CO₂) + `ONSpectra.xlsx` | Elemental gases |
| Combustion samples | `SAMPLES.xlsx` | 25 combustion compounds |

> **Note:** The sample spectra in this repository are from real gasification experiments at IISc CGPL. Full datasets remain under the lab's data governance policy.

---

## 👥 Contributors

Built during a Software Engineering Internship at **IISc's CGPL Lab, Bengaluru** (Jun–Jul 2025).

| Contributor | GitHub |
|-------------|--------|
| Shravya S Shetty | [@ShettyShravya03](https://github.com/ShettyShravya03) |
| Sridevi | [@Sridevi25git](https://github.com/Sridevi25git) |
| Khushi R Shetty | [@KhushiRShetty](https://github.com/KhushiRShetty) |

---

## 📜 License

MIT © 2025 Shravya S Shetty, Sridevi, Khushi R Shetty

<p align="center">
  <sub>Built at <a href="https://cgpl.iisc.ac.in/">IISc CGPL Lab</a>, Bengaluru · Software Engineering Internship 2025</sub>
</p>

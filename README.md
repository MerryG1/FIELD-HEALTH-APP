# Field Health App

A web application for analysing agricultural field health from drone-derived raster data. Upload multispectral imagery and canopy height model (CHM) data to produce a classified NDVI health map that identifies vegetation stress across the field.

---

## How It Works

1. Upload a **multispectral (RGB/NIR) raster** — required for all analyses.
2. Provide canopy height data via one of two options:
   - **Option A**: Upload a pre-computed **CHM** raster.
   - **Option B**: Upload a **DSM** (Digital Surface Model — includes vegetation & buildings) and a **DTM** (Digital Terrain Model — bare ground only); the app derives the CHM automatically (`CHM = DSM − DTM`).
3. Click **Analyze Field**.

The app produces three output GeoTIFFs per job:

| Output file | Description |
|---|---|
| `{job_id}_ndvi.tif` | NDVI derived from the red and NIR bands |
| `{job_id}_calculated_chm.tif` | CHM calculated from DSM and DTM (Option B only) |
| `{job_id}_ndvi_health_map.tif` | 4-class NDVI health map with embedded colormap (see below) |

---

## NDVI Health Classification

The health map classifies every vegetation pixel (CHM > 0) relative to a healthy-field reference NDVI of **0.75**.

| Pixel value | Condition | NDVI range | Colour |
|---|---|---|---|
| 0 | No data / bare ground | — | Transparent |
| 1 | Healthy | ≥ 0.70 | Green |
| 2 | Mild stress | 0.60 – 0.70 | Light Green |
| 3 | Stressed | 0.45 – 0.60 | Orange |
| 4 | Severe stress / poor canopy | < 0.45 | Red |

A **2 cm buffer** is applied around all stressed and severe stress zones (classes 3 & 4). Pixels at the boundary of these zones that fall within the buffer are reclassified as mild stress (class 2) to capture transitional areas.

The colormap is embedded directly in the GeoTIFF, so QGIS, ArcGIS, and GDAL will automatically render the correct colours without manual styling.

---

## Project Structure

```
field-health-app/
├── docker/
│   └── app.Dockerfile          # Container build definition
├── src/field_health/
│   ├── app.py                  # Flask application & routes
│   ├── config.py               # Directory paths
│   └── raster_processing.py    # NDVI, CHM, classification & buffer logic
├── static/
│   └── script.js               # Frontend form & fetch logic
├── templates/
│   └── index.html              # Upload UI
├── data/
│   ├── uploads/                # Uploaded rasters (per type)
│   └── outputs/                # Generated output rasters
├── docker-compose.yml
└── environment.yml
```

---

## Requirements

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

No local Python installation is required — all dependencies are managed inside the container via [micromamba](https://mamba.readthedocs.io/).

**Python dependencies** (defined in `environment.yml`):

- Python 3.11
- Flask
- NumPy
- Rasterio
- SciPy

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd field-health-app
```

### 2. Build and run with Docker Compose

```bash
docker compose up --build
```

The app will be available at **http://localhost:5000**.

### 3. Use the app

Open `http://localhost:5000` in your browser, upload your raster files, and click **Analyze Field**. Results are returned as JSON and saved to `data/outputs/`.

> **Upload size limit:** 700 MB per request.

---

## API Reference

### `POST /analyze`

Accepts a `multipart/form-data` request.

| Field | Required | Description |
|---|---|---|
| `multispectral` | Yes | RGB/NIR multispectral GeoTIFF |
| `chm` | Option A | Pre-computed CHM GeoTIFF |
| `dsm` | Option B | Digital Surface Model GeoTIFF |
| `dtm` | Option B | Digital Terrain Model GeoTIFF |

**Success response (200)**

```json
{
  "message": "Analysis completed",
  "chm_source": "uploaded CHM | calculated from DSM and DTM",
  "ndvi_output": "/app/data/outputs/<job_id>_ndvi.tif",
  "chm_used": "/app/data/outputs/<job_id>_calculated_chm.tif",
  "ndvi_health_map": "/app/data/outputs/<job_id>_ndvi_health_map.tif"
}
```

**Error responses**

- `400` — Missing multispectral file, or neither CHM nor DSM+DTM provided.
- `413` — Upload exceeds the 700 MB limit.

---

## Data Directory

The `data/` directory is bind-mounted into the container, so all uploaded and output files persist on the host machine after the container stops.

```
data/
├── uploads/
│   ├── multispectral/
│   ├── chm/
│   ├── dsm/
│   └── dtm/
└── outputs/
```

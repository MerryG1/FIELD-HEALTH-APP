# Field Health App

A web application for analysing agricultural field health from drone-derived raster data. Upload multispectral imagery and canopy height model (CHM) data to identify problem zones with low vegetation health and abnormal canopy heights.

---

## How It Works

1. Upload a **multispectral (RGB/NIR) raster** — required for all analyses.
2. Provide canopy height data via one of two options:
   - **Option A**: Upload a pre-computed **CHM** raster.
   - **Option B**: Upload both a **DSM** and **DTM** raster; the app derives the CHM automatically (`CHM = DSM − DTM`).
3. Click **Analyze Field**.

The app produces three output GeoTIFFs per job:

| Output file | Description |
|---|---|
| `{job_id}_ndvi.tif` | NDVI derived from the red and NIR bands |
| `{job_id}_calculated_chm.tif` | CHM calculated from DSM and DTM (Option B only) |
| `{job_id}_low_ndvi_tall_zones.tif` | Binary mask: pixels where CHM > 3 m **and** NDVI < 0.4 |

---

## Project Structure

```
field-health-app/
├── docker/
│   └── app.Dockerfile          # Container build definition
├── src/field_health/
│   ├── app.py                  # Flask application & routes
│   ├── config.py               # Directory paths
│   └── raster_processing.py    # NDVI, CHM, problem-zone logic
├── static/
│   └── script.js               # Frontend form & fetch logic
├── templates/
│   └── index.html              # Upload UI
├── data/
│   ├── uploads/                # Uploaded rasters (per type)
│   └── outputs/                # Generated output rasters
├── docker-compose.yml
├── environment.yml
└── requirements.txt
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
  "problem_zone_output": "/app/data/outputs/<job_id>_low_ndvi_tall_zones.tif"
}
```

**Error responses**

- `400` — Missing multispectral file, or neither CHM nor DSM+DTM provided.

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

from flask import Flask, render_template, request, jsonify
from pathlib import Path
import uuid

from src.field_health.config import (
    MULTISPECTRAL_DIR,
    CHM_DIR,
    DSM_DIR,
    DTM_DIR,
    OUTPUT_DIR,
)

from src.field_health.raster_processing import (
    calculate_ndvi,
    calculate_chm_from_dsm_dtm,
    detect_problem_zones,
)

app = Flask(
    __name__,
    template_folder="/app/templates",
    static_folder="/app/static"
)

# Max upload size: 700 MB
app.config["MAX_CONTENT_LENGTH"] = 700 * 1024 * 1024


@app.errorhandler(413)
def request_too_large(e):
    return jsonify({
        "error": "Upload too large. Maximum allowed size is 500 MB per request."
    }), 413


@app.route("/")
def home():
    return render_template("index.html")


def save_uploaded_file(file, folder, job_id, label):
    if not file:
        return None

    suffix = Path(file.filename).suffix
    path = folder / f"{job_id}_{label}{suffix}"
    file.save(path)
    return path


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        return _run_analyze()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _run_analyze():
    job_id = str(uuid.uuid4())

    multispectral_file = request.files.get("multispectral")
    chm_file = request.files.get("chm")
    dsm_file = request.files.get("dsm")
    dtm_file = request.files.get("dtm")

    if not multispectral_file:
        return jsonify({"error": "Please upload the RGB/NIR multispectral raster."}), 400

    multispectral_path = save_uploaded_file(
        multispectral_file,
        MULTISPECTRAL_DIR,
        job_id,
        "multispectral"
    )

    chm_path = save_uploaded_file(chm_file, CHM_DIR, job_id, "chm")
    dsm_path = save_uploaded_file(dsm_file, DSM_DIR, job_id, "dsm")
    dtm_path = save_uploaded_file(dtm_file, DTM_DIR, job_id, "dtm")

    ndvi_output = OUTPUT_DIR / f"{job_id}_ndvi.tif"
    final_chm_output = OUTPUT_DIR / f"{job_id}_calculated_chm.tif"
    problem_zone_output = OUTPUT_DIR / f"{job_id}_ndvi_health_map.tif"

    calculate_ndvi(multispectral_path, ndvi_output)

    if chm_path:
        used_chm_path = chm_path
        chm_source = "uploaded CHM"
    elif dsm_path and dtm_path:
        used_chm_path = calculate_chm_from_dsm_dtm(
            dsm_path,
            dtm_path,
            final_chm_output
        )
        chm_source = "calculated from DSM and DTM"
    else:
        return jsonify({
            "error": "Upload either an existing CHM raster OR both DSM and DTM rasters."
        }), 400

    detect_problem_zones(
        ndvi_path=ndvi_output,
        chm_path=used_chm_path,
        output_path=problem_zone_output
    )

    return jsonify({
        "message": "Analysis completed",
        "chm_source": chm_source,
        "ndvi_output": str(ndvi_output),
        "chm_used": str(used_chm_path),
        "ndvi_health_map": str(problem_zone_output)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
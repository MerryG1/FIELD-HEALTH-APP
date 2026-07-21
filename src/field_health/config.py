from pathlib import Path

BASE_DIR = Path("/app")

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"

MULTISPECTRAL_DIR = UPLOAD_DIR / "multispectral"
CHM_DIR = UPLOAD_DIR / "chm"
DSM_DIR = UPLOAD_DIR / "dsm"
DTM_DIR = UPLOAD_DIR / "dtm"

for folder in [
    MULTISPECTRAL_DIR,
    CHM_DIR,
    DSM_DIR,
    DTM_DIR,
    OUTPUT_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from scipy.ndimage import binary_dilation


def calculate_ndvi(multispectral_path, output_path, red_band=2, nir_band=4):
    with rasterio.open(multispectral_path) as src:
        red = src.read(red_band).astype("float32")
        nir = src.read(nir_band).astype("float32")

        denominator = nir + red
        ndvi = np.where(
            denominator == 0,
            np.nan,
            (nir - red) / denominator
        )

        profile = src.profile.copy()
        profile.update(count=1, dtype="float32", nodata=np.nan)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(ndvi, 1)

    return output_path


def calculate_chm_from_dsm_dtm(dsm_path, dtm_path, output_path):
    with rasterio.open(dsm_path) as dsm_src, rasterio.open(dtm_path) as dtm_src:
        dsm = dsm_src.read(1).astype("float32")
        dtm = dtm_src.read(1).astype("float32")

        chm = dsm - dtm

        profile = dsm_src.profile.copy()
        profile.update(count=1, dtype="float32", nodata=np.nan)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(chm, 1)

    return output_path


# NDVI health classification thresholds
# 1 = Healthy (>= 0.70)  — Green
# 2 = Mild stress (0.60–0.70) — Light Green
# 3 = Stressed (0.45–0.60)   — Orange
# 4 = Severe stress (< 0.45) — Red
# 0 = No data / non-vegetation
_COLORMAP = {
    0: (0, 0, 0, 0),          # nodata — transparent
    1: (0, 128, 0, 255),      # Healthy — Green
    2: (144, 238, 144, 255),  # Mild stress — Light Green
    3: (255, 165, 0, 255),    # Stressed — Orange
    4: (255, 0, 0, 255),      # Severe stress — Red
}


def detect_problem_zones(ndvi_path, chm_path, output_path):
    with rasterio.open(ndvi_path) as ndvi_src, rasterio.open(chm_path) as chm_src:
        ndvi = ndvi_src.read(1).astype("float32")

        # Resample CHM to match NDVI grid if dimensions differ
        if (chm_src.height, chm_src.width) != (ndvi_src.height, ndvi_src.width):
            chm = np.empty((ndvi_src.height, ndvi_src.width), dtype="float32")
            reproject(
                source=rasterio.band(chm_src, 1),
                destination=chm,
                src_transform=chm_src.transform,
                src_crs=chm_src.crs,
                dst_transform=ndvi_src.transform,
                dst_crs=ndvi_src.crs,
                resampling=Resampling.bilinear,
            )
        else:
            chm = chm_src.read(1).astype("float32")

        # Classify NDVI into 4 health categories
        classified = np.zeros(ndvi.shape, dtype="uint8")  # 0 = nodata
        vegetation = (chm > 0) & ~np.isnan(ndvi)          # exclude bare ground & nodata
        classified[vegetation & (ndvi >= 0.70)] = 1
        classified[vegetation & (ndvi >= 0.60) & (ndvi < 0.70)] = 2
        classified[vegetation & (ndvi >= 0.45) & (ndvi < 0.60)] = 3
        classified[vegetation & (ndvi < 0.45)] = 4

        # Apply 2cm buffer around stressed + severe stress zones (classes 3 & 4)
        pixel_width = abs(ndvi_src.transform.a)
        radius_px = 0.02 / pixel_width  # 2 cm in pixels
        if radius_px >= 0.5:
            r = int(np.ceil(radius_px))
            y, x = np.ogrid[-r:r + 1, -r:r + 1]
            disk = (x ** 2 + y ** 2) <= radius_px ** 2
            problem_mask = classified >= 3
            dilated = binary_dilation(problem_mask, structure=disk)
            # Border pixels that were dilated into healthy/mild areas → mild stress
            border = dilated & ~problem_mask & (classified != 0)
            classified[border] = 2

        profile = ndvi_src.profile.copy()
        profile.update(count=1, dtype="uint8", nodata=0)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(classified, 1)
            dst.write_colormap(1, _COLORMAP)

    return output_path
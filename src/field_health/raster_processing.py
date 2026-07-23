import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


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

        mask = np.where(
            (chm > 3.0) & (ndvi < 0.4),
            1,
            0
        ).astype("uint8")

        profile = ndvi_src.profile.copy()
        profile.update(count=1, dtype="uint8", nodata=0)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(mask, 1)

    return output_path
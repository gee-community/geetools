"""Tasseled Cap transformation coefficients for various Earth Engine datasets."""

# Sentinel-2 MSI Level 1C coefficients
SENTINEL2_1C = {
    "bands": (
        "B1",
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
        "B8",
        "B8A",
        "B9",
        "B10",
        "B11",
        "B12",
    ),
    "TCB": (
        0.2381,
        0.2569,
        0.2934,
        0.3020,
        0.3099,
        0.3740,
        0.4180,
        0.3580,
        0.3834,
        0.0103,
        0.0020,
        0.0896,
        0.0780,
    ),
    "TCG": (
        -0.2266,
        -0.2818,
        -0.3020,
        -0.4283,
        -0.2959,
        0.1602,
        0.3127,
        0.3138,
        0.4261,
        0.1454,
        -0.0017,
        -0.1341,
        -0.2538,
    ),
    "TCW": (
        0.1825,
        0.1763,
        0.1615,
        0.0486,
        0.0170,
        0.0223,
        0.0219,
        -0.0755,
        -0.0910,
        -0.1369,
        0.0003,
        -0.7701,
        -0.5293,
    ),
}

# Landsat 8 OLI Surface Reflectance (Collection 2)
LANDSAT8_SR = {
    "bands": ("SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"),
    "TCB": (0.2043, 0.4158, 0.5524, 0.5741, 0.3124, 0.2303),
    "TCG": (-0.1603, -0.2819, -0.4934, 0.7940, -0.0002, -0.1446),
    "TCW": (0.0315, 0.2021, 0.3102, 0.1594, -0.6806, -0.6109),
}

# Landsat 8 OLI TOA Reflectance
LANDSAT8_TOA = {
    "bands": ("B2", "B3", "B4", "B5", "B6", "B7"),
    "TCB": (0.3561, 0.3972, 0.3904, 0.6966, 0.2286, 0.1596),
    "TCG": (-0.3344, -0.3544, -0.4556, 0.6966, -0.0242, -0.2630),
    "TCW": (0.2626, 0.2141, 0.0926, 0.0656, -0.7629, -0.5388),
}

# Landsat 8 OLI are usable for Landsat 9 OLI-2 per Zhai et al. 2022
LANDSAT9_SR = LANDSAT8_SR
LANDSAT9_TOA = LANDSAT8_TOA

# Landsat 7 ETM+ TOA
LANDSAT7_TOA = {
    "bands": ("B1", "B2", "B3", "B4", "B5", "B7"),
    "TCB": (0.3561, 0.3972, 0.3904, 0.6966, 0.2286, 0.1596),
    "TCG": (-0.3344, -0.3544, -0.4556, 0.6966, -0.0242, -0.2630),
    "TCW": (0.2626, 0.2141, 0.0926, 0.0656, -0.7629, -0.5388),
}

# Landsat 5 TM Raw DN
LANDSAT5_DN = {
    "bands": ("B1", "B2", "B3", "B4", "B5", "B7"),
    "TCB": (0.2909, 0.2493, 0.4806, 0.5568, 0.4438, 0.1706),
    "TCG": (-0.2728, -0.2174, -0.5508, 0.7221, 0.0733, -0.1648),
    "TCW": (0.1446, 0.1761, 0.3322, 0.3396, -0.6210, -0.4186),
}

# Landsat 5 TM Surface Reflectance
LANDSAT5_SR = {
    "bands": ("SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"),
    "TCB": (0.1509, 0.1973, 0.3279, 0.3406, -0.7112, -0.4572),
    "TCG": (-0.1603, -0.2819, -0.4934, 0.7940, -0.0002, -0.1446),
    "TCW": (0.0315, 0.2021, 0.3102, 0.1594, -0.6806, -0.6109),
}

# Landsat 4 TM Raw DN
LANDSAT4_DN = {
    "bands": ("B1", "B2", "B3", "B4", "B5", "B7"),
    "TCB": (0.3037, 0.2793, 0.4743, 0.5585, 0.5082, 0.1863),
    "TCG": (-0.2848, -0.2435, -0.5435, 0.7243, 0.0840, -0.1800),
    "TCW": (0.1509, 0.1973, 0.3279, 0.3406, -0.7112, -0.4572),
}

# Landsat 4 TM Surface Reflectance
LANDSAT4_SR = {
    "bands": ("SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"),
    "TCB": (0.2043, 0.4158, 0.5524, 0.5741, 0.3124, 0.2303),
    "TCG": (-0.1603, -0.2819, -0.4934, 0.7940, -0.0002, -0.1446),
    "TCW": (0.0315, 0.2021, 0.3102, 0.1594, -0.6806, -0.6109),
}

# MODIS NBAR
MODIS_NBAR = {
    "bands": (
        "Nadir_Reflectance_Band1",
        "Nadir_Reflectance_Band2",
        "Nadir_Reflectance_Band3",
        "Nadir_Reflectance_Band4",
        "Nadir_Reflectance_Band5",
        "Nadir_Reflectance_Band6",
        "Nadir_Reflectance_Band7",
    ),
    "TCB": (0.4395, 0.5945, 0.2460, 0.3918, 0.3506, 0.2136, 0.2678),
    "TCG": (-0.4064, 0.5129, -0.2744, -0.2893, 0.4882, -0.0036, -0.4169),
    "TCW": (0.1147, 0.2489, 0.2408, 0.3132, -0.3122, -0.6416, -0.5087),
}

# Platform to coefficients mapping
PLATFORM_COEFFICIENTS: dict = {
    # Sentinel-2
    "COPERNICUS/S2": SENTINEL2_1C,
    "COPERNICUS/S2_HARMONIZED": SENTINEL2_1C,
    "COPERNICUS/S2_SR": SENTINEL2_1C,
    "COPERNICUS/S2_SR_HARMONIZED": SENTINEL2_1C,
    # Landsat 9
    "LANDSAT/LC09/C02/T1_L2": LANDSAT9_SR,
    "LANDSAT/LC09/C02/T2_L2": LANDSAT9_SR,
    "LANDSAT/LC09/C02/T1_TOA": LANDSAT9_TOA,
    "LANDSAT/LC09/C02/T1_RT_TOA": LANDSAT9_TOA,
    "LANDSAT/LC09/C02/T2_TOA": LANDSAT9_TOA,
    # Landsat 8
    "LANDSAT/LC08/C02/T1_L2": LANDSAT8_SR,
    "LANDSAT/LC08/C02/T2_L2": LANDSAT8_SR,
    "LANDSAT/LC08/C02/T1_TOA": LANDSAT8_TOA,
    "LANDSAT/LC08/C02/T1_RT_TOA": LANDSAT8_TOA,
    "LANDSAT/LC08/C02/T2_TOA": LANDSAT8_TOA,
    "LANDSAT/LC08/C01/T1_SR": LANDSAT8_SR,
    "LANDSAT/LC08/C01/T2_SR": LANDSAT8_SR,
    "LANDSAT/LC08/C01/T1_TOA": LANDSAT8_TOA,
    "LANDSAT/LC08/C01/T1_RT_TOA": LANDSAT8_TOA,
    "LANDSAT/LC08/C01/T2_TOA": LANDSAT8_TOA,
    # Landsat 7
    "LANDSAT/LE07/C02/T1_L2": LANDSAT7_TOA,
    "LANDSAT/LE07/C02/T2_L2": LANDSAT7_TOA,
    "LANDSAT/LE07/C02/T1_TOA": LANDSAT7_TOA,
    "LANDSAT/LE07/C02/T1_RT_TOA": LANDSAT7_TOA,
    "LANDSAT/LE07/C02/T2_TOA": LANDSAT7_TOA,
    "LANDSAT/LE07/C01/T1_SR": LANDSAT7_TOA,
    "LANDSAT/LE07/C01/T2_SR": LANDSAT7_TOA,
    "LANDSAT/LE07/C01/T1_TOA": LANDSAT7_TOA,
    "LANDSAT/LE07/C01/T1_RT_TOA": LANDSAT7_TOA,
    "LANDSAT/LE07/C01/T2_TOA": LANDSAT7_TOA,
    # Landsat 5
    "LANDSAT/LT05/C02/T1_L2": LANDSAT5_SR,
    "LANDSAT/LT05/C02/T2_L2": LANDSAT5_SR,
    "LANDSAT/LT05/C01/T1_SR": LANDSAT5_SR,
    "LANDSAT/LT05/C01/T2_SR": LANDSAT5_SR,
    "LANDSAT/LT05/C01/T1": LANDSAT5_DN,
    "LANDSAT/LT05/C01/T2": LANDSAT5_DN,
    # Landsat 4
    "LANDSAT/LT04/C02/T1_L2": LANDSAT4_SR,
    "LANDSAT/LT04/C02/T2_L2": LANDSAT4_SR,
    "LANDSAT/LT04/C01/T1_SR": LANDSAT4_SR,
    "LANDSAT/LT04/C01/T2_SR": LANDSAT4_SR,
    "LANDSAT/LT04/C01/T1": LANDSAT4_DN,
    "LANDSAT/LT04/C01/T2": LANDSAT4_DN,
    # MODIS
    "MODIS/006/MCD43A4": MODIS_NBAR,
    "MODIS/061/MCD43A4": MODIS_NBAR,
}

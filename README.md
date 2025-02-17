# LST Calculator 🌡️ - QGIS Plugin

A QGIS plugin for calculating Land Surface Temperature (LST) from Landsat 8 TIRS Band 10 data. Designed for remote sensing analysis with an intuitive workflow and thermal visualization.

![Plugin Icon](icon.png)

## Features ✨
- **TOA Radiance Calculation** using metadata constants
- **Brightness Temperature Conversion** to Celsius
- **Thermal Visualization** with custom color ramps
- **QGIS 3.0+ Compatibility**
- Simple GUI integration with toolbar icon

## Installation 🛠️
1. Download the [latest release](https://github.com/yourusername/LST_Calculator/releases) as ZIP
2. In QGIS:  
   **Plugins → Manage and Install Plugins → Install from ZIP**  
   ![Install from ZIP](https://qgis.org/en/_static/documentation/plugins_install_from_zip.png)

## Usage 🖱️
1. Click the thermal icon in the QGIS toolbar
2. Select Landsat 8 Band 10 TIFF file
3. View automatically styled LST layer


# Sample Workflow
```python
plugin = LSTCalculator(iface)
plugin.calculate_lst("/path/to/LC08_L1TP_123045_20220101_B10.TIF")
```
Scientific Workflow 🔬

TOA Radiance: 
Lλ = ML * B10 + AL

(ML/AL from MTL file)

Brightness Temperature: 
BT (°C) = (K2 / ln(K1/Lλ + 1)) - 273.15

(K1=774.89, K2=1321.08)


Visualization:

Thermal color ramp from 20°C (blue) to 70°C (red)

Plugin Structure 📁
```
LST_Calculator/
├── icon.png          # Plugin icon
├── metadata.txt      # Version/author info
├── __init__.py       # QGIS entry point
└── lst_plugin.py     # Core functionality
```

Troubleshooting 🚑:
Error	Solution
GDAL Error 4	Verify input file is valid GeoTIFF

Missing Layers	Use Landsat 8 Collection 2 data

Incorrect Values	Check MTL file constants


Future Enhancements 🚀
- Automated MTL file parsing

- Batch processing support

- NDVI-based emissivity correction

References 📚:

Landsat 8 Data Users Handbook

QGIS Plugin Development Guide

Maintainer: Azad Rasul (azad.rasul@soran.edu.iq)

Version: 0.2 | License: GPL-3.0

Contribute by reporting issues or suggesting enhancements!

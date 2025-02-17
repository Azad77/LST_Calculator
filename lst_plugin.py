import os
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon, QColor
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsRasterBandStats,
    QgsMessageLog, Qgis, QgsSingleBandPseudoColorRenderer,
    QgsColorRampShader, QgsRasterShader
)
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator

class LSTCalculator:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        self.action = QAction(QIcon(icon_path), "LST Calculator", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("LST Tools", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removePluginMenu("LST Tools", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        band_path, _ = QFileDialog.getOpenFileName(
            None, "Select Landsat Band 10 (TIFF)", "", "TIFF Files (*.tif)"
        )
        if band_path:
            self.calculate_lst(band_path)

    def calculate_lst(self, band10_path):
        try:
            # 1. Load and validate Band 10
            band10_layer = QgsRasterLayer(band10_path, "B10_RAW")
            if not band10_layer.isValid():
                raise Exception("Invalid Band 10 file. Check file format and path.")

            # 2. Get metadata values (example values - implement MTL parser)
            ml, al = 0.0003342, 0.1  # Landsat 8 B10 defaults

            # 3. Calculate TOA Radiance (force floating-point output)
            QgsMessageLog.logMessage("Calculating TOA...", "LST Plugin", level=Qgis.Info)
            toa_layer = self.calculate_toa(band10_layer, ml, al)
            
            # 4. Calculate Brightness Temperature (simplified formula)
            QgsMessageLog.logMessage("Calculating BT...", "LST Plugin", level=Qgis.Info)
            bt_layer = self.calculate_bt(toa_layer)
            
            # 5. Style and add results
            self.style_thermal_layer(bt_layer)
            QgsProject.instance().addMapLayer(bt_layer)
            self.iface.messageBar().pushSuccess("Success", "LST calculation completed!")

        except Exception as e:
            self.iface.messageBar().pushCritical("Error", str(e))
            QgsMessageLog.logMessage(f"Error: {str(e)}", "LST Plugin", level=Qgis.Critical)

    def calculate_toa(self, band_layer, ml, al):
        """Top of Atmosphere Radiance: ML * B10 + AL"""
        entry = self.create_raster_entry(band_layer, 'b10')
        formula = f'({ml} * 1.0 * "b10@1") + {al}'  # Force float calculation
        return self.raster_calculation(formula, [entry], "TOA_Radiance")

    def calculate_bt(self, toa_layer):
        """Brightness Temperature Calculation (simplified formula)"""
        k1 = 774.89
        k2 = 1321.08
        
        # Simplified formula with epsilon to avoid division by zero
        formula = f'({k2} / ln( ({k1} / ("toa@1" + 0.000001) + 1 )) ) - 273.15'
        formula = formula.replace('  ', ' ').strip()  # Remove extra spaces

        # Debug output
        QgsMessageLog.logMessage(f"BT Formula: {formula}", "LST Plugin", level=Qgis.Info)
        
        entry = self.create_raster_entry(toa_layer, 'toa')
        return self.raster_calculation(formula, [entry], "BrightnessTemp")

    def create_raster_entry(self, layer, prefix):
        entry = QgsRasterCalculatorEntry()
        entry.ref = f'{prefix}@1'
        entry.raster = layer
        entry.bandNumber = 1
        return entry

    def raster_calculation(self, formula, entries, output_name):
        """Robust raster calculation with validation"""
        output_dir = QgsProject.instance().homePath()
        output_path = os.path.join(output_dir, f"{output_name}.tif")
        
        # Cleanup existing file
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except PermissionError:
                raise Exception(f"File in use: {output_path}. Close other programs.")

        # Validate input layers
        for entry in entries:
            if not entry.raster.isValid():
                raise Exception(f"Invalid input layer: {entry.raster.source()}")
            stats = entry.raster.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
            QgsMessageLog.logMessage(
                f"Input {entry.ref} - Min: {stats.minimumValue}, Max: {stats.maximumValue}",
                "LST Plugin", level=Qgis.Info
            )

        # Initialize calculator
        calc = QgsRasterCalculator(
            formula,
            output_path,
            'GTiff',
            entries[0].raster.extent(),
            entries[0].raster.width(),
            entries[0].raster.height(),
            entries
        )

        # Execute calculation
        QgsMessageLog.logMessage(f"Executing formula: {formula}", "LST Plugin", level=Qgis.Info)
        result = calc.processCalculation()
        
        if result != 0:
            error_map = {
                1: "Missing input layers",
                2: "Invalid formula syntax",
                3: "Calculation error (e.g., division by zero)",
                4: "GDAL internal error"
            }
            raise Exception(f"GDAL Error {result}: {error_map.get(result, 'Unknown error')}")

        # Validate output
        result_layer = QgsRasterLayer(output_path, output_name)
        if not result_layer.isValid():
            raise Exception(f"Failed to create output layer: {output_path}")
        
        stats = result_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
        QgsMessageLog.logMessage(
            f"Output {output_name} - Min: {stats.minimumValue}, Max: {stats.maximumValue}",
            "LST Plugin", level=Qgis.Info
        )
        
        return result_layer
    def style_thermal_layer(self, layer):
        """Apply thermal color ramp to raster layer"""
        # 1. Create the color ramp shader
        color_ramp = QgsColorRampShader()
        color_ramp.setColorRampType(QgsColorRampShader.Interpolated)
    
        # Define color ramp items (temperature values in Celsius)
        items = [
            QgsColorRampShader.ColorRampItem(20, QColor(0, 0, 255), "20°C"),
            QgsColorRampShader.ColorRampItem(30, QColor(0, 255, 255), "30°C"),
            QgsColorRampShader.ColorRampItem(40, QColor(0, 255, 0), "40°C"),
            QgsColorRampShader.ColorRampItem(50, QColor(255, 255, 0), "50°C"),
            QgsColorRampShader.ColorRampItem(60, QColor(255, 165, 0), "60°C"),
            QgsColorRampShader.ColorRampItem(70, QColor(255, 0, 0), "70°C")
        ]
        color_ramp.setColorRampItemList(items)

        # 2. Create the raster shader and link the color ramp
        raster_shader = QgsRasterShader()
        raster_shader.setRasterShaderFunction(color_ramp)  # Corrected line

        # 3. Create the renderer and apply to layer
        renderer = QgsSingleBandPseudoColorRenderer(
            layer.dataProvider(),
            1,  # Band number
            raster_shader  # Use the raster_shader here
        )
        layer.setRenderer(renderer)
        layer.triggerRepaint()
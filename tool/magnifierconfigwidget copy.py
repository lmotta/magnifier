# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Magnifier config widget
Description          : Widget for configure magnifier
Date                 : December, 2025
copyright            : (C) 2025 by Luiz Motta
email                : motta.luiz@gmail.com
 ***************************************************************************/
"""

__author__ = 'Luiz Motta'
__date__ = '2025-12-01'
__copyright__ = '(C) 2025, Luiz Motta'
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import Qt, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QWidget,
    QSlider, QLabel, QComboBox,
    QHBoxLayout, QVBoxLayout,
    QSizePolicy
)

from qgis.gui import QgisInterface

from .magnifiermap import MagnifierMap
from .translate import tr


class MagnifierConfigWidget(QWidget):
    def __init__(self,
            iface:QgisInterface,
            magnifier_map:MagnifierMap,
            zoom_values:tuple,
            zoom_value:int,
            magnifier_values:tuple,
            magnifier_value:int
    ):
        def createSlider(title_format:str, values:tuple, value:int)->QSlider:
            slider = QSlider(Qt.Horizontal, self)
            slider.setMinimum(0)
            slider.setMaximum(len(values) - 1)
            slider.setValue(values.index(value))
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(1)

            lbls_x = [ f"{v}x" for v in values ]
            title = title_format.format( ','.join(lbls_x) )
            slider.setToolTip(title)

            return slider

        super().__init__( iface.mainWindow() )
        self.magnifier_map = magnifier_map
        self.zoom_values = zoom_values
        self.magnifier_values = magnifier_values

        main = QHBoxLayout(self)
        main.setContentsMargins(4, 0, 4, 0)
        main.setSpacing(8)

        self.lbl_layer = QLabel('', self)
        self.lbl_layer.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        main.addWidget(self.lbl_layer)
        
        slider_zoom = createSlider( tr('Zoom factor ({})'), zoom_values, zoom_value )
        slider_zoom.valueChanged.connect(self.on_ZoomValueChanged)
        main.addWidget(slider_zoom)
        slider_magnifier = createSlider( tr('Magnifier factor ({})'), magnifier_values, magnifier_value )
        slider_magnifier.valueChanged.connect(self.on_MagnifierValueChanged)
        main.addWidget(slider_magnifier)
        
        #main.addStretch()
        self.setLayout(main)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.setMaximumHeight(28)


    def setLayerName(self, name:str)->None:
        self.lbl_layer.setText(name)

    @pyqtSlot(int)
    def on_ZoomValueChanged(self, value:int)->None:
        self.magnifier_map.zoom_factor = value
        self.magnifier_map.setImage()
        self.magnifier_map.updateCanvas()

    @pyqtSlot(int)
    def on_MagnifierValueChanged(self, value:int)->None:
        self.magnifier_map.magnifier_factor = value
        self.magnifier_map.updateCanvas()

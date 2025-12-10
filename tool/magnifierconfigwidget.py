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
__date__ = '2015-12-10'
__copyright__ = '(C) 2025, Luiz Motta'
__revision__ = '$Format:%H$'


from qgis.PyQt.QtCore import Qt, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QComboBox, QLabel,
    QSizePolicy
)
from qgis.PyQt.QtGui import QColor, QPalette

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
        def createComboBox(title_format: str, values: tuple, current_val: int)->QComboBox:
            combo = QComboBox(self)
            
            for v in values:
                combo.addItem(f"{v}x", v)
            
            if current_val in values:
                index = values.index(current_val)
                combo.setCurrentIndex(index)
            
            lbls_x = [f"{v}x" for v in values]
            title = title_format.format(','.join(lbls_x))
            combo.setToolTip(title)
            
            return combo

        super().__init__( iface.mainWindow() )
        self.magnifier_map = magnifier_map
        self.zoom_values = zoom_values
        self.magnifier_values = magnifier_values

        main = QHBoxLayout(self)
        main.setContentsMargins(4, 0, 4, 0)
        main.setSpacing(8)

        self.lbl_layer = QLabel('', self)
        self.lbl_layer.setToolTip(tr('Active layer'))
        self.lbl_layer.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        main.addWidget(self.lbl_layer)
        
        combo_zoom = createComboBox( tr('Zoom factor ({})'), zoom_values, zoom_value )
        combo_zoom.currentIndexChanged.connect(self.on_ZoomValueChanged)
        main.addWidget(combo_zoom)
        combo_magnifier = createComboBox( tr('Magnifier factor ({})'), magnifier_values, magnifier_value )
        combo_magnifier.currentIndexChanged.connect(self.on_MagnifierValueChanged)
        main.addWidget(combo_magnifier)
        
        main.addStretch()
        self.setLayout(main)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.setMaximumHeight(28)

    @pyqtSlot(int)
    def on_ZoomValueChanged(self, index:int)->None:
        if 0 <= index < len(self.zoom_values):
            self.magnifier_map.zoom_factor = self.zoom_values[index]
            self.magnifier_map.setImage()
            self.magnifier_map.updateCanvas()

    @pyqtSlot(int)
    def on_MagnifierValueChanged(self, index:int)->None:
        if 0 <= index < len(self.magnifier_values):
            self.magnifier_map.magnifier_factor = self.magnifier_values[index]
            self.magnifier_map.updateCanvas()
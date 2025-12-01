# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Magnifier tool
Description          : Plugin for magnifier active layer
Date                 : November, 2025
copyright            : (C) 2025 by Luiz Motta
email                : motta.luiz@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Luiz Motta'
__date__ = '2025-11-27'
__copyright__ = '(C) 2025, Luiz Motta'
__revision__ = '$Format:%H$'

from typing import List

from qgis.PyQt.QtCore import (
    Qt,
    QPoint, QLine, QRect,
    QObject, pyqtSignal
)
from qgis.PyQt.QtGui import (
    QColor,
    QImage, QPainter, QPainterPath,
    QRegion
)

from qgis.core import (
    QgsMapLayer,
    QgsMapRendererParallelJob,
    QgsMapSettings,
    QgsPointXY, QgsRectangle
)
from qgis.gui import (
    QgsMapCanvas, QgsMapCanvasItem
)


class MagnifierSignals(QObject):
    creatingImage = pyqtSignal()
    finishedImage = pyqtSignal()

class MagnifierMap(QgsMapCanvasItem):
    def __init__(self, canvas:QgsMapCanvas):
        super().__init__( canvas )
        self.signals = MagnifierSignals()

        self.map_settings = None
        self.zoom_factor = 4
        self.magnifier_factor = 2
        self.setZValue(10)
        self.layers = []
        self.pixel_point = None
        self.canvas = canvas
        self.image = None
      
    def clear(self)->None:
        self.layers = []
        self.pixel_point = None
        self.image = None
        self.updateCanvas()

    def setLayers(self, layers:List[QgsMapLayer]):
        self.layers = layers

    def setPixelPoint(self, point:QgsPointXY)->None:
        if self.image is None: # Rendering image
            return

        self.pixel_point = point
        self.updateCanvas() # Call self.paint
      
    def paint(self, painter:QPainter, *args): # NEED *args for   WINDOWS!
        if not self.layers or self.pixel_point is None or self.image is None:
            return

        w, h = self.canvas.width(), self.canvas.height()
        x = int( self.pixel_point.x() )
        y = int( self.pixel_point.y() )

        if x < 0 or x > w or y < 0 or y > h:
            return
        
        min_size = min( w, h )
        d = int( min_size / 10 * self.magnifier_factor )
        r = d // 2
        rect_region = QRect(
            x - r,
            y - r,
            d, d
        )
        region = QRegion( rect_region, QRegion.Ellipse )
        painter.setClipRegion( region )
        
        offset_x = x * (1 - self.zoom_factor)
        offset_y = y * (1 - self.zoom_factor)        
        painter.drawImage( offset_x, offset_y, self.image )

        # --- Acabamento ---
        # Desenha a borda da lupa (opcional, para melhor visualização)
        painter.setClipping(False)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.black)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse( rect_region )

    # It is a slot, the decorator 'pyqtSlot' fail because QgsMapCanvasItem not is QObject
    def setMap(self):
        def createMapSettingsWithZoomFactor():
            settings = QgsMapSettings()
            settings.setBackgroundColor(QColor(Qt.transparent))
            settings.setLayers( self.layers )
            settings.setDestinationCrs( self.canvas.mapSettings().destinationCrs() )
            
            # Create Zoom
            settings.setOutputSize( self.canvas.size() * self.zoom_factor ) # More pixels
            settings.setExtent( self.canvas.extent() )

            return settings

        def finished():
            self.image = None
            image = job.renderedImage()
            if bool( self.canvas.property('retro') ):
                image = image.scaled( image.width() / 3, image.height() / 3 )
                image = image.convertToFormat( QImage.Format_Indexed8, Qt.OrderedDither | Qt.OrderedAlphaDither )
            self.image = image
            self.signals.finishedImage.emit()
            self.updateCanvas()

        if not self.layers:
            return

        self.signals.creatingImage.emit()

        self.map_settings = createMapSettingsWithZoomFactor()
        
        self.setRect( self.canvas.extent() )
        job = QgsMapRendererParallelJob( self.map_settings ) 
        job.start()
        job.finished.connect( finished ) 
        #job.waitForFinished()

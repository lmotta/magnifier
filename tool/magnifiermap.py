# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Magnifier Map
Description          : Magnifier Logic
Date                 : December, 2025
copyright            : (C) 2025 by Luiz Motta
email                : motta.luiz@gmail.com
 ***************************************************************************/
"""

__author__ = 'Luiz Motta'
__date__ = '2015-12-10'
__copyright__ = '(C) 2025, Luiz Motta'
__revision__ = '$Format:%H$'


from qgis.PyQt.QtCore import (
    Qt,
    QRect,
    QObject, pyqtSignal
)
from qgis.PyQt.QtGui import (
    QColor,
    QImage, QPainter,
    QRegion
)

from qgis.core import (
    QgsMapRendererParallelJob,
    QgsMapSettings,
    QgsPointXY
)
from qgis.gui import (
    QgsMapCanvas, QgsMapCanvasItem
)


class MagnifierSignals(QObject):
    creatingImage = pyqtSignal()
    finishedImage = pyqtSignal()

class MagnifierMap(QgsMapCanvasItem):
    def __init__(self, canvas:QgsMapCanvas, zoom_factor:int, magnifier_factor:int):
        self.canvas = canvas
        self.zoom_factor = zoom_factor
        self.magnifier_factor = magnifier_factor
        super().__init__( canvas )
        self.setZValue(10)

        self.signals = MagnifierSignals()
        self.layers = []
        self.pixel_point = None
        self.image = None
      
    def clear(self)->None:
        self.layers = []
        self.pixel_point = None
        self.image = None
        self.updateCanvas()

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

        painter.setClipping(False)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.black)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse( rect_region )

    # It is a slot, the decorator 'pyqtSlot' fail because QgsMapCanvasItem not is QObject
    def setImage(self):
        def createMapSettingsWithZoomFactor():
            settings = QgsMapSettings()
            settings.setBackgroundColor(QColor(Qt.transparent))
            settings.setDevicePixelRatio( 1 )
            settings.setLayers( self.layers )
            settings.setDestinationCrs( self.canvas.mapSettings().destinationCrs() )
            
            # Create Zoom
            settings.setOutputSize( self.canvas.size() * self.zoom_factor ) # More pixels
            settings.setExtent( self.canvas.extent() )

            return settings

        def finished():
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

        self.setRect( self.canvas.extent() )
        self.image = None
        job = QgsMapRendererParallelJob( createMapSettingsWithZoomFactor() ) 
        job.start()
        job.finished.connect( finished ) 
        #job.waitForFinished()

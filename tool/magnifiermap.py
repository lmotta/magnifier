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
    QPoint, QRect, QLine 
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
    QgsPointXY
)
from qgis.gui import (
    QgsMapCanvas, QgsMapCanvasItem
)

class MagnifierMap(QgsMapCanvasItem):
    def __init__(self, canvas:QgsMapCanvas):
        super().__init__( canvas )
        self.settings = None
        self.magnification_factor = 1
        self.magnifier_factor = 4
        self.setZValue(-9.0)
        self.layers = []
        self.map_point = None
        self.canvas = canvas
        self.image = None

        self.inCanvas = lambda x, y: x > 0 or x < self.boundingRect().width() or y > 0 or y < self.boundingRect().height()
      
    def clear(self)->None:
        del self.layers[:]
        self.map_point = None

    def setLayers(self, layers:List[QgsMapLayer]):
        del self.layers[:]
        self.layers = [ item for item in layers ]

    def setMapPoint(self, point:QgsPointXY)->None:
        self.map_point = point
        self.updateCanvas() # Call self.paint
      
    def paint(self, painter:QPainter, *args): # NEED *args for   WINDOWS!
        if len( self.layers ) == 0 or self.map_point is None:
            return

        pixel_point = self.toCanvasCoordinates( self.map_point )
        if  not self.inCanvas( pixel_point.x(), pixel_point.y() ):
            return
        
        min_size = min( self.image.width(), self.image.height() )
        #min_size = min( self.boundingRect().width(), self.boundingRect().height() )
        d = int( min_size / 10 * self.magnifier_factor )
        r = d // 2
        pixel_point = self.settings.mapToPixel().transform( self.map_point )
        rect_region = QRect(
            int( pixel_point.x() ) - r,
            int( pixel_point.y() ) - r,
            d, d
        )
        region = QRegion( rect_region, QRegion.Ellipse )
        painter.setClipRegion( region )
        painter.drawImage( 0, 0, self.image )

        # min_size = min( self.boundingRect().width(), self.boundingRect().height() )
        # d = int( min_size / 10 * self.magnifier_factor )
        # r = d // 2
        # pixel_point = self.toCanvasCoordinates( self.map_point )
        # rect_ellipse = QRect(
        #     int( pixel_point.x() ) - r,
        #     int( pixel_point.y() ) - r,
        #     d, d
        # )
        # painter.setRenderHint( QPainter.Antialiasing ) # Smooths edges
        # painter.drawEllipse( rect_ellipse )
        


        # r = ( min_size / 10 * self.magnifier_factor ) // 2 # / self.magnification_factor
        # clip_path = QPainterPath()
        # clip_path.addEllipse( self.point.x() - r, self.point.y() - r, r, r )
        # painter.setClipPath( clip_path )

        # painter.setRenderHint( QPainter.Antialiasing ) # Smooths edges
        # painter.drawImage( 0,0, self.image )
        # #painter.drawEllipse( magnifier_rect )

    # It is a slot, the decorator 'pyqtSlot' fail because QgsMapCanvasItem not is QObject
    def setMap(self):
        def finished():
            image = job.renderedImage()
            if bool( self.canvas.property('retro') ):
                image = image.scaled( image.width() / 3, image.height() / 3 )
                image = image.convertToFormat( QImage.Format_Indexed8, Qt.OrderedDither | Qt.OrderedAlphaDither )
            self.image = image

        if len( self.layers ) == 0:
            return

        self.settings = QgsMapSettings( self.canvas.mapSettings() )
        self.settings.setLayers( self.layers )
        self.settings.setBackgroundColor( QColor( Qt.transparent ) )
        self.settings.setMagnificationFactor( float(self.magnification_factor ) )
        self.settings.setDevicePixelRatio( 1 )
        
        self.setRect( self.canvas.extent() )
        job = QgsMapRendererParallelJob( self.settings ) 
        job.start()
        job.finished.connect( finished) 
        job.waitForFinished()

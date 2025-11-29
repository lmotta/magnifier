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
    QgsPointXY, QgsRectangle
)
from qgis.gui import (
    QgsMapCanvas, QgsMapCanvasItem
)

class MagnifierMap(QgsMapCanvasItem):
    def __init__(self, canvas:QgsMapCanvas):
        super().__init__( canvas )
        self.map_settings = None
        self.zoom_factor = 2
        self.magnifier_factor = 2
        self.setZValue(10)
        self.layers = []
        self.map_point = None
        self.canvas = canvas
        self.image = None

        self.inCanvas = lambda x, y: x > 0 or x < self.boundingRect().width() or y > 0 or y < self.boundingRect().height()
      
    def clear(self)->None:
        self.layers = []
        self.map_point = None
        self.image = None
        self.updateCanvas()

    def setLayers(self, layers:List[QgsMapLayer]):
        self.layers = layers

    def setMapPoint(self, point:QgsPointXY)->None:
        self.map_point = point
        self.updateCanvas() # Call self.paint
      
    def paint(self, painter:QPainter, *args): # NEED *args for   WINDOWS!
        if not self.layers or self.map_point is None or self.image is None:
            return

        pixel_point = self.toCanvasCoordinates( self.map_point )
        if  not self.inCanvas( pixel_point.x(), pixel_point.y() ):
            return
        
        #min_size = min( self.image.width(), self.image.height() )
        min_size = min( self.boundingRect().width(), self.boundingRect().height() )
        d = int( min_size / 10 * self.magnifier_factor )
        r = d // 2
        #pixel_point = self.map_settings.mapToPixel().transform( self.map_point )
        rect_region = QRect(
            int( pixel_point.x() ) - r,
            int( pixel_point.y() ) - r,
            d, d
        )
        region = QRegion( rect_region, QRegion.Ellipse )
        painter.setClipRegion( region )
        
        offset_x = pixel_point.x() * (1 - self.zoom_factor)
        offset_y = pixel_point.y() * (1 - self.zoom_factor)        
        painter.drawImage( int(offset_x), int(offset_y), self.image )



        # --- Acabamento ---
        # Desenha a borda da lupa (opcional, para melhor visualização)
        painter.setClipping(False)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.black)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect_region)


        # painter.setRenderHint( QPainter.Antialiasing ) # Smooths edges
        # painter.drawImage( 0,0, self.image )
        # painter.drawEllipse( rect_region )

    # It is a slot, the decorator 'pyqtSlot' fail because QgsMapCanvasItem not is QObject
    def setMap(self):
        def createMapSettingsWithZoomFactor():
            settings = QgsMapSettings()
            settings.setLayers( self.layers )
            settings.setDestinationCrs( self.canvas.mapSettings().destinationCrs() )

            # settings.setOutputSize( self.canvas.size() )
            # settings.setBackgroundColor( QColor( Qt.transparent ) )
            
            # settings.setExtent( self.canvas.extent() )
            # settings.setMagnificationFactor( self.zoom_factor )

            # --- CORREÇÃO DE TAMANHO ---
            # Multiplicamos o tamanho de saída pelo fator de zoom.
            # Isso cria uma imagem fisicamente maior (mais pixels para a mesma área geográfica).
            new_size = self.canvas.size() * self.zoom_factor
            settings.setOutputSize(new_size)
            
            settings.setBackgroundColor(QColor(Qt.white)) # Fundo branco ou transparente
            
            # Mantemos a MESMA extensão geográfica do canvas.
            # Como a imagem é maior, teremos mais detalhes (zoom).
            settings.setExtent(self.canvas.extent())
            
            # Nota: Não usamos setMagnificationFactor aqui, pois aumentamos o OutputSize.
            # Se usar setMagnificationFactor, o texto aumenta, mas a imagem não ganha resolução.


            return settings

        def finished():
            image = job.renderedImage()
            if bool( self.canvas.property('retro') ):
                image = image.scaled( image.width() / 3, image.height() / 3 )
                image = image.convertToFormat( QImage.Format_Indexed8, Qt.OrderedDither | Qt.OrderedAlphaDither )
            self.image = image

        if not self.layers:
            return

        self.map_settings = createMapSettingsWithZoomFactor()
        
        self.setRect( self.canvas.extent() )
        job = QgsMapRendererParallelJob( self.map_settings ) 
        job.start()
        job.finished.connect( finished) 
        job.waitForFinished()

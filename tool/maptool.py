# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Magnifier tool
Description          : Plugin for magnifier active layer
Date                 : November, 2025
copyright            : (C) 2025 by Luiz Motta
email                : motta.luiz@gmail.com

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

from qgis._core import QgsLayerTreeLayer
from qgis.PyQt.QtCore import (
  Qt,
  QPoint,
  pyqtSlot,
  QItemSelection
)
from qgis.PyQt.QtGui import QCursor


from qgis.core import QgsLayerTreeLayer, QgsMapLayer, QgsProject
from qgis.gui import QgisInterface, QgsMapTool, QgsMapMouseEvent

from .magnifiermap import MagnifierMap
from .translate import tr


class MagnifierTool(QgsMapTool):
    def __init__(self, title:str, iface:QgisInterface):
        self.canvas = iface.mapCanvas()
        super().__init__( self.canvas )
        self.view = iface.layerTreeView()
        self.msg_bar = iface.messageBar()
        self.title = title
        self.magnifier_map = MagnifierMap( self.canvas )
        self.enabled_magnifier = None

        self._signal_slot = (
            { 'signal': QgsProject.instance().removeAll, 'slot': self.disable },
            { 'signal': self.view.selectionModel().selectionChanged, 'slot': self.setLayers },
            { 'signal': self.canvas.mapCanvasRefreshed, 'slot': self.magnifier_map.setMap }
        )
  
    def _connect(self, isConnect:bool = True)->None:
        if isConnect:
            for item in self._signal_slot:
                item['signal'].connect( item['slot'] )
            return

        for item in self._signal_slot:
            item['signal'].disconnect( item['slot'] )

    @pyqtSlot()
    def activate(self)->None:
        super().activate()
        self.canvas.setCursor( QCursor( Qt.CrossCursor ) )
        self._connect()
        self.enabled_magnifier = True
        self.setLayers( None, None )

    @pyqtSlot()
    def deactivate(self)->None:
        super().deactivate()
        self.deactivated.emit()
        self.magnifier_map.clear()
        self.disable()

    @pyqtSlot(QgsMapMouseEvent)
    def canvasPressEvent(self, e:QgsMapMouseEvent)->None:
        if len( self.magnifier_map.layers ) == 0:
            self.msg_bar.clearWidgets()
            self.msg_bar.pushWarning( self.title, tr('Select Layer or Group in legend.') )

            return

    @pyqtSlot(QgsMapMouseEvent)
    def canvasReleaseEvent(self, e:QgsMapMouseEvent)->None:
        if not self.enabled_magnifier or len( self.magnifier_map.layers ) == 0:
            return

        #self.magnifier_map.setMapPoint( e.mapPoint() )
    
    @pyqtSlot(QgsMapMouseEvent)
    def canvasMoveEvent(self, e:QgsMapMouseEvent)->None:
        if not self.enabled_magnifier or len( self.magnifier_map.layers ) == 0:
            return

        self.magnifier_map.setMapPoint( e.mapPoint() )

    @pyqtSlot(QItemSelection,QItemSelection)
    def setLayers(self, selected:QItemSelection, deselected:QItemSelection)->None:
        def finished(layers:List[QgsMapLayer], message:str)->None:
            self.magnifier_map.clear()
            self.magnifier_map.setLayers( layers )
            self.magnifier_map.setMap()

            self.msg_bar.clearWidgets()
            self.msg_bar.pushInfo( self.title, message )

        if not self.enabled_magnifier:
            return

        layers, msg = None, None
        node = self.view.currentNode()
        if node.itemVisibilityChecked():
            node.setItemVisibilityChecked( False )

        if isinstance( node, QgsLayerTreeLayer ):
            layer = node.layer()
            if not layer.isSpatial():
                f = tr("Active layer '{}' need be a spatial layer.")
                msg = f.format( layer.name() )
                self.msgBar.pushWarning( self.pluginName, msg )

                return

            layers = [ layer ]
            f = tr("Active layer is '{}'.")
            msg = f.format( layer.name() )
            finished( layers, msg )

            return

        group = self.view.currentGroupNode()
        if group.parent() is None: # Root
            return

        layers = [ ltl.layer() for ltl in group.findLayers() if ltl.itemVisibilityChecked() ]
        if len( layers ) ==  0:
            self.msg_bar.clearWidgets()
            f = tr("Active group '{}' need at least one item with visible checked")
            msg = f.format( group.name() )
            self.msg_bar.pushWarning( self.title, msg )

            return

        f = tr("Active group is '{}'.")
        msg = f.format( group.name() )
        finished( layers, msg )

    @pyqtSlot()
    def disable(self):
        self._connect( False )
        self.magnifier_map.clear()
        self.enabled_magnifier = False
        

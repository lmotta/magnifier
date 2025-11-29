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


from qgis.core import (
    QgsLayerTreeLayer, QgsMapLayer,
    QgsProject
)
from qgis.gui import (
    QgisInterface,
    QgsMapTool, QgsMapToolPan,
    QgsMapMouseEvent
)

from .magnifiermap import MagnifierMap
from .translate import tr


class MagnifierTool(QgsMapTool):
    def __init__(self, title:str, iface:QgisInterface):
        self.canvas = iface.mapCanvas()
        super().__init__( self.canvas )
        self.view = iface.layerTreeView()
        self.msg_bar = iface.messageBar()
        self.project = QgsProject.instance()
        self.title = title
        self.magnifier_map = MagnifierMap( self.canvas )
        self.enabled_magnifier = False

        self._signal_slot = (
            { 'signal': self.project.removeAll, 'slot': self.disable },
            { 'signal': self.view.selectionModel().selectionChanged, 'slot': self.setLayers },
            { 'signal': self.canvas.extentsChanged, 'slot': self.magnifier_map.setMap }
        )
  
    def _connect(self, isConnect:bool = True)->None:
        if isConnect:
            for item in self._signal_slot:
                item['signal'].connect( item['slot'] )
            return

        for item in self._signal_slot:
            item['signal'].disconnect( item['slot'] )

    def canExecute(self):
        if not len( self.project.mapLayers() ):
            self.msg_bar.pushWarning( self.title, tr('Missing layers required for tool.') )
            return False
        
        return True

    @pyqtSlot()
    def disable(self):
        self.magnifier_map.clear() # OUT self.magnifier_map.setMap
        self.enabled_magnifier = False

    @pyqtSlot(QItemSelection,QItemSelection)
    def setLayers(self, selected:QItemSelection, deselected:QItemSelection)->None:
        def finished(layers:List[QgsMapLayer], message:str)->None:
            self.magnifier_map.setLayers( layers )
            self.magnifier_map.setMap()

            node.setItemVisibilityChecked( False )

            self.msg_bar.clearWidgets()
            self.msg_bar.pushInfo( self.title, message )

        if not self.enabled_magnifier:
            return

        node = self.view.currentNode()
        if node is None: # Example BAND (tree item)
            return

        if self.project.layerTreeRoot() == node:
            self.disable()
            self.msg_bar.clearWidgets()
            return


        if isinstance( node, QgsLayerTreeLayer ):
            layer = node.layer()
            if layer in self.magnifier_map.layers:
                return

            if not layer.isSpatial():
                f = tr("Active layer '{}' need be a spatial layer.")
                msg = f.format( layer.name() )
                self.msgBar.pushWarning( self.pluginName, msg )

                return

            node.setItemVisibilityChecked( True )
            f = tr("Active layer is '{}'.")
            msg = f.format( layer.name() )
            finished( [ layer ], msg )

            return

        # Group
        layers = [ ltl.layer() for ltl in node.findLayers() if ltl.itemVisibilityChecked() ]
        if len( layers ) ==  0:
            self.msg_bar.clearWidgets()
            f = tr("Active group '{}' need at least one item with visible checked")
            msg = f.format( node.name() )
            self.msg_bar.pushWarning( self.title, msg )

            return

        f = tr("Active group is '{}'.")
        msg = f.format( node.name() )
        finished( layers, msg )

    # QgsMapTool Signals
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
        self._connect( False )
        self.disable()

    # @pyqtSlot(QgsMapMouseEvent)
    # def canvasPressEvent(self, e:QgsMapMouseEvent)->None:
    #     if not self.enabled_magnifier or not self.magnifier_map.layers:
    #         return

    # @pyqtSlot(QgsMapMouseEvent)
    # def canvasReleaseEvent(self, e:QgsMapMouseEvent)->None:
    #     if not self.enabled_magnifier or not self.magnifier_map.layers:
    #         return

    #     #self.magnifier_map.setMapPoint( e.mapPoint() )
    
    @pyqtSlot(QgsMapMouseEvent)
    def canvasMoveEvent(self, e:QgsMapMouseEvent)->None:
        if not self.enabled_magnifier or not self.magnifier_map.layers:
            return

        self.magnifier_map.setMapPoint( e.mapPoint() )
        

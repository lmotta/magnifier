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
  QItemSelection,
  QModelIndex
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
        self.toggle_magnifier = False # If True, the magnifier will be toggled when the mouse is released
        self.current_magnifier = None

        self._signal_slot = (
            { 'signal': self.project.removeAll, 'slot': self.disable },
            { 'signal': self.view.selectionModel().currentChanged, 'slot': self.setLayers },
            
            # {
            #     'signal': self.view.selectionModel().currentChanged,
            #     'slot': lambda current, previus: print( f"{ 'Nothing' if current is None else current.data() }" )
            # },

            { 'signal': self.canvas.extentsChanged, 'slot': self.magnifier_map.setMap },
            # self.magnifier_map Signals
            {
                'signal': self.magnifier_map.signals.creatingImage,
                'slot': lambda: self.msg_bar.pushInfo(
                    self.title,
                    tr('Magnifier image rendering in progress ({})...').format( self.current_magnifier )
                )
            },
            {
                'signal': self.magnifier_map.signals.finishedImage,
                'slot': lambda: self.msg_bar.clearWidgets()
            }
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
        self.magnifier_map.clear()
        self.enabled_magnifier = False
  
    @pyqtSlot(QModelIndex,QModelIndex)
    def setLayers(self, current:QModelIndex, previous:QModelIndex)->None:
        def finished(layers:List[QgsMapLayer])->None:
            self.magnifier_map.setLayers( layers )
            self.magnifier_map.setMap()
            node.setItemVisibilityChecked( False )

        if not self.enabled_magnifier or current is None:
            return

        node = self.view.index2node( current )
        if node is None: # index is subtree
            return

        if self.project.layerTreeRoot() == node:
            self.disable()
            self.msg_bar.clearWidgets()
            return

        self.current_magnifier = node.name()

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
            finished( [ layer ] )

            return

        # Group
        layers = [ ltl.layer() for ltl in node.findLayers() if ltl.itemVisibilityChecked() ]
        if len( layers ) ==  0:
            self.msg_bar.clearWidgets()
            f = tr("Active group '{}' need at least one item with visible checked")
            msg = f.format( node.name() )
            self.msg_bar.pushWarning( self.title, msg )

            return
        
        finished( layers )

    # QgsMapTool Signals
    @pyqtSlot()
    def activate(self)->None:
        super().activate()
        self.canvas.setCursor( QCursor( Qt.CrossCursor ) )
        self._connect()
        self.enabled_magnifier = True
        self.setLayers( self.view.currentIndex(), None )

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

    @pyqtSlot(QgsMapMouseEvent)
    def canvasReleaseEvent(self, e:QgsMapMouseEvent)->None:
        if not self.enabled_magnifier or not self.magnifier_map.layers:
            return

        self.toggle_magnifier = not self.toggle_magnifier
        if self.toggle_magnifier:
            pass

    @pyqtSlot(QgsMapMouseEvent)
    def canvasMoveEvent(self, e:QgsMapMouseEvent)->None:
        if not self.enabled_magnifier or not self.magnifier_map.layers:
            return

        if self.toggle_magnifier:
            return

        self.magnifier_map.setPixelPoint( e.pixelPoint() )
        

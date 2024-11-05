# -*- coding: utf-8 -*-

__author__ = 'Sanda Takeru'
__date__ = '2024-07-17'
__copyright__ = '(C) 2024 by Sanda Takeru'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from pathlib import Path
from PyQt5.QtGui import QIcon
from qgis.core import QgsProcessingProvider
from .online_map_linker_algorithm import OnlineMapLinkerHTML,OnlineMapLinkerCSV,OnlineMapLinkerLayer, OnlineMapLinkerMulti


class OnlineMapLinkerProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.addAlgorithm(OnlineMapLinkerHTML())
        self.addAlgorithm(OnlineMapLinkerCSV())
        self.addAlgorithm(OnlineMapLinkerLayer())
        self.addAlgorithm(OnlineMapLinkerMulti())
        # add additional algorithms here

    def id(self):
        return 'Online Map Linker'

    def name(self):
        return self.tr('Online Map Linker')

    def icon(self):
        path = (Path(__file__).parent / "icon.svg").resolve()
        return QIcon(str(path))

    def longName(self):
        return self.name()

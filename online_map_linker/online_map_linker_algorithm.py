# -*- coding: utf-8 -*-

__author__ = 'Sanda Takeru'
__date__ = '2024-07-17'
__copyright__ = '(C) 2024 by Sanda Takeru'
__revision__ = '$Format:%H$'

import tempfile, datetime

from qgis.PyQt.QtCore import QCoreApplication, QMetaType
from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField, QgsProcessingParameterEnum, QgsCoordinateReferenceSystem, QgsProcessingParameterFileDestination,
                       QgsCoordinateTransform, QgsProject, QgsProcessingOutputHtml, QgsProcessingOutputFile, QgsVectorFileWriter, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsProcessingParameterString, QgsProcessingParameterCrs, QgsFeatureRequest)

class OnlineMapLinkerBase(QgsProcessingAlgorithm):
    MAP_LIST = ['Google Maps', 'Apple Maps', 'Open Street Map', 'GSI Maps Japan', 'GSI Maps Vector Japan', 'Google Earth', 'Yahoo! MAP', 'Bing Maps', 'Mapion', 'MapFan']

    def createCoordinateTransform(self, source_crs):
        crs_wgs84 = QgsCoordinateReferenceSystem(4326)
        return QgsCoordinateTransform(source_crs, crs_wgs84, QgsProject.instance())

    def getSortedFeatures(self, point_layer, sort_field):
        if sort_field:
            order_by_clause = QgsFeatureRequest.OrderByClause(sort_field)
            order_by = QgsFeatureRequest.OrderBy([order_by_clause])
            request = QgsFeatureRequest().setOrderBy(order_by)
            return point_layer.getFeatures(request)
        return point_layer.getFeatures()

    def generateLinkFunction(self, map_name):
        if (map_name == 'Google Maps'):
            return lambda x, y, name: f"https://www.google.com/maps/place/{y}N+{x}E/@{y},{x},16z"
        elif (map_name == 'Apple Maps'):
            return lambda x, y, name: f"https://maps.apple.com/?ll={y},{x}&q={name}&t=m"
        elif (map_name == 'Open Street Map'):
            return lambda x, y, name: f"https://www.openstreetmap.org/?mlat={y}&mlon={x}#map=16/{y}/{x}"
        elif (map_name == 'GSI Maps Japan'):
            return lambda x, y, name: f"https://maps.gsi.go.jp/#16/{y}/{x}"
        elif (map_name == 'GSI Maps Vector Japan'):
            return lambda x, y, name: f"https://maps.gsi.go.jp/vector/#16/{y}/{x}/&ls=vstd&disp=1&d=l"
        elif (map_name == 'Google Earth'):
            return lambda x, y, name: f"https://earth.google.com/web/@{y},{x},20000d"
        elif (map_name == 'Yahoo! MAP'):
            return lambda x, y, name: f"https://map.yahoo.co.jp/?lat={y}&lon={x}&zoom=16&maptype=basic"
        elif (map_name == 'Bing Maps'):
            return lambda x, y, name: f"https://www.bing.com/maps?cp={y}%7E{x}&lvl=16.0"
        elif (map_name == 'Mapion'):
            return lambda x, y, name: f"https://www.mapion.co.jp/m2/{y},{x},16"
        elif (map_name == 'MapFan'):
            return lambda x, y, name: f"https://mapfan.com/map?c={y},{x},16"
        else:
            raise Exception('No online maps found. Exiting process.')

class OnlineMapLinkerHTML(OnlineMapLinkerBase):
    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    NAME_FIELD = 'name_field'
    SORT_FIELD = 'sort_field'
    POINT_LAYER = 'point_layer'
    ONLINE_MAP = 'online_map'
    HTML_PATH = 'html_path'

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT_LAYER, 'Point Layer for creating links', types=[QgsProcessing.SourceType.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum(self.ONLINE_MAP, 'Online Map', options=self.MAP_LIST, allowMultiple=False, usesStaticStrings=False, defaultValue='Open Street Map'))
        self.addParameter(QgsProcessingParameterField(self.NAME_FIELD, 'Name Field - If blank, the coordinates will be used.', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterField(self.SORT_FIELD, 'Sort Field', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterFileDestination(self.HTML_PATH, 'HTML Output', fileFilter='HTML files (*.html)', defaultValue=None))
        self.addOutput(QgsProcessingOutputHtml(self.OUTPUT, 'Online Map Linker (HTML) output'))

    def processAlgorithm(self, parameters, context, feedback):
        point_layer = self.parameterAsSource(parameters, self.POINT_LAYER, context)
        online_map = self.parameterAsEnum(parameters, self.ONLINE_MAP, context)
        name_field = self.parameterAsString(parameters, self.NAME_FIELD, context)
        sort_field = self.parameterAsString(parameters, self.SORT_FIELD, context)
        html_path = self.parameterAsString(parameters, self.HTML_PATH, context)

        if point_layer.featureCount() == 0:
            error_msg = 'The layer has no features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)

        transform = self.createCoordinateTransform(point_layer.sourceCrs())
        features = self.getSortedFeatures(point_layer, sort_field)

        link_function = self.generateLinkFunction(self.MAP_LIST[online_map])

        html_output = "<html><head><meta charset=\"utf-8\"></head><body><h1>Online Map Linker</h1><ul>\n"
        for feature in features:
            geometry = feature.geometry()
            geometry.transform(transform)
            x, y = geometry.asPoint().x(), geometry.asPoint().y()
            name = feature[name_field] if name_field else f"{x}, {y}"
            link = link_function(x, y, name)
            html_output += f"<li><a href='{link}'>{name} ({self.MAP_LIST[online_map]})</a></li>\n"
        html_output += '</ul><p>Generated by the QGIS plugin "<a href="https://plugins.qgis.org/plugins/online_map_linker/" target="_blank">Online Map Linker</a>".</p></body></html>'

        output_filepath = tempfile.gettempdir() + '/OML('+self.MAP_LIST[online_map]+')_'+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')+'.html' if 'html_path.html' in html_path else html_path
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(html_output)
        return {self.OUTPUT: output_filepath}

    def name(self):
        return 'Online Map Linker (HTML)'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return None

    def groupId(self):
        return None

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return OnlineMapLinkerHTML()

class OnlineMapLinkerCSV(OnlineMapLinkerBase):
    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    SORT_FIELD = 'sort_field'
    POINT_LAYER = 'point_layer'
    ONLINE_MAP = 'online_map'
    CSV_PATH = 'csv_path'

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT_LAYER, 'Point Layer for creating links', types=[QgsProcessing.SourceType.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum(self.ONLINE_MAP, 'Online Map', options=self.MAP_LIST, allowMultiple=False, usesStaticStrings=False, defaultValue='Open Street Map'))
        self.addParameter(QgsProcessingParameterField(self.SORT_FIELD, 'Sort Field', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterFileDestination(self.CSV_PATH, 'CSV Output', fileFilter='CSV files (*.csv)', defaultValue=None))
        self.addOutput(QgsProcessingOutputFile(self.OUTPUT, 'Online Map Linker (CSV) output'))

    def processAlgorithm(self, parameters, context, feedback):
        point_layer = self.parameterAsSource(parameters, self.POINT_LAYER, context)
        online_map = self.parameterAsEnum(parameters, self.ONLINE_MAP, context)
        sort_field = self.parameterAsString(parameters, self.SORT_FIELD, context)
        csv_path = self.parameterAsString(parameters, self.CSV_PATH, context)

        if point_layer.featureCount() == 0:
            error_msg = 'The layer has no features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)

        transform = self.createCoordinateTransform(point_layer.sourceCrs())
        features = self.getSortedFeatures(point_layer, sort_field)

        link_function = self.generateLinkFunction(self.MAP_LIST[online_map])

        source_crs = point_layer.sourceCrs()
        output_layer = QgsVectorLayer(f"Point?crs={source_crs.authid()}", "online map linked", "memory")
        output_layer_data = output_layer.dataProvider()
        output_layer_data.addAttributes(point_layer.fields().toList())
        output_layer.updateFields()

        oml_field = "OML_" + self.MAP_LIST[online_map]
        output_layer.dataProvider().addAttributes([QgsField(oml_field, QMetaType.Type.QString)])
        output_layer.updateFields()

        for feature in features:
            wgs84_point = transform.transform(feature.geometry().asPoint())
            x, y = wgs84_point.x(), wgs84_point.y()
            link = link_function(x, y, "Pin")
            new_feature = QgsFeature(output_layer.fields())
            new_feature.setGeometry(feature.geometry())
            for field in point_layer.fields():
                new_feature[field.name()] = feature[field.name()]
            new_feature[oml_field] = link
            output_layer_data.addFeatures([new_feature])

        output_filepath = tempfile.gettempdir() + '/OML('+self.MAP_LIST[online_map]+')_'+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')+'.csv' if 'csv_path.csv' in csv_path else csv_path
        output_layer.updateFields()
        csv_options = QgsVectorFileWriter.SaveVectorOptions()
        csv_options.driverName = 'CSV'
        csv_options.fileEncoding = 'Shift_JIS'
        QgsVectorFileWriter.writeAsVectorFormatV3(output_layer, output_filepath, QgsProject.instance().transformContext(), csv_options)
        return {self.OUTPUT: output_filepath}

    def name(self):
        return 'Online Map Linker (CSV)'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return None

    def groupId(self):
        return None

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return OnlineMapLinkerCSV()

class OnlineMapLinkerLayer(OnlineMapLinkerBase):
    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    SORT_FIELD = 'sort_field'
    POINT_LAYER = 'point_layer'
    ONLINE_MAP = 'online_map'
    LAYER_PATH = 'layer_path'
    OUTPUT_CRS = 'output_crs'

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT_LAYER, 'Point Layer for creating links', types=[QgsProcessing.SourceType.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum(self.ONLINE_MAP, 'Online Map', options=self.MAP_LIST, allowMultiple=False, usesStaticStrings=False, defaultValue='Open Street Map'))
        self.addParameter(QgsProcessingParameterField(self.SORT_FIELD, 'Sort Field', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterCrs(self.OUTPUT_CRS, 'Output CRS', defaultValue='ProjectCrs'))
        self.addParameter(QgsProcessingParameterFileDestination(self.LAYER_PATH, 'Layer Output', fileFilter='GeoPackage file (*.gpkg)', defaultValue=None))

    def processAlgorithm(self, parameters, context, feedback):
        point_layer = self.parameterAsSource(parameters, self.POINT_LAYER, context)
        online_map = self.parameterAsEnum(parameters, self.ONLINE_MAP, context)
        sort_field = self.parameterAsString(parameters, self.SORT_FIELD, context)
        layer_path = self.parameterAsString(parameters, self.LAYER_PATH, context)
        output_crs = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)

        if point_layer.featureCount() == 0:
            error_msg = 'The layer has no features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)

        transform = self.createCoordinateTransform(point_layer.sourceCrs())
        geom_transform = QgsCoordinateTransform(point_layer.sourceCrs(), output_crs, QgsProject.instance())
        features = self.getSortedFeatures(point_layer, sort_field)

        link_function = self.generateLinkFunction(self.MAP_LIST[online_map])

        output_layer = QgsVectorLayer(f"Point?crs={output_crs.authid()}", "online map linked", "memory")
        output_layer_data = output_layer.dataProvider()
        output_layer_data.addAttributes(point_layer.fields().toList())
        output_layer.updateFields()

        oml_field = "OML_" + self.MAP_LIST[online_map]
        output_layer.dataProvider().addAttributes([QgsField(oml_field, QMetaType.Type.QString)])
        output_layer.updateFields()

        for feature in features:
            source_pt = feature.geometry().asPoint()
            wgs84_point = transform.transform(source_pt)
            x, y = wgs84_point.x(), wgs84_point.y()
            link = link_function(x, y, "Pin")
            out_pt = geom_transform.transform(source_pt)
            new_feature = QgsFeature(output_layer.fields())
            new_feature.setGeometry(QgsGeometry.fromPointXY(out_pt))
            for field in point_layer.fields():
                new_feature[field.name()] = feature[field.name()]
            new_feature[oml_field] = link
            output_layer_data.addFeatures([new_feature])

        if layer_path == QgsProcessing.TEMPORARY_OUTPUT or 'layer_path' in layer_path:
            output_layer.setName('online_map_linked')
            QgsProject.instance().addMapLayer(output_layer)
        else:
            layer_options = QgsVectorFileWriter.SaveVectorOptions()
            layer_options.driverName = 'GPKG'
            layer_options.fileEncoding = 'UTF-8'
            QgsVectorFileWriter.writeAsVectorFormatV3(output_layer, layer_path, QgsProject.instance().transformContext(), layer_options)
            QgsProject.instance().addMapLayer(QgsVectorLayer(layer_path, 'online_map_linked', 'ogr'))
        return {self.OUTPUT: layer_path}

    def name(self):
        return 'Online Map Linker (Layer)'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return None

    def groupId(self):
        return None

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return OnlineMapLinkerLayer()

class OnlineMapLinkerMulti(OnlineMapLinkerBase):
    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    SORT_FIELD = 'sort_field'
    POINT_LAYER = 'point_layer'
    HTML_PATH = 'html_path'
    URL_TITLE = 'url_title'

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT_LAYER, 'Point Layer for creating links (Up to 10 features.)', types=[QgsProcessing.SourceType.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.SORT_FIELD, 'Sort Field', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterString(self.URL_TITLE, 'URL Title', defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterFileDestination(self.HTML_PATH, 'HTML Output', fileFilter='HTML files (*.html)', defaultValue=None))
        self.addOutput(QgsProcessingOutputHtml(self.OUTPUT, 'Online Map Linker "Multi-destination routing" (HTML) output'))

    def processAlgorithm(self, parameters, context, feedback):
        point_layer = self.parameterAsSource(parameters, self.POINT_LAYER, context)
        sort_field = self.parameterAsString(parameters, self.SORT_FIELD, context)
        html_path = self.parameterAsString(parameters, self.HTML_PATH, context)
        url_title = self.parameterAsString(parameters, self.URL_TITLE, context)

        feature_count = point_layer.featureCount()
        if feature_count == 0:
            error_msg = 'The layer has no features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)
        elif feature_count > 10:
            error_msg = 'The layer has over 10 features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)

        transform = self.createCoordinateTransform(point_layer.sourceCrs())
        features = self.getSortedFeatures(point_layer, sort_field)

        URL = 'https://www.google.co.jp/maps/dir'
        for feature in features:
            geometry = feature.geometry()
            geometry.transform(transform)
            x, y = geometry.asPoint().x(), geometry.asPoint().y()
            URL += f"/{y},{x}"

        link_text = f'<p><a href="{URL}" target="_blank">{url_title}</a></p>' if url_title else f'<p><a href="{URL}" target="_blank">{URL}</a></p>'
        html_output = f"<html><head><meta charset=\"utf-8\"></head><body><h1>Online Map Linker</h1>{link_text}<p>Generated by the QGIS plugin \"<a href=\"https://plugins.qgis.org/plugins/online_map_linker/\" target=\"_blank\">Online Map Linker</a>\".</p></body></html>"

        output_filepath = tempfile.gettempdir() + '/OML(Google Maps)_'+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')+'.html' if 'html_path.html' in html_path else html_path
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(html_output)
        return {self.OUTPUT: output_filepath}

    def name(self):
        return 'Multi-destination routing (HTML, Google Maps)'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return None

    def groupId(self):
        return None

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return OnlineMapLinkerMulti()
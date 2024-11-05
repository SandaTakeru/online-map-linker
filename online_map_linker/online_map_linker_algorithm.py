# -*- coding: utf-8 -*-

__author__ = 'Sanda Takeru'
__date__ = '2024-07-17'
__copyright__ = '(C) 2024 by Sanda Takeru'
__revision__ = '$Format:%H$'

# impor library
import tempfile, datetime

from qgis.PyQt.QtCore import QCoreApplication,QVariant

from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField, QgsProcessingParameterEnum, QgsCoordinateReferenceSystem, QgsProcessingParameterFileDestination,
                       QgsCoordinateTransform, QgsProject, QgsProcessingOutputHtml, QgsVectorFileWriter, QgsVectorLayer, QgsField, QgsProcessingParameterString)


class OnlineMapLinkerHTML(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    NAME_FIELD = 'name_field'
    SORT_FIELD = 'sort_field'
    POINT_LAYER = 'point_layer'
    ONLINE_MAP = 'online_map'
    MAP_LIST =['Google Maps', 'Apple Maps', 'Open Street Map', 'GSI Maps Japan', 'GSI Maps Vector Japan', 'Google Earth', 'Yahoo! MAP', 'Bing Maps', 'Mapion', 'MapFan'] #You can add online maps here!
    HTML_PATH = 'html_path'

    def initAlgorithm(self, config):
        
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT_LAYER, 'Point Layer for creating links', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum(self.ONLINE_MAP, 'Online Map', options=self.MAP_LIST, allowMultiple=False, usesStaticStrings=False, defaultValue='Open Street Map'))
        self.addParameter(QgsProcessingParameterField(self.NAME_FIELD, 'Name Field - If blank, the coordinates will be used.', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterField(self.SORT_FIELD, 'Sort Field', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterFileDestination(self.HTML_PATH, 'HTML Output', fileFilter='HTML files (*.html)', defaultValue=None))

        # Add an HTML output parameter
        self.addOutput(QgsProcessingOutputHtml(self.OUTPUT, 'Online Map Linker (HTML) output'))

    def processAlgorithm(self, parameters, context, feedback):
        # Get the input parameters
        point_layer = self.parameterAsSource(parameters, self.POINT_LAYER, context)
        online_map = self.parameterAsEnum(parameters, self.ONLINE_MAP, context)
        name_field = self.parameterAsString(parameters, self.NAME_FIELD, context)
        sort_field = self.parameterAsString(parameters, self.SORT_FIELD, context)
        output_filepath = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        map_list = self.MAP_LIST
        html_path = self.parameterAsString(parameters, self.HTML_PATH, context)
        
        # Check if the layer has features
        feature_count = point_layer.featureCount()     
        if feature_count == 0:
            error_msg = 'The layer has no features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)

        # Create a coordinate transform to WGS84
        crs_wgs84 = QgsCoordinateReferenceSystem(4326)
        transform = QgsCoordinateTransform(point_layer.sourceCrs(), crs_wgs84, QgsProject.instance())

        # Sort by SORT_FIELD
        if sort_field:
            features = sorted(point_layer.getFeatures(), key=lambda f: f[sort_field])
        else:
            features = point_layer.getFeatures()

        # Initialize the HTML output
        html_output = "<html><body><h1>Online Map Linker</h1><ul>\n"

        # Iterate over each feature in the point layer
        for feature in features:
            # Transform the feature's geometry to WGS84
            geometry = feature.geometry()
            geometry.transform(transform)

            # Get the coordinates of the point
            x = geometry.asPoint().x()
            y = geometry.asPoint().y()

            # Get the name of the point
            name = feature[name_field] if name_field else f"{x}, {y}"

            # Generate the online map link  # Add more elif conditions for other online maps
            if map_list[online_map] == 'Google Maps':
                link = f"https://www.google.com/maps/place/{y}N+{x}E/@{y},{x},16z"
            elif map_list[online_map] == 'Apple Maps':
                link = f"https://maps.apple.com/?ll={y},{x}&q={name}&t=m"
            elif map_list[online_map] == 'Open Street Map':
                link = f"https://www.openstreetmap.org/?mlat={y}&mlon={x}#map=16/{y}/{x}"
            elif map_list[online_map] == 'GSI Maps Japan':
                link = f"https://maps.gsi.go.jp/#16/{y}/{x}"
            elif map_list[online_map] == 'GSI Maps Vector Japan':
                link = f"https://maps.gsi.go.jp/vector/#16/{y}/{x}/&ls=vstd&disp=1&d=l"
            elif map_list[online_map] == 'Google Earth':
                link = f"https://earth.google.com/web/@{y},{x},20000d"
            elif map_list[online_map] == 'Yahoo! MAP':
                link = f"https://map.yahoo.co.jp/?lat={y}&lon={x}&zoom=16&maptype=basic"
            elif map_list[online_map] == 'Bing Maps':
                link = f"https://www.bing.com/maps?cp={y}%7E{x}&lvl=16.0"
            elif map_list[online_map] == 'Mapion':
                link = f"https://www.mapion.co.jp/m2/{y},{x},16"
            elif map_list[online_map] == 'MapFan':
                link = f"https://mapfan.com/map?c={y},{x},16"
            elif map_list[online_map] == 'XXXX':
                link = f""
            elif map_list[online_map] == 'XXXX':
                link = f""
            else:
                error_msg = 'No online maps found. Exiting process.'
                feedback.reportError(error_msg)
                raise Exception(error_msg)
            
            # Add the link to the HTML output
            html_output += f"<li><a href='{link}'>{name} ({map_list[online_map]})</a></li>\n"

        # Finalize the HTML output
        html_output += '</ul><p>Generated by the QGIS plugin "<a href="https://plugins.qgis.org/plugins/online_map_linker/" target="_blank">Online Map Linker</a>".</p></body></html>'

        # Write the HTML output to the output file
        if 'html_path.html' in html_path:
            output_filepath = tempfile.gettempdir() + '/OML('+map_list[online_map]+')_'+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')+'.html'
        else:
            output_filepath = html_path

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

class OnlineMapLinkerCSV(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    SORT_FIELD = 'sort_field'
    POINT_LAYER = 'point_layer'
    ONLINE_MAP = 'online_map'
    MAP_LIST =['Google Maps', 'Apple Maps', 'Open Street Map', 'GSI Maps Japan', 'GSI Maps Vector Japan', 'Google Earth', 'Yahoo! MAP', 'Bing Maps', 'Mapion', 'MapFan'] #You can add online maps here!
    CSV_PATH = 'csv_path'

    def initAlgorithm(self, config):
        
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT_LAYER, 'Point Layer for creating links', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum(self.ONLINE_MAP, 'Online Map', options=self.MAP_LIST, allowMultiple=False, usesStaticStrings=False, defaultValue='Open Street Map'))
        #self.addParameter(QgsProcessingParameterField(self.SORT_FIELD, 'Sort Field', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterFileDestination(self.CSV_PATH, 'CSV Output', fileFilter='CSV files (*.csv)', defaultValue=None))

        # Add an CSV output parameter
        self.addOutput(QgsProcessingOutputHtml(self.OUTPUT, 'Online Map Linker (CSV) output'))

    def processAlgorithm(self, parameters, context, feedback):
        # Get the input parameters
        point_layer = self.parameterAsSource(parameters, self.POINT_LAYER, context)
        online_map = self.parameterAsEnum(parameters, self.ONLINE_MAP, context)
        sort_field = self.parameterAsString(parameters, self.SORT_FIELD, context)
        output_filepath = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        map_list = self.MAP_LIST
        csv_path = self.parameterAsString(parameters, self.CSV_PATH, context)
        
        # Check if the layer has features
        feature_count = point_layer.featureCount()     
        if feature_count == 0:
            error_msg = 'The layer has no features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)
            
        # Create a coordinate transform to WGS84
        crs_wgs84 = QgsCoordinateReferenceSystem(4326)
        transform = QgsCoordinateTransform(point_layer.sourceCrs(), crs_wgs84, QgsProject.instance())

        # Sort by SORT_FIELD
        if sort_field:
            features = sorted(point_layer.getFeatures(), key=lambda f: f[sort_field])
        else:
            features = point_layer.getFeatures()

        output_layer = QgsVectorLayer("Point?crs=epsg:4326", "online map linked", "memory")
        output_layer_data = output_layer.dataProvider()
        output_layer_data.addAttributes(point_layer.fields().toList())
        output_layer.updateFields()

        oml_field = "OML_"+map_list[online_map]
        output_layer.dataProvider().addAttributes([QgsField(oml_field, QVariant.String)])
        output_layer.updateFields()

        # Iterate over each feature in the point layer
        for feature in features:

            # Transform the feature's geometry to WGS84
            geometry = feature.geometry()
            geometry.transform(transform)

            # Get the coordinates of the point
            x = geometry.asPoint().x()
            y = geometry.asPoint().y()

            # Generate the online map link  # Add more elif conditions for other online maps
            if map_list[online_map] == 'Google Maps':
                link = f"https://www.google.com/maps/place/{y}N+{x}E/@{y},{x},16z"
            elif map_list[online_map] == 'Apple Maps':
                link = f"https://maps.apple.com/?ll={y},{x}&q=Pin&t=m"
            elif map_list[online_map] == 'Open Street Map':
                link = f"https://www.openstreetmap.org/?mlat={y}&mlon={x}#map=16/{y}/{x}"
            elif map_list[online_map] == 'GSI Maps Japan':
                link = f"https://maps.gsi.go.jp/#16/{y}/{x}"
            elif map_list[online_map] == 'GSI Maps Vector Japan':
                link = f"https://maps.gsi.go.jp/vector/#16/{y}/{x}/&ls=vstd&disp=1&d=l"
            elif map_list[online_map] == 'Google Earth':
                link = f"https://earth.google.com/web/@{y},{x},20000d"
            elif map_list[online_map] == 'Yahoo! MAP':
                link = f"https://map.yahoo.co.jp/?lat={y}&lon={x}&zoom=16&maptype=basic"
            elif map_list[online_map] == 'Bing Maps':
                link = f"https://www.bing.com/maps?cp={y}%7E{x}&lvl=16.0"
            elif map_list[online_map] == 'Mapion':
                link = f"https://www.mapion.co.jp/m2/{y},{x},16"
            elif map_list[online_map] == 'MapFan':
                link = f"https://mapfan.com/map?c={y},{x},16"
            elif map_list[online_map] == 'XXXX':
                link = f""
            elif map_list[online_map] == 'XXXX':
                link = f""
            else:
                error_msg = 'No online maps found. Exiting process.'
                feedback.reportError(error_msg)
                raise Exception(error_msg)
            
            # Add the link to the output_layer
            output_layer_data.addFeatures([feature])
            attributes = {output_layer.fields().indexFromName(oml_field): link}
            output_layer_data.changeAttributeValues({feature.id(): attributes})

        # Write the CSV output to the output file
        if 'csv_path.csv' in csv_path:
            output_filepath = tempfile.gettempdir() + '/OML('+map_list[online_map]+')_'+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')+'.csv'
        else:
            output_filepath = csv_path

        output_layer.updateFields()
        QgsVectorFileWriter.writeAsVectorFormat(output_layer, output_filepath, "Shift_JIS", driverName="CSV")

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

class OnlineMapLinkerLayer(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    SORT_FIELD = 'sort_field'
    POINT_LAYER = 'point_layer'
    ONLINE_MAP = 'online_map'
    MAP_LIST =['Google Maps', 'Apple Maps', 'Open Street Map', 'GSI Maps Japan', 'GSI Maps Vector Japan', 'Google Earth', 'Yahoo! MAP', 'Bing Maps', 'Mapion', 'MapFan'] #You can add online maps here!
    LAYER_PATH = 'layer_path'

    def initAlgorithm(self, config):
        
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT_LAYER, 'Point Layer for creating links', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum(self.ONLINE_MAP, 'Online Map', options=self.MAP_LIST, allowMultiple=False, usesStaticStrings=False, defaultValue='Open Street Map'))
        #self.addParameter(QgsProcessingParameterField(self.SORT_FIELD, 'Sort Field', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterFileDestination(self.LAYER_PATH, 'Layer Output',fileFilter='GeoPackage file (*.gpkg)', defaultValue=None))

    def processAlgorithm(self, parameters, context, feedback):
        # Get the input parameters
        point_layer = self.parameterAsSource(parameters, self.POINT_LAYER, context)
        online_map = self.parameterAsEnum(parameters, self.ONLINE_MAP, context)
        sort_field = self.parameterAsString(parameters, self.SORT_FIELD, context)
        output_filepath = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        map_list = self.MAP_LIST
        layer_path = self.parameterAsString(parameters, self.LAYER_PATH, context)
        
        # Check if the layer has features
        feature_count = point_layer.featureCount()     
        if feature_count == 0:
            error_msg = 'The layer has no features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)
            
        # Create a coordinate transform to WGS84
        crs_wgs84 = QgsCoordinateReferenceSystem(4326)
        transform = QgsCoordinateTransform(point_layer.sourceCrs(), crs_wgs84, QgsProject.instance())

        # Sort by SORT_FIELD
        if sort_field:
            features = sorted(point_layer.getFeatures(), key=lambda f: f[sort_field])
        else:
            features = point_layer.getFeatures()

        output_layer = QgsVectorLayer("Point?crs=epsg:4326", "online map linked", "memory")
        output_layer_data = output_layer.dataProvider()
        output_layer_data.addAttributes(point_layer.fields().toList())
        output_layer.updateFields()

        oml_field = "OML_"+map_list[online_map]
        output_layer.dataProvider().addAttributes([QgsField(oml_field, QVariant.String)])
        output_layer.updateFields()

        # Iterate over each feature in the point layer
        for feature in features:

            # Transform the feature's geometry to WGS84
            geometry = feature.geometry()
            geometry.transform(transform)

            # Get the coordinates of the point
            x = geometry.asPoint().x()
            y = geometry.asPoint().y()

            # Generate the online map link  # Add more elif conditions for other online maps
            if map_list[online_map] == 'Google Maps':
                link = f"https://www.google.com/maps/place/{y}N+{x}E/@{y},{x},16z"
            elif map_list[online_map] == 'Apple Maps':
                link = f"https://maps.apple.com/?ll={y},{x}&q=Pin&t=m"
            elif map_list[online_map] == 'Open Street Map':
                link = f"https://www.openstreetmap.org/?mlat={y}&mlon={x}#map=16/{y}/{x}"
            elif map_list[online_map] == 'GSI Maps Japan':
                link = f"https://maps.gsi.go.jp/#16/{y}/{x}"
            elif map_list[online_map] == 'GSI Maps Vector Japan':
                link = f"https://maps.gsi.go.jp/vector/#16/{y}/{x}/&ls=vstd&disp=1&d=l"
            elif map_list[online_map] == 'Google Earth':
                link = f"https://earth.google.com/web/@{y},{x},20000d"
            elif map_list[online_map] == 'Yahoo! MAP':
                link = f"https://map.yahoo.co.jp/?lat={y}&lon={x}&zoom=16&maptype=basic"
            elif map_list[online_map] == 'Bing Maps':
                link = f"https://www.bing.com/maps?cp={y}%7E{x}&lvl=16.0"
            elif map_list[online_map] == 'Mapion':
                link = f"https://www.mapion.co.jp/m2/{y},{x},16"
            elif map_list[online_map] == 'MapFan':
                link = f"https://mapfan.com/map?c={y},{x},16"
            elif map_list[online_map] == 'XXXX':
                link = f""
            elif map_list[online_map] == 'XXXX':
                link = f""
            else:
                error_msg = 'No online maps found. Exiting process.'
                feedback.reportError(error_msg)
                raise Exception(error_msg)
            
            # Add the link to the output_layer
            output_layer_data.addFeatures([feature])
            attributes = {output_layer.fields().indexFromName(oml_field): link}
            output_layer_data.changeAttributeValues({feature.id(): attributes})
        
         # Write the HTML output to the output file
        print(layer_path)
        if 'layer_path' in layer_path:
            QgsProject.instance().addMapLayer(output_layer)
        else:
            QgsVectorFileWriter.writeAsVectorFormat(output_layer, layer_path, "UTF-8")
            QgsProject.instance().addMapLayer(QgsVectorLayer(layer_path, "online_map_linked", "ogr"))

        return {self.OUTPUT: output_filepath}

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

class OnlineMapLinkerMulti(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    #NAME_FIELD = 'name_field'
    SORT_FIELD = 'sort_field'
    POINT_LAYER = 'point_layer'
    #ONLINE_MAP = 'online_map'
    #MAP_LIST =['Google Maps', 'Apple Maps', 'Open Street Map', 'GSI Maps Japan', 'GSI Maps Vector Japan', 'Google Earth', 'Yahoo! MAP', 'Bing Maps', 'Mapion', 'MapFan'] #You can add online maps here!
    HTML_PATH = 'html_path'
    URL_TITLE = 'url_title'

    def initAlgorithm(self, config):
        
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT_LAYER, 'Point Layer for creating links (Up to 10 features.)', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        #self.addParameter(QgsProcessingParameterEnum(self.ONLINE_MAP, 'Online Map', options=self.MAP_LIST, allowMultiple=False, usesStaticStrings=False, defaultValue='Open Street Map'))
        #self.addParameter(QgsProcessingParameterField(self.NAME_FIELD, 'Name Field - If blank, the coordinates will be used.', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterField(self.SORT_FIELD, 'Sort Field', parentLayerParameterName=self.POINT_LAYER, allowMultiple=False, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterString(self.URL_TITLE, 'URL Title', defaultValue=None, optional=True))        
        self.addParameter(QgsProcessingParameterFileDestination(self.HTML_PATH, 'HTML Output', fileFilter='HTML files (*.html)', defaultValue=None))

        # Add an HTML output parameter
        self.addOutput(QgsProcessingOutputHtml(self.OUTPUT, 'Online Map Linker "Multi-destination routing" (HTML) output'))

    def processAlgorithm(self, parameters, context, feedback):
        # Get the input parameters
        point_layer = self.parameterAsSource(parameters, self.POINT_LAYER, context)
        #online_map = self.parameterAsEnum(parameters, self.ONLINE_MAP, context)
        #name_field = self.parameterAsString(parameters, self.NAME_FIELD, context)
        sort_field = self.parameterAsString(parameters, self.SORT_FIELD, context)
        output_filepath = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        #map_list = self.MAP_LIST
        html_path = self.parameterAsString(parameters, self.HTML_PATH, context)
        url_title = self.parameterAsString(parameters, self.URL_TITLE, context)
        
        # Check if the layer features count
        feature_count = point_layer.featureCount()     
        if feature_count == 0:
            error_msg = 'The layer has no features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)
        elif feature_count > 10:
            error_msg = 'The layer has over 10 features. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)

        # Create a coordinate transform to WGS84
        crs_wgs84 = QgsCoordinateReferenceSystem(4326)
        transform = QgsCoordinateTransform(point_layer.sourceCrs(), crs_wgs84, QgsProject.instance())

        # Sort by SORT_FIELD
        if sort_field:
            features = sorted(point_layer.getFeatures(), key=lambda f: f[sort_field])
        else:
            features = point_layer.getFeatures()

        # Initialize the HTML output
        html_output = "<html><body><h1>Online Map Linker</h1>\n"
        
        '''
        # Iterate over each feature in the point layer
        for feature in features:
            # Transform the feature's geometry to WGS84
            geometry = feature.geometry()
            geometry.transform(transform)

            # Get the coordinates of the point
            x = geometry.asPoint().x()
            y = geometry.asPoint().y()

            # Get the name of the point
            name = feature[name_field] if name_field else f"{x}, {y}"

            # Generate the online map link  # Add more elif conditions for other online maps
            if map_list[online_map] == 'Google Maps':
                link = f"https://www.google.com/maps/place/{y}N+{x}E/@{y},{x},16z"
            elif map_list[online_map] == 'Apple Maps':
                link = f"https://maps.apple.com/?ll={y},{x}&q={name}&t=m"
            elif map_list[online_map] == 'Open Street Map':
                link = f"https://www.openstreetmap.org/?mlat={y}&mlon={x}#map=16/{y}/{x}"
            elif map_list[online_map] == 'GSI Maps Japan':
                link = f"https://maps.gsi.go.jp/#16/{y}/{x}"
            elif map_list[online_map] == 'GSI Maps Vector Japan':
                link = f"https://maps.gsi.go.jp/vector/#16/{y}/{x}/&ls=vstd&disp=1&d=l"
            elif map_list[online_map] == 'Google Earth':
                link = f"https://earth.google.com/web/@{y},{x},20000d"
            elif map_list[online_map] == 'Yahoo! MAP':
                link = f"https://map.yahoo.co.jp/?lat={y}&lon={x}&zoom=16&maptype=basic"
            elif map_list[online_map] == 'Bing Maps':
                link = f"https://www.bing.com/maps?cp={y}%7E{x}&lvl=16.0"
            elif map_list[online_map] == 'Mapion':
                link = f"https://www.mapion.co.jp/m2/{y},{x},16"
            elif map_list[online_map] == 'MapFan':
                link = f"https://mapfan.com/map?c={y},{x},16"
            elif map_list[online_map] == 'XXXX':
                link = f""
            elif map_list[online_map] == 'XXXX':
                link = f""
            else:
                error_msg = 'No online maps found. Exiting process.'
                feedback.reportError(error_msg)
                raise Exception(error_msg)
                    
            # Add the link to the HTML output
            html_output += f"<li><a href='{link}'>{name} ({map_list[online_map]})</a></li>\n"
        '''

        # Make URL
        URL = 'https://www.google.co.jp/maps/dir'
        for feature in features:
            # Transform the feature's geometry to WGS84
            geometry = feature.geometry()
            geometry.transform(transform)

            # Get the coordinates of the point
            x = geometry.asPoint().x()
            y = geometry.asPoint().y()

            URL += f"/{y},{x}"

        # Finalize the HTML output
        if url_title:
            link_text = f'<p><a href="{URL}" target="_blank">{url_title}</a></p>'
        else:
            link_text = f'<p><a href="{URL}" target="_blank">{URL}</a></p>'

        html_output += f'{link_text}<p>Generated by the QGIS plugin "<a href="https://plugins.qgis.org/plugins/online_map_linker/" target="_blank">Online Map Linker</a>".</p></body></html>'

        # Write the HTML output to the output file
        if 'html_path.html' in html_path:
            output_filepath = tempfile.gettempdir() + '/OML(Google Maps)_'+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')+'.html'
        else:
            output_filepath = html_path

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
import sys
import os

# QGISアプリ初期化
sys.path.insert(0, '/Applications/QGIS4.02.app/Contents/Resources/python')
sys.path.insert(0, '/Applications/QGIS4.02.app/Contents/Resources/python/plugins')

os.environ['QGIS_PREFIX_PATH'] = '/Applications/QGIS4.02.app/Contents/MacOS'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from qgis.core import (
    QgsApplication, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField, QgsProject, QgsCoordinateReferenceSystem
)
from qgis.PyQt.QtCore import QMetaType

app = QgsApplication([], False)
app.initQgis()

# プラグインのパスを追加
plugin_dir = os.path.expanduser(
    '~/Library/Application Support/QGIS/QGIS4/profiles/Sanda Takeru/python/plugins'
)
sys.path.insert(0, plugin_dir)

from qgis.core import QgsProcessingFeedback, QgsProcessingContext

# online_map_linker を直接インポート
from online_map_linker.online_map_linker_algorithm import (
    OnlineMapLinkerHTML, OnlineMapLinkerCSV, OnlineMapLinkerLayer, OnlineMapLinkerMulti
)

# テスト用ポイントレイヤ作成（WGS84、東京・大阪・福岡）
layer = QgsVectorLayer('Point?crs=EPSG:4326', 'test_points', 'memory')
pr = layer.dataProvider()
pr.addAttributes([QgsField('name', QMetaType.Type.QString)])
layer.updateFields()

points = [
    ('東京', 139.6917, 35.6895),
    ('大阪', 135.5022, 34.6937),
    ('福岡', 130.4017, 33.5903),
]
features = []
for name, x, y in points:
    f = QgsFeature(layer.fields())
    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
    f['name'] = name
    features.append(f)
pr.addFeatures(features)
layer.updateExtents()
QgsProject.instance().addMapLayer(layer)

print(f'テストレイヤ作成: {layer.featureCount()} フィーチャ')
print()

feedback = QgsProcessingFeedback()
context = QgsProcessingContext()

# ---- テスト1: HTML出力 ----
print('=== テスト1: OnlineMapLinkerHTML ===')
try:
    algo = OnlineMapLinkerHTML()
    algo.initAlgorithm({})
    params = {
        'point_layer': layer,
        'online_map': 2,  # Open Street Map
        'name_field': 'name',
        'sort_field': None,
        'html_path': '/tmp/oml_test.html',
    }
    result = algo.processAlgorithm(params, context, feedback)
    with open(result['OUTPUT'], encoding='utf-8') as f:
        html = f.read()
    assert '東京' in html, '東京が出力に含まれていない'
    assert '大阪' in html, '大阪が出力に含まれていない'
    assert 'meta charset' in html, 'charset宣言がない'
    assert 'openstreetmap.org' in html, 'OSMのURLがない'
    print('PASS: HTML出力、文字コード、URL確認OK')
except Exception as e:
    print(f'FAIL: {e}')

# ---- テスト2: CSV出力 ----
print()
print('=== テスト2: OnlineMapLinkerCSV ===')
try:
    algo = OnlineMapLinkerCSV()
    algo.initAlgorithm({})
    params = {
        'point_layer': layer,
        'online_map': 2,  # Open Street Map
        'sort_field': None,
        'csv_path': '/tmp/oml_test.csv',
    }
    result = algo.processAlgorithm(params, context, feedback)
    import csv
    with open(result['OUTPUT'], encoding='shift_jis') as f:
        rows = list(csv.reader(f))
    print(f'  行数: ヘッダ1 + フィーチャ{len(rows)-1}')
    assert len(rows) == 4, f'行数が期待値(4)と異なる: {len(rows)}'
    oml_col = [h for h in rows[0] if h.startswith('OML_')]
    assert oml_col, 'OMLフィールドがない'
    assert 'openstreetmap.org' in rows[1][rows[0].index(oml_col[0])], 'URLが不正'
    print(f'PASS: CSV出力、Shift_JIS、URLフィールド({oml_col[0]})確認OK')
except Exception as e:
    print(f'FAIL: {e}')

# ---- テスト3: Layer出力 ----
print()
print('=== テスト3: OnlineMapLinkerLayer ===')
try:
    algo = OnlineMapLinkerLayer()
    algo.initAlgorithm({})
    params = {
        'point_layer': layer,
        'online_map': 0,  # Google Maps
        'sort_field': None,
        'output_crs': QgsCoordinateReferenceSystem('EPSG:4326'),
        'layer_path': '/tmp/oml_test.gpkg',
    }
    result = algo.processAlgorithm(params, context, feedback)
    out = QgsVectorLayer('/tmp/oml_test.gpkg', 'check', 'ogr')
    assert out.isValid(), 'GeoPackageが無効'
    assert out.featureCount() == 3, f'フィーチャ数が期待値(3)と異なる: {out.featureCount()}'
    field_names = [f.name() for f in out.fields()]
    oml_col = [n for n in field_names if n.startswith('OML_')]
    assert oml_col, 'OMLフィールドがない'
    first = next(out.getFeatures())
    url = first[oml_col[0]]
    assert 'google.com/maps' in url, f'GoogleマップURLが不正: {url}'
    print(f'PASS: GeoPackage出力、フィーチャ数、URLフィールド({oml_col[0]})確認OK')
except Exception as e:
    print(f'FAIL: {e}')

# ---- テスト4: Multi（経路）出力 ----
print()
print('=== テスト4: OnlineMapLinkerMulti ===')
try:
    algo = OnlineMapLinkerMulti()
    algo.initAlgorithm({})
    params = {
        'point_layer': layer,
        'sort_field': None,
        'url_title': 'テストルート',
        'html_path': '/tmp/oml_multi_test.html',
    }
    result = algo.processAlgorithm(params, context, feedback)
    with open(result['OUTPUT'], encoding='utf-8') as f:
        html = f.read()
    assert 'google.co.jp/maps/dir' in html, '経路URLがない'
    assert 'テストルート' in html, 'タイトルがない'
    assert 'meta charset' in html, 'charset宣言がない'
    print('PASS: Multi経路HTML、URL、タイトル、charset確認OK')
except Exception as e:
    print(f'FAIL: {e}')

print()
print('=== テスト完了 ===')
app.exitQgis()

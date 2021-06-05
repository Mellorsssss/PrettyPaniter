from GraphicsItems.line_item import LineItem
from GraphicsItems.polygon_item import PolygonItem
from GraphicsItems.ellipse_item import EllipseItem
from GraphicsItems.curve_item import CurveItem
from GraphicsItems.compound_item import CompoundItem
from GraphicsItems.text_item import TextItem


class ItemFactory:
    '''
    使用简单工厂模式简化生成新item的操作
    '''

    def __init__(self):
        pass

    def get_item(self, item_id: str, item_type: str, p_list: list, algorithm: str = ''):
        if item_type == 'line':
            return LineItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'polygon':
            return PolygonItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'ellipse':
            return EllipseItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'curve':
            return CurveItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'composite':
            return CompoundItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'text':
            return TextItem(item_id)



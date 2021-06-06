from graphics_item.line_item import LineItem
from graphics_item.polygon_item import PolygonItem
from graphics_item.ellipse_item import EllipseItem
from graphics_item.curve_item import CurveItem
from graphics_item.compound_item import CompoundItem
from graphics_item.text_item import TextItem
from graphics_item.triangle_item import TriangleItem
from graphics_item.square_item import SquareItem
from graphics_item.circle_item import CircleItem


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
        elif item_type == 'square':
            return SquareItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'triangle':
            return TriangleItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'circle':
            return CircleItem(item_id, item_type, p_list, algorithm)


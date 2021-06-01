from GraphicsItems.LineItemModule import LineItem
from GraphicsItems.PolygonItemModule import PolygonItem
from GraphicsItems.EllipseItemModule import EllipseItem
from GraphicsItems.CurveItemModule import CurveItem


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


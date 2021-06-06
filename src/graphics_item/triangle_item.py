from graphics_item.polygon_item import PolygonItem
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsItem


class TriangleItem(PolygonItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(TriangleItem, self).__init__(item_id, 'triangle', p_list, algorithm, parent)

        # init the vertex of triangle
        ret = self.p_list
        left_bottom = self.p_list[0]
        self.p_list.append([left_bottom[0]+100, left_bottom[1]])
        self.p_list.append([left_bottom[0]+50, left_bottom[1] + 50])

        self.fill = False
        self.fill_color = QColor(255, 255, 255)
        self.is_finish = True

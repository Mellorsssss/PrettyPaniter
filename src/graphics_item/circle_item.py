from graphics_item.ellipse_item import EllipseItem
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsItem


class CircleItem(EllipseItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        # init the vertex of triangle
        self.p_list = p_list
        left_bottom = self.p_list[0]
        self.p_list.append([left_bottom[0]+100, left_bottom[1]+100])

        super(CircleItem, self).__init__(item_id, 'circle', p_list, algorithm, parent)

        self.fill = False
        self.fill_color = QColor(255, 255, 255)
        self.is_finish = True

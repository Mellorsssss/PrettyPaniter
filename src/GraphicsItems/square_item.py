from GraphicsItems.polygon_item import PolygonItem
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsItem


class SquareItem(PolygonItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(SquareItem, self).__init__(item_id, 'square', p_list, algorithm, parent)

        # init the vertex of Square
        left_bottom = self.p_list[0]
        self.p_list.append([left_bottom[0]+100, left_bottom[1]])
        self.p_list.append([left_bottom[0]+100, left_bottom[1] + 100])
        self.p_list.append([left_bottom[0], left_bottom[1]+100])

        self.fill = False
        self.fill_color = QColor(255, 255, 255)
        self.is_finish = True

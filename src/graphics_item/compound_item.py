from typing import Optional
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from graphics_item.pp_item import PPItem
from algorithms import my_algorithms as alg


class CompoundItem(PPItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(CompoundItem, self).__init__(item_id, 'composite', None, None, parent)
        self.itemList = []

    def appendItem(self, item):
        # if item is not subclass of PPItem, then do not append them
        if not issubclass(type(item), PPItem):
            return

        self.itemList.append(item)
        item.unableSelect()
        return self  # for chain call

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        for item in self.itemList:
            item.paint(painter, option, widget)

        if self.selected:
            self.drawBoundingBox(painter)

    def boundingRect(self) -> QRectF:
        # iterate all the boundingRect of the items
        # get the boundingRect of all the rect
        assert len(self.itemList) >= 1
        cur_rect = QRectF(self.itemList[0].boundingRect())

        for item in self.itemList:

            com_rect = QRectF(item.boundingRect())
            p1_x = min(cur_rect.x(), com_rect.x())
            p1_y = min(cur_rect.y(), com_rect.y())
            p2_x = max(cur_rect.x() + cur_rect.width(), com_rect.x() + com_rect.width())
            p2_y = max(cur_rect.y() + cur_rect.height(), com_rect.y() + com_rect.height())

            cur_rect = QRectF(p1_x, p1_y, p2_x - p1_x, p2_y - p1_y)

        return cur_rect

    def clone(self):
        cloned_object = CompoundItem(self.id, 'composite', None, None)
        cloned_object.itemList = [item.clone() for item in self.itemList]  # deep copy every item in itemlist
        return cloned_object

    def __find_nearest_control_point(self, x, y, max_dis=30):
        pass

    def set_control_point(self, x, y):
        self.position = [x, y]

    def update_control_point(self, x, y):
        if self.position is None:
            return
        for item in self.itemList:
            item.translate(x-self.position[0], y - self.position[1])

        self.position = [x, y]

    def release_control_point(self):
        pass

    def translate(self, dx, dy):
        for item in self.itemList:
            item.translate(dx, dy)

    def rotate(self, xc, yc, r):
        for item in self.itemList:
            item.rotate(xc, yc, r)

    def scale(self, xc, yc, s):
        for item in self.itemList:
            item.scale(xc, yc, s)

    def dump_as_dict(self):
        pass

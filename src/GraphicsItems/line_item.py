from typing import Optional
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter, QColor
from algorithms import cg_algorithms as alg
from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from GraphicsItems.pp_item import PPItem
import copy


class LineItem(PPItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(LineItem, self).__init__(item_id, 'line', p_list, algorithm, parent)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(self.color)
        item_pixels = alg.draw_line(self.p_list, self.algorithm)
        for p in item_pixels:
            painter.drawPoint(*p)
        if not self.is_finish or self.selected:
            painter.setPen(QColor(0, 0, 0))
            for p in self.p_list:  # 绘制控制点
                painter.drawRect(p[0] - 4, p[1] - 4, 8, 8)
        if self.selected:
            self.drawBoundingBox(painter)

    def boundingRect(self) -> QRectF:
        x0, y0 = self.p_list[0]
        x1, y1 = self.p_list[1]
        x = min(x0, x1)
        y = min(y0, y1)
        w = max(x0, x1) - x
        h = max(y0, y1) - y
        return QRectF(x - 1, y - 1, w + 2, h + 2)

    def clone(self):
        cloned_obj = LineItem(self.id, self.item_type, copy.deepcopy(self.p_list), self.algorithm)
        cloned_obj.setFinish(True)\
            .setColor(self.color)
        return cloned_obj
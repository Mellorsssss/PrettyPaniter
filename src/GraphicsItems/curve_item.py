import copy
from typing import Optional

from PyQt5.QtCore import QRectF,Qt
from PyQt5.QtGui import QPainter, QColor, QPen
from algorithms import my_algorithms as alg
from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from GraphicsItems.pp_item import PPItem


class CurveItem(PPItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(CurveItem, self).__init__(item_id, 'curve', p_list, algorithm, parent)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(self.color)
        item_pixels = None
        if self.algorithm != 'B-spline' or len(self.p_list) >= 4:  # 需要注意三次b样条曲线需要至少四个控制点
            item_pixels = alg.draw_curve(self.p_list, self.algorithm)
        if item_pixels is not None:
            for p in item_pixels:
                painter.drawPoint(*p)
        if not self.is_finish or self.selected:
            painter.setPen(QColor(0, 0, 0))
            for p in self.p_list:  # 绘制控制点
                painter.drawRect(p[0] - 4, p[1] - 4, 8, 8)

            pen = QPen(Qt.DashLine)
            pen.setColor(Qt.blue)
            pen.setCapStyle(Qt.FlatCap)
            pen.setDashPattern((3, 3))
            painter.setPen(pen)

            for index in range(len(self.p_list) - 1):
                painter.drawLine(self.p_list[index][0], self.p_list[index][1], self.p_list[index + 1][0],
                                 self.p_list[index + 1][1])
        if self.selected:
            self.drawBoundingBox(painter)

    def boundingRect(self) -> QRectF:
        x0, y0 = self.p_list[0]
        x, y, w, h = x0, y0, x0, y0
        for (X, Y) in self.p_list:
            x = min(x, X)
            y = min(y, Y)
            w = max(w, X)
            h = max(h, Y)
        w -= x
        h -= y
        return QRectF(x - 1, y - 1, w + 2, h + 2)

    def clone(self):
        cloned_obj =  CurveItem(self.id, self.item_type, copy.deepcopy(self.p_list), self.algorithm)
        cloned_obj.setFinish(True) \
            .setColor(self.color)
        return cloned_obj
import copy
from typing import Optional
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter, QColor
from algorithms import cg_algorithms as alg
from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from GraphicsItems.PPItemModule import PPItem


class EllipseItem(PPItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(EllipseItem, self).__init__(item_id, 'ellipse', p_list, algorithm, parent)
        self.paint_list = copy.deepcopy(self.p_list)

    def setPaintList(self):
        x1, y1 = self.p_list[0]
        x2, y2 = self.p_list[1]
        self.paint_list[0] = [min(x1, x2), max(y1, y2)]
        self.paint_list[1] = [max(x1, x2), min(y1, y2)]

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(self.color)
        item_pixels = alg.draw_ellipse(self.paint_list)
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
        return QRectF(x0 - 1, y1 - 1, x1 - x0 + 2, y0 - y1 + 2)

    def update_control_point(self, x, y):
        super().update_control_point(x, y)
        self.setPaintList()

    def clone(self):
        return EllipseItem(self.id, self.item_type, copy.deepcopy(self.p_list), self.algorithm)

    def translate(self, dx, dy):
        self.p_list = alg.translate(self.p_list, dx, dy)
        self.setPaintList()

    def rotate(self, xc, yc, r):
        pass

    def scale(self, xc, yc, s):
        self.p_list = alg.scale(self.p_list, xc, yc, s)

    def scale(self, xc, yc, s):
        self.p_list = alg.scale(self.p_list, xc, yc, s)
        self.setPaintList()
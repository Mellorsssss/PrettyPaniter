from typing import Optional
from GraphicsItems.pp_item import PPItem
from algorithms import cg_algorithms as alg
from PyQt5.QtCore import QRectF,Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QGraphicsItem, QWidget, QStyleOptionGraphicsItem
import copy

class PolygonItem(PPItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(PolygonItem, self).__init__(item_id, 'polygon', p_list, algorithm, parent)
        self.fill = False
        self.fill_color = QColor(255, 255, 255)

    def set_fill(self, fill_color):
        self.fill = True
        self.fill_color = fill_color
        return self

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(self.color)
        item_pixels = alg.draw_polygon(self.p_list, self.algorithm, self.is_finish)
        for p in item_pixels:
            painter.drawPoint(*p)

        # 只要是一个合格的多边形，就进行填充
        if self.fill and len(self.p_list) >= 3:
            pen = QPen(Qt.SolidLine)
            pen.setColor(self.fill_color)
            painter.setPen(pen)
            points = alg.polygon_fill_line(self.p_list, 1000)
            for p in points:
                [start, end] = p
                painter.drawLine(start[0], start[1], end[0], end[1])
                # painter.drawPoint(*p)

        if self.selected:
            pen = QPen(Qt.DashLine)
            pen.setColor(Qt.blue)
            pen.setCapStyle(Qt.FlatCap)
            pen.setDashPattern((3, 3))
            painter.setPen(pen)
            painter.drawRect(self.boundingRect())

            ### 测试多边形填充

        if not self.is_finish or self.selected:
            painter.setPen(QColor(0, 0, 0))
            for p in self.p_list:  # 绘制控制点
                painter.drawRect(p[0] - 4, p[1] - 4, 8, 8)

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

    def clone(self):  # 重载以实现填充的复制
        cloned_obj = PolygonItem(self.id, self.item_type, copy.deepcopy(self.p_list), self.algorithm)
        if self.fill:
            cloned_obj.set_fill(self.fill_color)
        cloned_obj.setFinish(True) \
            .setColor(self.color)
        return cloned_obj

    def dump_as_dict(self):  # 记录是否填充的信息
        tem = super(PolygonItem, self).dump_as_dict()
        tem["fill"] = self.fill
        tem["fill_color"] = [self.fill_color.red(), self.fill_color.green(), self.fill_color.blue()]
        return tem

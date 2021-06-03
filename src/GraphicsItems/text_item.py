from typing import Optional

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QFont, QPainter, QPen, QColor
from PyQt5.QtWidgets import QGraphicsTextItem, QStyleOptionGraphicsItem, QWidget, QGraphicsItem
from GraphicsItems.pp_item import PPItem


class TextItem(QGraphicsTextItem):
    def __init__(self, _id):
        super(TextItem, self).__init__()
        self.id = _id
        self.item_type = 'text'

        self.selected = False  # 当前的图元是否被选中
        self.color = QColor(0, 0, 0)  # 图元颜色
        self.setZValue(int(self.id))  # 设置深度，用于控制图元的上下图层关系
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.is_finish = False

        self.moving_control_point = -1  # 当前正在移动的控制点索引
        self.position = None
        self.setFont(QFont("华文琥珀", 20))
        self.setPlainText("this is a simple demo")

    def setFinish(self, flag):
        self.is_finish = flag
        return self

    def setSelect(self, flag: bool):
        '''
        设置selected位并同时设置当前的图元是否可以移动

        :param flag: 为True如果当前被选中
        :return: None
        '''
        self.selected = flag
        return self

    def setColor(self, color: QColor):
        self.color = color
        return self

    def setId(self, id):
        self.id = id
        return self

    def get_center(self):
        # get the center of the current item
        boundingRect = self.boundingRect()
        bottom_left_point = boundingRect.bottomLeft()
        top_right_point = boundingRect.topRight()
        return (bottom_left_point.x() + top_right_point.x()) / 2, (bottom_left_point.y() + top_right_point.y()) / 2

    def drawBoundingBox(self, painter):
        pen = QPen(Qt.DashLine)
        pen.setColor(Qt.blue)
        pen.setCapStyle(Qt.FlatCap)
        pen.setDashPattern((3, 3))
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())


    # traverse all the control points and find the one which is near to (x, y)
    # max_dis is the min distance between the control points and (x,y)
    def __find_nearest_control_point(self, x, y, max_dis=30):
        pass

    def set_control_point(self, x, y):
        pass

    def update_control_point(self, x, y):
        pass

    def release_control_point(self):
        pass

    def dump_as_dict(self):
        '''
        将当前的 item 转换为一个 dict 用于可持续化
        :return: 转换之后的
        '''
        params_dict = {'id': self.id, 'type': self.item_type, 'p_list': None, 'algorithm': None,
                       'color': [self.color.red(), self.color.green(), self.color.blue()], 'zvalue': self.zValue()}
        return params_dict

    def clone(self):
        return TextItem(self.id)

    # translation on item
    def translate(self, dx, dy):
        pass

    def rotate(self, xc, yc, r):
        pass

    def scale(self, xc, yc, s):
        pass

    # drawing functions of item
    def start_draw(self):
        pass

    def end_draw(self):
        pass



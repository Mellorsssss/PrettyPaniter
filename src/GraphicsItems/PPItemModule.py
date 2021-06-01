from typing import Optional
from PyQt5.QtCore import QRectF,Qt
from PyQt5.QtGui import QColor, QPen, QPainter
from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from algorithms import cg_algorithms as alg


class PPItem(QGraphicsItem):
    """
    PPItem is the base item of all the graphics items
    """

    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        """

        :param item_id: 图元ID
        :param item_type: 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        :param p_list: 图元参数
        :param algorithm: 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        :param parent:
        """
        super().__init__(parent)
        self.id = item_id  # 图元ID
        self.item_type = item_type  # 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        self.p_list = p_list  # 图元参数
        self.algorithm = algorithm  # 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        self.selected = False  # 当前的图元是否被选中
        self.color = QColor(0, 0, 0)  # 图元颜色
        self.setZValue(int(item_id))  # 设置深度，用于控制图元的上下图层关系
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.is_finish = False

        self.moving_control_point = -1  # 当前正在移动的控制点索引
        self.position = None

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

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(self.color)
        pass

    def boundingRect(self) -> QRectF:
        pass

    # traverse all the control points and find the one which is near to (x, y)
    # max_dis is the min distance between the control points and (x,y)
    def find_nearest_control_point(self, x, y, max_dis=30):
        def get_dis(x, y, p):
            return (x - p[0]) ** 2 + (y - p[1]) ** 2

        min_dis = 1000000
        min_p_index = -1
        for index, p in enumerate(self.p_list):
            cur_dis = get_dis(x, y, p)
            if cur_dis <= max_dis ** 2:
                min_dis = min(min_dis, cur_dis)
                min_p_index = index

        return min_p_index

    def set_control_point(self, x, y):
        nearest_control_point_index = self.find_nearest_control_point(x, y)
        self.position = [x, y]
        if nearest_control_point_index != -1:
            self.moving_control_point = nearest_control_point_index
            return True
        else:
            return False

    def update_control_point(self, x, y):
        if self.moving_control_point != -1:
            try:
                self.p_list[self.moving_control_point] = [x, y]
            except IndexError:
                print("control index out of range!")
        else:
            if self.position is None:
                return
            alg.translate(self.p_list, x - self.position[0], y - self.position[1])
            self.position = [x, y]

    def release_control_point(self):
        if self.moving_control_point != -1:
            self.moving_control_point = -1

    def dump_as_dict(self):
        '''
        将当前的 item 转换为一个 dict 用于可持续化
        :return: 转换之后的
        '''
        params_dict = {'id': self.id, 'type': self.item_type, 'p_list': self.p_list, 'algorithm': self.algorithm,
                       'color': [self.color.red(), self.color.green(), self.color.blue()], 'zvalue': self.zValue()}
        return params_dict

    def clone(self):
        '''
        prototype pattern, abstract clone method
        sub class will override this method
        :return: cloned object
        '''
        pass

    def translate(self, dx, dy):
        self.p_list = alg.translate(self.p_list, dx, dy)


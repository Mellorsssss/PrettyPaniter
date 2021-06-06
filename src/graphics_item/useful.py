from typing import Optional
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QPen, QPainter
from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from algorithms import my_algorithms as alg
import copy

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

    def unableSelect(self):
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)

    def reverseSelect(self):
        self.selected = not self.selected

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
    def __find_nearest_control_point(self, x, y, max_dis=30):
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
        nearest_control_point_index = self.__find_nearest_control_point(x, y)
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

    # translation on item
    def translate(self, dx, dy):
        self.p_list = alg.translate(self.p_list, dx, dy)

    def rotate(self, xc, yc, r):
        self.p_list = alg.rotate(self.p_list, xc, yc, r)

    def scale(self, xc, yc, s):
        self.p_list = alg.scale(self.p_list, xc, yc, s)

    # drawing functions of item
    def start_draw(self):
        pass

    def end_draw(self):
        pass


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


class EllipseItem(PPItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(EllipseItem, self).__init__(item_id, 'ellipse', p_list, algorithm, parent)
        self.paint_list = copy.deepcopy(self.p_list)
        self.setPaintList()

    def setPaintList(self):
        x1, y1 = self.p_list[0]
        x2, y2 = self.p_list[1]
        self.paint_list[0] = [min(x1, x2), max(y1, y2)]
        self.paint_list[1] = [max(x1, x2), min(y1, y2)]

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(self.color)
        item_pixels = alg.draw_ellipse(self.paint_list)
        self.setPaintList()
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
        left = min(x0, x1)
        top = min(y0, y1)
        return QRectF(left, top, abs(x1 - x0) + 2, abs(y1 - y0) + 2)

    def update_control_point(self, x, y):
        super().update_control_point(x, y)
        self.setPaintList()

    def clone(self):
        cloned_obj =  EllipseItem(self.id, self.item_type, copy.deepcopy(self.p_list), self.algorithm)
        cloned_obj.setFinish(True) \
            .setColor(self.color)
        return cloned_obj

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


class ItemFactory:
    '''
    使用简单工厂模式简化生成新item的操作
    '''

    def __init__(self):
        pass

    def get_item(self, item_id: str, item_type: str, p_list: list, algorithm: str = ''):
        if item_type == 'line':
            return LineItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'polygon':
            return PolygonItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'ellipse':
            return EllipseItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'curve':
            return CurveItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'composite':
            return CompoundItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'text':
            return TextItem(item_id)
        elif item_type == 'square':
            return SquareItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'triangle':
            return TriangleItem(item_id, item_type, p_list, algorithm)
        elif item_type == 'circle':
            return CircleItem(item_id, item_type, p_list, algorithm)


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

class TextItem(QGraphicsTextItem):
    def __init__(self, _id, _text: str = "this is demo"):
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
        self.setFont(QFont("Consolas", 20))
        self.setPlainText(_text)

    def set_text(self, _text):
        self.setPlainText(_text)

    def setFinish(self, flag):
        self.is_finish = flag
        return self

    def setSelect(self, flag: bool):
        self.selected = flag
        return self

    def unableSelect(self):
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)

    def reverseSelect(self):
        self.selected = not self.selected

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

    def __find_nearest_control_point(self, x, y, max_dis=30):
        pass

    def set_control_point(self, x, y):
        self.position = [x, y]

    def update_control_point(self, x, y):
        if self.position is None:
            return
        self.translate(x-self.position[0], y-self.position[1])

        self.position = [x, y]

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
        cloned_obj = TextItem(self.id)
        cloned_obj.setX(self.x())
        cloned_obj.setY(self.y())
        return cloned_obj

    # translation on item
    def translate(self, dx, dy):
        self.setX(self.x() + dx)
        self.setY(self.y() + dy)

    def rotate(self, xc, yc, r):
        pass

    def scale(self, xc, yc, s):
        pass

    # drawing functions of item
    def start_draw(self):
        pass

    def end_draw(self):
        pass

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
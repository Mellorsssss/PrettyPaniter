#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import math
import json
import os
import copy
import cg_algorithms as alg
from typing import Optional
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    qApp,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsItem,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QStyleOptionGraphicsItem,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QColorDialog,
    QFileDialog,
    QCheckBox
)
from PyQt5.QtGui import QPainter, QMouseEvent, QColor, QKeyEvent, QWheelEvent, QIntValidator, QDoubleValidator, QPen, \
    QIcon
from PyQt5.QtCore import QRectF, Qt

import numpy as np
from PIL import Image


class MyCanvas(QGraphicsView):
    """
    画布窗体类，继承自QGraphicsView，采用QGraphicsView、QGraphicsScene、QGraphicsItem的绘图框架
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.setFocusPolicy(Qt.StrongFocus)
        self.queue_pos = 0
        self.main_window = None
        self.item_dict = {}
        self.selected_id = ''

        self.status = 'mouse'
        self.clip_rect = None
        self.temp_algorithm = ''
        self.temp_id = ''
        self.temp_item = None
        self.selected_item = None
        self.pen_color = QColor(0, 0, 0)

        self.item_factory = ItemFactory()  # 图元工厂类，用于生成各种类型的图元
        self.clipboard = None  # 剪切板，记录已经被复制的元素

        self.verticalScrollBar().setVisible(False)
        self.horizontalScrollBar().setVisible(False)

        self.max_z = 999

    ###### 保存、删除等功能 ######
    def remove_item(self, id):
        self.clear_selection()
        self.scene().removeItem(self.item_dict[id])
        del self.item_dict[id]
        self.updateScene([self.sceneRect()])

    def remove_all(self):
        self.status_changed()
        self.clear_selection()
        for key, item in self.item_dict.items():
            self.scene().removeItem(self.item_dict[key])
        self.item_dict.clear()
        self.updateScene([self.sceneRect()])

    def has_select_item(self):
        '''
        当前是否选中了图元
        :return:  如果当前选中了图元，返回真
        '''
        return self.selected_id != '' and self.selected_item is not None

    def save_all(self, save_path):
        '''
        保存当前画布中的item信息为json文件
        :param save_path: 保存的文件名
        '''
        self.status_changed()
        dump_dict = {}
        for index, item in self.item_dict.items():
            ans = item.dump_as_dict()
            dump_dict[index] = ans

        with open(save_path, 'w', encoding='UTF=8') as save_file:
            json.dump(dump_dict, save_file)
        save_file.close()

    def save_all_as_bmp(self, save_path):
        weight, height = self.size().width(), self.size().height()
        print(weight, height)
        canvas = np.zeros([height, weight, 3], np.uint8)
        canvas.fill(255)
        self.status_changed()
        dump_dict = {}

        def axis_valid(_x, _y):
            return 0 <= _x < weight and 0 <= _y < height

        for index, item in self.item_dict.items():
            ans = item.dump_as_dict()
            dump_dict[index] = ans
        for item in dump_dict.values():
            item_type = item["type"]
            p_list = item["p_list"]
            algorithm = item["algorithm"]
            color = item["color"]
            if item_type == 'line':
                pixels = alg.draw_line(p_list, algorithm)
                for x, y in pixels:
                    if not axis_valid(x, y):
                        continue
                    canvas[y, x] = color
            elif item_type == 'polygon':
                pixels = alg.draw_polygon(p_list, algorithm)
                for x, y in pixels:
                    if not axis_valid(x, y):
                        continue
                    canvas[y, x] = color
                if item["fill"]:
                    fill_pixels = alg.polygon_fill(p_list, 1000)
                    fill_color = item["fill_color"]
                    for x, y in fill_pixels:
                        if not axis_valid(x, y):
                            continue
                        canvas[y, x] = fill_color
            elif item_type == 'ellipse':
                pixels = alg.draw_ellipse(p_list)
                for x, y in pixels:
                    if not axis_valid(x, y):
                        continue
                    canvas[y, x] = color
            elif item_type == 'curve':
                if algorithm == 'B-spline' and len(p_list) < 4:
                    continue
                pixels = alg.draw_curve(p_list, algorithm)
                for x, y in pixels:
                    if not axis_valid(x, y):
                        continue
                    canvas[y, x] = color
        Image.fromarray(canvas).save(save_path, 'bmp')

    def load_json(self, json_file_path):
        '''
        加载保存的画图json文件
        :param json_file_path: 画图json文件地址
        :return:
        '''
        # 读取画布上图元json文件
        try:
            with open(json_file_path, 'r', encoding='UTF-8') as fin:
                load_dict = json.load(fin)
            fin.close()
        except:
            print("load failure")
            return

        if load_dict is None:
            return

        # 删除当前所有图元，并且清除所有选中
        self.status_changed()
        self.remove_all()
        self.clear_selection()
        max_key = -1
        try:
            for key, item in load_dict.items():
                max_key = max(max_key, int(key))
                new_item = self.item_factory.get_item(key, item['type'], item['p_list'], item['algorithm'])
                new_item.setFinish(True)
                new_item.setZValue(item['zvalue'])
                new_item.setColor(QColor(item['color'][0], item['color'][1], item['color'][2]))
                if new_item.item_type == 'polygon':
                    if item["fill"]:
                        new_item.set_fill(QColor(item['fill_color'][0], item['fill_color'][1], item['fill_color'][2]))
                self.scene().addItem(new_item)
                self.item_dict[key] = new_item
        except:
            print("load failure")
            return
        self.main_window.set_id(max_key + 1)
        self.temp_id = self.main_window.get_id()

    def copy(self):
        if self.selected_item is None:
            return

        if self.selected_item.item_type == 'curve' and len(self.selected_item.p_list) > 10:
            print("控制点数大于10的曲线不进行复制")
            msg_box = QMessageBox(QMessageBox.Warning, '复制错误', '为了软件的稳定运行，暂不支持复制超过10个控制点的曲线')
            msg_box.exec_()
            return

        self.clipboard = self.selected_item.clone()
        self.clipboard.set_id(self.main_window.get_id())
        # self.item_factory.get_item(self.main_window.get_id(),
        #                                         self.selected_item.item_type,
        #                                         copy.deepcopy(self.selected_item.p_list),
        #                                         self.selected_item.algorithm)
        # self.clipboard = copy.deepcopy(self.selected_item)
        self.clipboard.setColor(self.selected_item.color)  # 颜色也要拷贝
        self.clipboard.setFinish(True)  # 设置当前的图元为已经绘制完成

    def paste(self, dx=10, dy=10):
        '''
        粘贴当前剪切板图元到scene中
        :param dx: 偏移原先图元的x偏移量
        :param dy: 偏移原先图元的y偏移量
        '''

        # 防止过多的粘贴导致程序崩溃
        if len(self.items()) >= 30:
            msg_box = QMessageBox(QMessageBox.Warning, '复制错误', '图元超过30个，暂不支持继续粘贴')
            msg_box.exec_()
            return
        if self.clipboard is None:
            return
        alg.translate(self.clipboard.p_list, 30, 30)
        if self.clipboard.item_type == 'ellipse':
            self.clipboard.setPaintList()
        self.item_dict[self.clipboard.id] = self.clipboard
        self.scene().addItem(self.clipboard)
        self.scene().update()
        self.updateScene([self.sceneRect()])

        # 更新clipboard为一个新的图元
        temp_color = self.clipboard.color
        self.clipboard = self.clipboard.clone()
        self.clipboard.set_id(self.main_window.get_id())
        # self.clipboard = self.item_factory.get_item(self.main_window.get_id(),
        #                                             self.clipboard.item_type,
        #                                             copy.deepcopy(self.clipboard.p_list),
        #                                             self.clipboard.algorithm)
        self.clipboard.setColor(temp_color)  # 颜色也要拷贝
        self.clipboard.setFinish(True)

    def add_clip_rect(self, x_min, y_min, x_max, y_max):
        if x_min > x_max:
            x_min, x_max = x_max, x_min
        if y_min > y_max:
            y_min, y_max = y_max, y_min

        if self.clip_rect is not None:
            print("clip rect should be None.")
            self.remove_clip_rect()

        self.clip_rect = ClipRectangle(x_min, y_min, x_max - x_min, y_max - y_min)
        self.scene().addItem(self.clip_rect)
        self.updateScene([self.sceneRect()])

    def remove_clip_rect(self):
        if self.clip_rect is None:
            print("clip rectangle is None.")
            return

        self.scene().removeItem(self.clip_rect)
        self.clip_rect = None
        print("remove the clip rect")

    def update_clip_rect(self, x_min, y_min, x_max, y_max):
        if self.clip_rect is None:
            print("clip rect should not be None.")
            return

        if x_min > x_max:
            x_min, x_max = x_max, x_min
        if y_min > y_max:
            y_min, y_max = y_max, y_min

        self.clip_rect.set_x(x_min). \
            set_y(y_min). \
            set_w(x_max - x_min). \
            set_h(y_max - y_min)

        self.updateScene([self.sceneRect()])

    ###### setter & getter ######
    def setPenColor(self, color: QColor):
        self.pen_color = color

    def get_selected_item_type(self):
        if self.selected_item is None:
            return None
        else:
            return self.selected_item.item_type

    def get_status(self):
        return self.status

    ###### 图元的绘制方法 ######
    def start_draw_line(self, algorithm, item_id):
        self.setStatus('line')
        self.temp_algorithm = algorithm
        self.temp_id = item_id

    def start_draw_polygon(self, algorithm, item_id):
        self.setStatus('polygon')
        self.temp_algorithm = algorithm
        self.temp_id = item_id
        self.queue_pos = -1

    def start_draw_ellipse(self, item_id):
        self.setStatus('ellipse')
        self.temp_algorithm = None
        self.temp_id = item_id

    def start_draw_curve(self, algorithm, item_id):
        self.setStatus('curve')
        self.temp_algorithm = algorithm
        self.temp_id = item_id
        self.queue_pos = -1

    def translate(self, dx, dy):
        if not self.has_select_item():
            return

        self.selected_item.p_list = alg.translate(self.selected_item.p_list, dx, dy)
        if self.selected_item.item_type == 'ellipse':  # 椭圆需要额外设置绘制的点
            self.selected_item.setPaintList()
        self.updateScene([self.sceneRect()])

    def rotate(self, xc, yc, r):
        if not self.has_select_item():
            return

        if self.selected_item.item_type == 'ellipse':  # 椭圆不进行旋转
            return
        self.selected_item.p_list = alg.rotate(self.selected_item.p_list, xc, yc, r)
        self.updateScene([self.sceneRect()])

    def scale(self, xc, yc, s):
        if not self.has_select_item():
            return

        self.item_dict[self.selected_id].p_list = alg.scale(self.selected_item.p_list, xc, yc, s)
        if self.selected_item.item_type == 'ellipse':
            self.selected_item.setPaintList()
        self.updateScene([self.sceneRect()])

    def clip(self, x_min, y_min, x_max, y_max, algorithm):
        if not self.has_select_item():
            return

        cliped_p_list = alg.clip(self.selected_item.p_list, x_min, y_min, x_max,
                                 y_max, algorithm)
        if cliped_p_list is None:
            self.remove_item(self.selected_id)
            self.selected_id = ''
            return True
        else:
            self.selected_item.p_list = cliped_p_list
            self.updateScene([self.sceneRect()])
            return False

    def fill_polygon(self, fill_color):
        if self.selected_item is None or self.selected_item.item_type != 'polygon':
            return
        self.selected_item.set_fill(fill_color)
        self.updateScene([self.sceneRect()])

    def finish_draw_polygon(self):
        if self.status != 'polygon' or self.temp_item is None:
            # raise Exception("item is not polygon or is None!")
            return
        else:
            if len(self.temp_item.p_list) < 3: # 不是一个多边形
                self.scene().removeItem(self.temp_item)
            else:
                self.temp_item.setFinish(True)
                self.item_dict[self.temp_id] = self.temp_item
            self.update()
            self.queue_pos = -1
            self.finish_draw()

    def finish_draw_curve(self):
        if self.status != 'curve' or self.temp_item is None:
            return
        else:
            if self.temp_item.algorithm == 'B-spline' and len(self.temp_item.p_list) <4:
                self.scene().removeItem(self.temp_item)
            else:
                self.temp_item.setFinish(True)
                self.item_dict[self.temp_id] = self.temp_item
            self.update()
            self.queue_pos = -1
            self.finish_draw()

    def finish_draw(self):
        self.temp_id = self.main_window.get_id()
        self.temp_item = None

    ###### 系统状态机维护 ######
    def status_changed(self):
        '''
        canvas的状态转移方程
        :return:
        '''
        if self.status == 'polygon':
            self.finish_draw_polygon()
            self.updateScene([self.sceneRect()])
        elif self.status == 'curve':
            self.finish_draw_curve()
            self.updateScene([self.sceneRect()])

    def clear_selection(self):
        if self.has_select_item():
            try:
                self.selected_item.setSelect(False)
                self.selected_id = ''
                self.selected_item = None
            except KeyError:
                print("KeyError: {0} is not in the item dict.".format(self.selected_id))

    def selection_changed(self, selected):
        if selected == '':
            return
        if selected == self.selected_id:
            return
        self.main_window.statusBar().showMessage('图元选择： %s' % selected)
        if self.has_select_item():
            try:
                self.selected_item.setSelect(False)
                self.selected_item.setZValue(int(self.selected_id))
                self.selected_item.update()
            except KeyError:
                print("KeyError: {0} is not in the item dict.".format(self.selected_id))
            self.selected_item = None

        self.selected_id = selected
        try:
            self.selected_item = self.item_dict[selected]
        except KeyError:
            print("KeyError: {0} is not in the item dict.".format(selected))
            return
        self.item_dict[selected].setSelect(True)
        self.item_dict[selected].setZValue(self.max_z + 1)  # 将当前的图元放在最顶层
        self.max_z += 1
        self.item_dict[selected].update()  # 更新bounding box的绘制
        self.setStatus('mouse')
        self.updateScene([self.sceneRect()])

    def setStatus(self, status):
        '''
        将状态的转移进行封装
        :param status: 新的状态（str）
        :return:
        '''
        self.status_changed()
        self.status = status

    ###### 鼠标与键盘事件处理 ######
    def __mouse_press_handle(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            if self.status == 'polygon' and self.temp_item is not None:
                self.finish_draw_polygon()
                self.updateScene([self.sceneRect()])
            elif self.status == 'curve' and self.temp_item is not None:
                self.finish_draw_curve()
                self.updateScene([self.sceneRect()])
            return

        if event.button() != Qt.LeftButton:
            return

        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())

        if self.status == 'line':
            p_list = [[x, y], [x, y]]
            self.temp_item = self.item_factory.get_item(self.temp_id, self.status, p_list, self.temp_algorithm)
            self.temp_item.setColor(self.pen_color)
            self.scene().addItem(self.temp_item)
        elif self.status == 'polygon':
            if self.queue_pos == -1:  # 当前为一个新的多边形
                p_list = [[x, y]]
                self.queue_pos += 1
                self.temp_item = self.item_factory.get_item(self.temp_id, self.status, p_list, self.temp_algorithm)
                self.temp_item.setColor(self.pen_color)
                self.scene().addItem(self.temp_item)
            else:
                if self.temp_item is None:
                    raise Exception("the temp item shouldn't be None!")
                self.queue_pos += 1
                self.temp_item.p_list.append([x, y])
        elif self.status == 'ellipse':
            p_list = [[x, y], [x, y]]
            self.temp_item = self.item_factory.get_item(self.temp_id, self.status, p_list, self.temp_algorithm)
            self.temp_item.setColor(self.pen_color)
            self.scene().addItem(self.temp_item)
        elif self.status == 'curve':
            if self.queue_pos == -1:
                self.queue_pos = 0
                p_list = [[x, y]]
                self.temp_item = self.item_factory.get_item(self.temp_id, self.status, p_list, self.temp_algorithm)
                self.temp_item.setColor(self.pen_color)
                self.scene().addItem(self.temp_item)
            else:
                if self.temp_item is None:
                    raise Exception("the temp item shouldn't be None!")
                self.queue_pos += 1
                self.temp_item.p_list.append([x, y])
        self.updateScene([self.sceneRect()])
        if self.status == 'mouse':
            selected_item = self.itemAt(x, y)
            if selected_item is not None:
                self.selection_changed(selected_item.id)
                if not self.selected_item.set_control_point(x, y):
                    self.setCursor(Qt.SizeAllCursor)
                else:
                    self.setCursor(Qt.PointingHandCursor)
            else:
                self.clear_selection()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.__mouse_press_handle(event)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.__mouse_press_handle(event)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not (event.buttons() & Qt.LeftButton):
            return

        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())

        if self.status != 'mouse' and self.temp_item is None:
            return
        if self.status == 'line':
            self.temp_item.p_list[1] = [x, y]  # 不断改变终点
        elif self.status == 'polygon':
            if len(self.temp_item.p_list) == 1:  # 第一个节点不允许改变位置
                self.queue_pos += 1
                self.temp_item.p_list.append([x, y])
            else:
                self.temp_item.p_list[self.queue_pos] = [x, y]  # 不断改变终点
        elif self.status == 'ellipse':
            self.temp_item.p_list[1] = [x, y]
            self.temp_item.setPaintList()
        elif self.status == 'curve':
            if len(self.temp_item.p_list) == 1:  # 第一个节点不允许改变位置
                self.queue_pos += 1
                self.temp_item.p_list.append([x, y])
            else:
                self.temp_item.p_list[self.queue_pos] = [x, y]  # 不断改变终点

        if self.status == 'mouse':
            if self.selected_item is not None:
                self.selected_item.update_control_point(x, y)

        self.updateScene([self.sceneRect()])
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.unsetCursor()
        if event.button() != Qt.LeftButton:
            return
        if self.status != 'mouse' and self.temp_item is None:
            return
        if self.status == 'line':
            self.item_dict[self.temp_id] = self.temp_item
            self.temp_item.setFinish(True)
            self.update()
            self.finish_draw()

        elif self.status == 'polygon':
            def get_distance(point1, point2):
                return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

            if self.queue_pos > 1 and get_distance(self.temp_item.p_list[0],
                                                   self.temp_item.p_list[self.queue_pos]) < 15:
                # self.temp_item.p_list[self.queue_pos] = self.temp_item.p_list[0]
                self.temp_item.p_list.pop(-1)
                self.temp_item.setFinish(True)
                self.temp_item.update()
                self.finish_draw_polygon()
            # else:
            #     self.temp_item.p_list += [self.temp_item.p_list[self.queue_pos]]
            #     self.queue_pos += 1

        elif self.status == 'ellipse':
            self.item_dict[self.temp_id] = self.temp_item
            self.temp_item.setFinish(True)
            self.update()
            self.finish_draw()

        # elif self.status == 'curve':
        #     pass

        if self.status == 'mouse':
            if self.selected_item is not None:
                self.selected_item.release_control_point()
        self.updateScene([self.sceneRect()])
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Space:
            if self.status == 'polygon' and self.temp_item is not None:
                self.finish_draw_polygon()
            elif self.status == 'curve' and self.temp_item is not None:
                self.finish_draw_curve()

        # 使用键盘变换当前选中的图元
        if self.has_select_item():
            if event.key() == Qt.Key_W:
                self.translate(0, -5)
            elif event.key() == Qt.Key_A:
                self.translate(-5, 0)
            elif event.key() == Qt.Key_S:
                self.translate(0, 5)
            elif event.key() == Qt.Key_D:
                self.translate(5, 0)

            elif event.key() == Qt.Key_Q:
                center_x, center_y = self.selected_item.get_center()
                self.scale(int(center_x), int(center_y), 1.1)
            elif event.key() == Qt.Key_E:
                center_x, center_y = self.selected_item.get_center()
                self.scale(int(center_x), int(center_y), 0.9)

            elif event.key() == Qt.Key_R:
                center_x, center_y = self.selected_item.get_center()
                self.rotate(int(center_x), int(center_y), 10)

        # ctrl 组合键处理
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_D and self.has_select_item():
                self.remove_item(self.selected_id)
            elif event.key() == Qt.Key_C:
                self.copy()
            elif event.key() == Qt.Key_V:
                self.paste()

        self.updateScene([self.sceneRect()])
        super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        return


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


class MyItem(QGraphicsItem):
    """
    自定义图元类，继承自QGraphicsItem
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

    def setSelect(self, flag: bool):
        '''
        设置selected位并同时设置当前的图元是否可以移动

        :param flag: 为True如果当前被选中
        :return: None
        '''
        self.selected = flag

    def setColor(self, color: QColor):
        self.color = color

    def set_id(self, id):
        self.id = id

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

    # 遍历所有的控制点，返回最近的一个控制点，并且距离小于阈值
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
        item_generator = ItemFactory()
        return item_generator.get_item(self.id, self.item_type, copy.deepcopy(self.p_list), self.algorithm)


class LineItem(MyItem):
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


class PolygonItem(MyItem):
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        super(PolygonItem, self).__init__(item_id, 'polygon', p_list, algorithm, parent)
        self.fill = False
        self.fill_color = QColor(255, 255, 255)

    def set_fill(self, fill_color):
        self.fill = True
        self.fill_color = fill_color

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
        tem = super(PolygonItem, self).clone()
        if self.fill:
            tem.set_fill(self.fill_color)
        return tem

    def dump_as_dict(self):  # 记录是否填充的信息
        tem = super(PolygonItem, self).dump_as_dict()
        tem["fill"] = self.fill
        tem["fill_color"] = [self.fill_color.red(), self.fill_color.green(), self.fill_color.blue()]
        return tem


class EllipseItem(MyItem):
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


class CurveItem(MyItem):
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


class ClipRectangle(QGraphicsItem):
    def __init__(self, x=0, y=0, w=100, h=100):
        super(ClipRectangle, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def set_x(self, x):
        self.x = x
        return self

    def set_y(self, y):
        self.y = y
        return self

    def set_w(self, w):
        self.w = w
        return self

    def set_h(self, h):
        self.h = h
        return self

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        pos = self.mapToScene(self.x, self.y)
        pen = QPen(Qt.DashLine)
        pen.setColor(Qt.red)
        pen.setCapStyle(Qt.FlatCap)
        pen.setDashPattern((3, 3))
        painter.setPen(pen)
        painter.drawRect(QRectF(pos.x(), pos.y(), self.w, self.h))

    def boundingRect(self):
        return QRectF(self.x, self.y, self.w, self.h)


class TranslateWidget(QWidget):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas
        self.init_ui()
        self.init_operation()

    def init_ui(self):
        # self.setGeometry(200, 300, 500, 500)
        self.setWindowTitle('平移操作')
        self.init_componets()
        self.init_layout()
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)

    def init_componets(self):
        self.dx_label = QLabel('x轴方向偏移量', self)
        self.dy_label = QLabel('y轴方向偏移量', self)

        self.dx_input_linedit = QLineEdit('1', self)
        self.dy_input_linedit = QLineEdit('1', self)
        self.input_check = QIntValidator()
        self.input_check.setRange(-500, 500)
        self.dx_input_linedit.setValidator(self.input_check)
        self.dy_input_linedit.setValidator(self.input_check)

        self.yes_pushbuuton = QPushButton('确定', self)
        self.no_pushbuuton = QPushButton('关闭', self)

    def init_layout(self):
        self.label_v_layout = QVBoxLayout()
        self.line_v_layout = QVBoxLayout()
        self.label_line_h_layout = QHBoxLayout()
        self.button_h_layout = QHBoxLayout()
        self.ui_v_layout = QVBoxLayout()

        self.label_v_layout.addWidget(self.dx_label)
        self.label_v_layout.addWidget(self.dy_label)
        self.line_v_layout.addWidget(self.dx_input_linedit)
        self.line_v_layout.addWidget(self.dy_input_linedit)
        self.label_line_h_layout.addLayout(self.label_v_layout)
        self.label_line_h_layout.addLayout(self.line_v_layout)
        self.button_h_layout.addWidget(self.yes_pushbuuton)
        self.button_h_layout.addWidget(self.no_pushbuuton)
        self.ui_v_layout.addLayout(self.label_line_h_layout)
        self.ui_v_layout.addLayout(self.button_h_layout)
        self.setLayout(self.ui_v_layout)

    def init_operation(self):
        def finish_input():
            try:
                x, y = int(self.dx_input_linedit.text()), int(self.dy_input_linedit.text())
            except ValueError:
                print("Null is not valid input!")
                info = QMessageBox(self)
                info.setText("Null is not valid input!")
                info.setWindowTitle("警告！")
                info.exec_()
            else:
                self.canvas.translate(x, -y)

        self.yes_pushbuuton.clicked.connect(finish_input)
        self.no_pushbuuton.clicked.connect(self.close)


class RotateWidget(QWidget):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas
        self.init_ui()
        self.init_operation()

    def init_ui(self):
        # self.setGeometry(200, 300, 500, 500)
        self.setWindowTitle('旋转操作')
        self.init_componets()
        self.init_layout()
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)

    def init_componets(self):
        self.x_label = QLabel('旋转中心x坐标', self)
        self.y_label = QLabel('旋转中心y坐标', self)
        self.angle_label = QLabel('旋转角度', self)

        self.x_input_linedit = QLineEdit('0', self)
        self.y_input_linedit = QLineEdit('0', self)
        self.xy_input_check = QIntValidator()
        self.xy_input_check.setRange(-500, 500)
        self.x_input_linedit.setValidator(self.xy_input_check)
        self.y_input_linedit.setValidator(self.xy_input_check)

        self.angle_input_linedit = QLineEdit('10', self)
        self.angle_input_check = QIntValidator()
        self.angle_input_check.setRange(-360, 360)
        self.angle_input_linedit.setValidator(self.angle_input_check)

        self.yes_pushbuuton = QPushButton('确定', self)
        self.no_pushbuuton = QPushButton('关闭', self)

    def init_layout(self):
        self.label_v_layout = QVBoxLayout()
        self.line_v_layout = QVBoxLayout()
        self.label_line_h_layout = QHBoxLayout()
        self.button_h_layout = QHBoxLayout()
        self.ui_v_layout = QVBoxLayout()

        self.label_v_layout.addWidget(self.x_label)
        self.label_v_layout.addWidget(self.y_label)
        self.label_v_layout.addWidget(self.angle_label)
        self.line_v_layout.addWidget(self.x_input_linedit)
        self.line_v_layout.addWidget(self.y_input_linedit)
        self.line_v_layout.addWidget(self.angle_input_linedit)
        self.label_line_h_layout.addLayout(self.label_v_layout)
        self.label_line_h_layout.addLayout(self.line_v_layout)
        self.button_h_layout.addWidget(self.yes_pushbuuton)
        self.button_h_layout.addWidget(self.no_pushbuuton)
        self.ui_v_layout.addLayout(self.label_line_h_layout)
        self.ui_v_layout.addLayout(self.button_h_layout)
        self.setLayout(self.ui_v_layout)

    def init_operation(self):
        def finish_input():
            try:
                x, y, r = int(self.x_input_linedit.text()), int(self.y_input_linedit.text()), int(
                    self.angle_input_linedit.text())
            except ValueError:
                print("Null is not valid input!")
                info = QMessageBox(self)
                info.setText("Null is not valid input!")
                info.setWindowTitle("警告！")
                info.exec_()
            else:
                self.canvas.rotate(x, y, r)

        self.yes_pushbuuton.clicked.connect(finish_input)
        self.no_pushbuuton.clicked.connect(self.close)


class ScaleWidget(QWidget):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas
        self.init_ui()
        self.init_operation()

    def init_ui(self):
        # self.setGeometry(200, 300, 500, 500)
        self.setWindowTitle('缩放操作')
        self.init_componets()
        self.init_layout()
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)

    def init_componets(self):
        self.x_label = QLabel('缩放中心x坐标', self)
        self.y_label = QLabel('缩放中心y坐标', self)
        self.angle_label = QLabel('缩放比例', self)

        self.x_input_linedit = QLineEdit('0', self)
        self.y_input_linedit = QLineEdit('0', self)
        self.xy_input_check = QIntValidator()
        self.xy_input_check.setRange(-500, 500)
        self.x_input_linedit.setValidator(self.xy_input_check)
        self.y_input_linedit.setValidator(self.xy_input_check)

        self.scale_input_linedit = QLineEdit('1.5', self)
        self.scale_input_check = QDoubleValidator()
        self.scale_input_check.setNotation(QDoubleValidator.StandardNotation)
        self.scale_input_check.setRange(0, 5)  # TODO: fix the bug of bound
        self.scale_input_check.setDecimals(1)
        self.scale_input_linedit.setValidator(self.scale_input_check)

        self.yes_pushbuuton = QPushButton('确定', self)
        self.no_pushbuuton = QPushButton('关闭', self)

    def init_layout(self):
        self.label_v_layout = QVBoxLayout()
        self.line_v_layout = QVBoxLayout()
        self.label_line_h_layout = QHBoxLayout()
        self.button_h_layout = QHBoxLayout()
        self.ui_v_layout = QVBoxLayout()

        self.label_v_layout.addWidget(self.x_label)
        self.label_v_layout.addWidget(self.y_label)
        self.label_v_layout.addWidget(self.angle_label)
        self.line_v_layout.addWidget(self.x_input_linedit)
        self.line_v_layout.addWidget(self.y_input_linedit)
        self.line_v_layout.addWidget(self.scale_input_linedit)
        self.label_line_h_layout.addLayout(self.label_v_layout)
        self.label_line_h_layout.addLayout(self.line_v_layout)
        self.button_h_layout.addWidget(self.yes_pushbuuton)
        self.button_h_layout.addWidget(self.no_pushbuuton)
        self.ui_v_layout.addLayout(self.label_line_h_layout)
        self.ui_v_layout.addLayout(self.button_h_layout)
        self.setLayout(self.ui_v_layout)

    def init_operation(self):
        def finish_input():
            try:
                x, y, s = int(self.x_input_linedit.text()), int(self.y_input_linedit.text()), float(
                    self.scale_input_linedit.text())
            except ValueError:
                print("Null is not valid input!")
                info = QMessageBox(self)
                info.setText("Null is not valid input!")
                info.setWindowTitle("警告！")
                info.exec_()
            else:
                self.canvas.scale(x, y, s)

        self.yes_pushbuuton.clicked.connect(finish_input)
        self.no_pushbuuton.clicked.connect(self.close)


class ClipWindow(QWidget):
    def __init__(self, canvas, algorithm):
        super().__init__()
        self.canvas = canvas
        self.algorithm = algorithm
        self.init_ui()
        self.init_operation()

    def init_ui(self):
        self.setWindowTitle('裁剪操作 ' + self.algorithm)
        self.init_componets()
        self.init_layout()
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)

    def init_componets(self):
        self.xmin_label = QLabel('裁剪矩形左上角x坐标', self)
        self.ymax_label = QLabel('裁剪矩形左上角y坐标', self)
        self.xmax_label = QLabel('裁剪矩形右下角x坐标', self)
        self.ymin_label = QLabel('裁剪矩形右下角y坐标', self)

        self.xmin_input_linedit = QLineEdit('0', self)
        self.ymin_input_linedit = QLineEdit('0', self)
        self.xmax_input_linedit = QLineEdit('400', self)
        self.ymax_input_linedit = QLineEdit('400', self)
        self.xy_input_check = QIntValidator()
        self.xy_input_check.setRange(-500, 500)
        self.xmin_input_linedit.setValidator(self.xy_input_check)
        self.ymin_input_linedit.setValidator(self.xy_input_check)
        self.xmax_input_linedit.setValidator(self.xy_input_check)
        self.ymax_input_linedit.setValidator(self.xy_input_check)

        self.yes_pushbuuton = QPushButton('确定', self)
        self.no_pushbuuton = QPushButton('关闭', self)
        self.show_area = QCheckBox('显示裁剪窗口', self)

    def init_layout(self):
        self.label_v_layout = QVBoxLayout()
        self.line_v_layout = QVBoxLayout()
        self.label_line_h_layout = QHBoxLayout()
        self.button_h_layout = QHBoxLayout()
        self.ui_v_layout = QVBoxLayout()

        self.label_v_layout.addWidget(self.xmin_label)
        self.label_v_layout.addWidget(self.ymax_label)
        self.label_v_layout.addWidget(self.xmax_label)
        self.label_v_layout.addWidget(self.ymin_label)
        self.line_v_layout.addWidget(self.xmin_input_linedit)
        self.line_v_layout.addWidget(self.ymin_input_linedit)
        self.line_v_layout.addWidget(self.xmax_input_linedit)
        self.line_v_layout.addWidget(self.ymax_input_linedit)

        self.label_line_h_layout.addLayout(self.label_v_layout)
        self.label_line_h_layout.addLayout(self.line_v_layout)
        self.button_h_layout.addWidget(self.yes_pushbuuton)
        self.button_h_layout.addWidget(self.no_pushbuuton)
        self.button_h_layout.addWidget(self.show_area)
        self.ui_v_layout.addLayout(self.label_line_h_layout)
        self.ui_v_layout.addLayout(self.button_h_layout)
        self.setLayout(self.ui_v_layout)

    def init_operation(self):
        def get_axis():
            try:
                x, y, z, w = 0, 0, 0, 0
                if self.xmin_input_linedit.text() != '':
                    x = int(self.xmin_input_linedit.text())

                if self.ymax_input_linedit.text() != '':
                    y = int(self.ymax_input_linedit.text())

                if self.xmax_input_linedit.text() != '':
                    z = int(self.xmax_input_linedit.text())

                if self.ymin_input_linedit.text() != '':
                    w = int(self.ymin_input_linedit.text())
                # x, y, z, w = int(self.xmin_input_linedit.text()), int(self.ymax_input_linedit.text()), \
                #                      int(self.xmax_input_linedit.text()), int(self.ymin_input_linedit.text())
            except ValueError:
                print("Null is not valid input!")
                info = QMessageBox(self)
                info.setText("Null is not valid input!")
                info.setWindowTitle("警告！")
                info.exec_()
            else:
                return x, y, z, w

        def finish_input():
            try:
                xmin, ymax, xmax, ymin = get_axis()
            except TypeError:
                print("get axis failure")
                return
            if self.canvas.clip(xmin, ymax, xmax, ymin, self.algorithm):
                self.close()
                self.canvas.remove_clip_rect()

        def show_state_change():
            if self.show_area.checkState() == Qt.Checked:
                try:
                    x_min, y_min, x_max, y_max = get_axis()
                except TypeError:
                    print("get axis failure")
                    return
                self.canvas.add_clip_rect(x_min, y_min, x_max, y_max)
            else:
                self.canvas.remove_clip_rect()

        def update_clip_rect():
            if self.show_area.checkState() == Qt.Checked:
                try:
                    x_min, y_min, x_max, y_max = get_axis()
                except TypeError:
                    print("get axis failure")
                    return
                self.canvas.update_clip_rect(x_min, y_min, x_max, y_max)

        self.xmax_input_linedit.textEdited.connect(update_clip_rect)
        self.ymax_input_linedit.textEdited.connect(update_clip_rect)
        self.xmin_input_linedit.textEdited.connect(update_clip_rect)
        self.ymin_input_linedit.textEdited.connect(update_clip_rect)
        self.yes_pushbuuton.clicked.connect(finish_input)
        self.no_pushbuuton.clicked.connect(self.close)
        self.show_area.stateChanged.connect(show_state_change)

    def closeEvent(self, a0) -> None:
        self.canvas.remove_clip_rect()


class ResetCanvasWidget(QWidget):
    def __init__(self, canvas=None, min_weight=400, min_height=400):
        super().__init__()
        self.canvas = canvas
        self.min_weight = min_weight
        self.min_height = min_height
        self.init_ui()
        self.init_operation()

    def init_ui(self):
        # self.setGeometry(200, 300, 500, 500)
        self.setWindowTitle('重置画布')
        self.init_componets()
        self.init_layout()
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)

    def init_componets(self):
        self.weight_label = QLabel('画布宽', self)
        self.height_label = QLabel('画布高', self)

        self.weight_linedit = QLineEdit('400', self)
        self.height_linedit = QLineEdit('400', self)
        self.input_check = QIntValidator()
        self.input_check.setRange(400, 800)
        self.weight_linedit.setValidator(self.input_check)
        self.height_linedit.setValidator(self.input_check)

        self.yes_pushbuuton = QPushButton('确定', self)
        self.no_pushbuuton = QPushButton('关闭', self)

    def init_layout(self):
        self.label_v_layout = QVBoxLayout()
        self.line_v_layout = QVBoxLayout()
        self.label_line_h_layout = QHBoxLayout()
        self.button_h_layout = QHBoxLayout()
        self.ui_v_layout = QVBoxLayout()

        self.label_v_layout.addWidget(self.weight_label)
        self.label_v_layout.addWidget(self.height_label)
        self.line_v_layout.addWidget(self.weight_linedit)
        self.line_v_layout.addWidget(self.height_linedit)
        self.label_line_h_layout.addLayout(self.label_v_layout)
        self.label_line_h_layout.addLayout(self.line_v_layout)
        self.button_h_layout.addWidget(self.yes_pushbuuton)
        self.button_h_layout.addWidget(self.no_pushbuuton)
        self.ui_v_layout.addLayout(self.label_line_h_layout)
        self.ui_v_layout.addLayout(self.button_h_layout)
        self.setLayout(self.ui_v_layout)

    def init_operation(self):
        def finish_input():
            try:
                w, h = int(self.weight_linedit.text()), int(self.height_linedit.text())
            except ValueError:
                print("Null is not valid input!")
                info = QMessageBox(self)
                info.setText("Null is not valid input!")
                info.setWindowTitle("警告！")
                info.exec_()
            else:
                if w < self.min_weight:
                    info = QMessageBox(self)
                    info.setText("宽度不可以少于{}".format(self.min_weight))
                    info.setWindowTitle("警告！")
                    info.exec_()
                    return
                if h < self.min_height:
                    info = QMessageBox(self)
                    info.setText("高度不可以少于{}".format(self.min_weight))
                    info.setWindowTitle("警告！")
                    info.exec_()
                    return
                self.canvas.remove_all()
                self.canvas.setFixedSize(w, h)
                self.close()

        self.yes_pushbuuton.clicked.connect(finish_input)
        self.no_pushbuuton.clicked.connect(self.close)


class MainWindow(QMainWindow):
    """
    主窗口类
    """

    def __init__(self):
        super().__init__()
        self.item_cnt = 0
        self.init_items()
        self.init_menu()
        self.init_layout()

    def init_items(self):
        # 使用QListWidget来记录已有的图元，并用于选择图元。注：这是图元选择的简单实现方法，更好的实现是在画布中直接用鼠标选择图元
        self.item_list = []

        # 使用QGraphicsView作为画布
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 800, 800)
        self.canvas_widget = MyCanvas(self.scene, self)
        self.canvas_widget.setFixedSize(800, 800)
        self.canvas_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.canvas_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.canvas_widget.main_window = self
        # 图元操作的对话框
        self.translate_window = None
        self.rotate_window = None
        self.scale_window = None
        self.clip_window = None

    def init_menu(self):
        # 设置菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        set_pen_act = file_menu.addAction('设置画笔')
        reset_canvas_act = file_menu.addAction('重置画布')
        save_canvas_as_bmp_act = file_menu.addAction('保存画布为bmp')
        save_canvas_act = file_menu.addAction('保存画布为json')
        load_canvas_act = file_menu.addAction('从json加载画布')
        exit_act = file_menu.addAction('退出')
        draw_menu = menubar.addMenu('绘制')
        line_menu = draw_menu.addMenu('线段')
        line_naive_act = line_menu.addAction('Naive')
        line_naive_act.setIcon(QIcon('../other_folder/other_folder/line.ico'))
        line_dda_act = line_menu.addAction('DDA')
        line_dda_act.setIcon(QIcon('../other_folder/other_folder/line.ico'))
        line_bresenham_act = line_menu.addAction('Bresenham')
        line_bresenham_act.setIcon(QIcon('../other_folder/other_folder/line.ico'))
        polygon_menu = draw_menu.addMenu('多边形')
        polygon_dda_act = polygon_menu.addAction('DDA')
        polygon_bresenham_act = polygon_menu.addAction('Bresenham')
        ellipse_act = draw_menu.addAction('椭圆')
        curve_menu = draw_menu.addMenu('曲线')
        curve_bezier_act = curve_menu.addAction('Bezier')
        curve_bezier_act.setIcon(QIcon('../other_folder/other_folder/curve.ico'))
        curve_b_spline_act = curve_menu.addAction('B-spline')
        curve_b_spline_act.setIcon(QIcon('../other_folder/other_folder/curve.ico'))
        edit_menu = menubar.addMenu('编辑')
        translate_act = edit_menu.addAction('平移')
        translate_act.setIcon(QIcon('../other_folder/other_folder/translate.ico'))
        rotate_act = edit_menu.addAction('旋转')
        rotate_act.setIcon(QIcon('../other_folder/other_folder/rotate.ico'))
        scale_act = edit_menu.addAction('缩放')
        scale_act.setIcon(QIcon('../other_folder/other_folder/scale.ico'))
        clip_menu = edit_menu.addMenu('裁剪')
        clip_cohen_sutherland_act = clip_menu.addAction('Cohen-Sutherland')
        clip_cohen_sutherland_act.setIcon(QIcon('../other_folder/other_folder/clip.ico'))
        clip_liang_barsky_act = clip_menu.addAction('Liang-Barsky')
        clip_liang_barsky_act.setIcon(QIcon('../other_folder/other_folder/clip.ico'))
        fill_act = edit_menu.addAction('填充多边形')
        fill_act.setIcon(QIcon('../other_folder/other_folder/paint_bucket.png'))

        # 连接信号和槽函数
        reset_canvas_act.triggered.connect(lambda: self.reset_canvas_action())
        set_pen_act.triggered.connect(lambda: self.pen_color_action())
        save_canvas_act.triggered.connect(lambda: self.save_canvas_as_json_action())
        save_canvas_as_bmp_act.triggered.connect(lambda: self.save_canvas_as_bmp_action())
        load_canvas_act.triggered.connect(lambda: self.load_canvas_from_json_action())

        exit_act.triggered.connect(qApp.quit)

        line_naive_act.triggered.connect(lambda: self.line_action('Naive'))
        line_bresenham_act.triggered.connect(lambda: self.line_action('Bresenham'))
        line_dda_act.triggered.connect(lambda: self.line_action('DDA'))
        polygon_dda_act.triggered.connect(lambda: self.polygon_action('DDA'))
        polygon_dda_act.setIcon(QIcon('../other_folder/other_folder/polygon.ico'))
        polygon_bresenham_act.triggered.connect(lambda: self.polygon_action('Bresenham'))
        polygon_bresenham_act.setIcon(QIcon('../other_folder/other_folder/polygon.ico'))
        ellipse_act.triggered.connect(lambda: self.ellipse_action())
        ellipse_act.setIcon(QIcon('../other_folder/other_folder/ellipse.ico'))
        curve_bezier_act.triggered.connect(lambda: self.curve_action('Bezier'))
        curve_b_spline_act.triggered.connect(lambda: self.curve_action('B-spline'))

        translate_act.triggered.connect(lambda: self.translate_action())
        rotate_act.triggered.connect(lambda: self.rotate_action())
        scale_act.triggered.connect(lambda: self.scale_action())
        clip_cohen_sutherland_act.triggered.connect(lambda: self.clip_action('Cohen-Sutherland'))
        clip_liang_barsky_act.triggered.connect(lambda: self.clip_action('Liang-Barsky'))
        fill_act.triggered.connect(lambda: self.fill_action())

        tool_bar = self.addToolBar('选择')
        mouse_selection_act = tool_bar.addAction('选择')
        mouse_selection_act.triggered.connect(lambda: self.mouse_selection())
        mouse_selection_act.setIcon(QIcon('../other_folder/other_folder/mouse.ico'))

        tool_bar = self.addToolBar('颜色')
        tool_bar.addAction(set_pen_act)
        set_pen_act.setIcon(QIcon('../other_folder/other_folder/pen.ico'))

        tool_bar = self.addToolBar('线段')
        tool_bar.addAction(line_dda_act)

        tool_bar = self.addToolBar('多边形')
        tool_bar.addAction(polygon_bresenham_act)

        tool_bar = self.addToolBar('椭圆')
        tool_bar.addAction(ellipse_act)

        tool_bar = self.addToolBar('Bezier曲线')
        tool_bar.addAction(curve_bezier_act)

        tool_bar = self.addToolBar('B-spline曲线')
        tool_bar.addAction(curve_b_spline_act)

        tool_bar = self.addToolBar('平移')
        tool_bar.addAction(translate_act)

        tool_bar = self.addToolBar('旋转')
        tool_bar.addAction(rotate_act)

        tool_bar = self.addToolBar('缩放')
        tool_bar.addAction(scale_act)

        tool_bar = self.addToolBar('裁剪')
        tool_bar.addAction(clip_liang_barsky_act)

        tool_bar = self.addToolBar('多边形填充')
        tool_bar.addAction(fill_act)

    def init_layout(self):
        # 设置主窗口的布局
        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.addWidget(self.canvas_widget)
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.hbox_layout)
        self.setCentralWidget(self.central_widget)
        self.statusBar().showMessage('空闲')
        self.resize(600, 600)
        self.setWindowTitle('Pretty Printer')
        self.setWindowIcon(QIcon('../other_folder/other_folder/cover.png'))

    def get_id(self):
        # 该方法已经被弃用
        _id = str(self.item_cnt)
        self.item_cnt += 1
        return _id

    def set_id(self, cnt):
        self.item_cnt = cnt

    def pen_color_action(self):
        color = QColorDialog.getColor()
        self.canvas_widget.setPenColor(color)

    def reset_canvas_action(self):
        self.reset_canvas_window = ResetCanvasWidget(self.canvas_widget)
        self.reset_canvas_window.show()
        # self.canvas_widget.remove_all()

    def save_canvas_as_json_action(self):
        save_path, file_type = QFileDialog.getSaveFileName(self, '保存', os.getcwd(), 'Json Files(*.json)')

        if save_path != '':
            self.canvas_widget.save_all(save_path + '.json')

    def load_canvas_from_json_action(self):
        load_path, file_type = QFileDialog.getOpenFileName(self, '打开已保存画布', os.getcwd(), 'Json Files(*.json)')

        if load_path != '':
            self.canvas_widget.load_json(load_path)

    def save_canvas_as_bmp_action(self):
        save_path, file_type = QFileDialog.getSaveFileName(self, '保存', os.getcwd(), 'Bmp Files(*.bmp)')

        if save_path != '':
            self.canvas_widget.save_all_as_bmp(save_path + '.bmp')

    def line_action(self, algorithm='Naive'):
        self.canvas_widget.start_draw_line(algorithm, self.get_id())
        self.statusBar().showMessage(algorithm + '算法绘制线段')
        self.canvas_widget.clear_selection()

    def polygon_action(self, algorithm='DDA'):
        self.canvas_widget.start_draw_polygon(algorithm, self.get_id())
        self.statusBar().showMessage(algorithm + '算法绘制多边形')
        self.canvas_widget.clear_selection()

    def ellipse_action(self):
        self.canvas_widget.start_draw_ellipse(self.get_id())
        self.statusBar().showMessage('中点画圆分绘制椭圆')
        self.canvas_widget.clear_selection()

    def curve_action(self, algorithm):
        '''
        绘制曲线的action
        :param algorithm: 使用的算法
        :return:
        '''
        self.canvas_widget.start_draw_curve(algorithm, self.get_id())
        self.statusBar().showMessage(algorithm + '算法绘制曲线')
        self.canvas_widget.clear_selection()

    def translate_action(self):
        '''
        平移GUI窗口
        '''
        if self.canvas_widget.get_selected_item_type() is None:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '当前没有图元被选中！')
            msg_box.exec_()
        else:
            self.translate_window = TranslateWidget(self.canvas_widget)
            self.translate_window.show()

    def rotate_action(self):
        if self.canvas_widget.get_selected_item_type() is None:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '当前没有图元被选中！')
            msg_box.exec_()
        else:
            self.rotate_window = RotateWidget(self.canvas_widget)
            self.rotate_window.show()

    def scale_action(self):
        if self.canvas_widget.get_selected_item_type() is None:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '当前没有图元被选中！')
            msg_box.exec_()
        else:
            self.scale_window = ScaleWidget(self.canvas_widget)
            self.scale_window.show()

    def clip_action(self, algorithm):
        if self.canvas_widget.get_selected_item_type() is None:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '当前没有图元被选中！')
            msg_box.exec_()
        elif self.canvas_widget.get_selected_item_type() != 'line':
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '只能对线段进行剪裁！')
            msg_box.exec_()
        elif algorithm not in ['Liang-Barsky', 'Cohen-Sutherland']:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '使用了不正确的算法！')
            msg_box.exec_()
        else:
            self.scale_window = ClipWindow(self.canvas_widget, algorithm)
            self.scale_window.show()

    def fill_action(self):
        if self.canvas_widget.get_selected_item_type() is None:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '当前没有图元被选中！')
            msg_box.exec_()
        elif self.canvas_widget.get_selected_item_type() != 'polygon':
            msg_box = QMessageBox(QMessageBox.Warning, '警告', '只能填充多边形！')
            msg_box.exec_()
        else:
            color = QColorDialog.getColor(title="选择填充颜色")
            self.canvas_widget.fill_polygon(color)

    def mouse_selection(self):
        self.canvas_widget.setStatus('mouse')

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.save_canvas_as_json_action()
            elif event.key() == Qt.Key_O:
                self.load_canvas_from_json_action()

        super(MainWindow, self).keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
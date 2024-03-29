#!/usr/bin/env python
# -*- coding:utf-8 -*-
import copy
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import math
import json
from algorithms import my_algorithms as alg
from graphics_item.item_factory import ItemFactory
from graphics_item.pp_item import PPItem
from utils.command import Command
from utils.copy_command import CopyCommand
from utils.paste_command import PasteCommand
from utils.undo_command import UndoCommand
from utils.add_command import AddCommand
from utils.remove_command import RemoveCommand
from utils.command_history import CommandHistory
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


class PPCanvas(QGraphicsView):
    """
    PPCanvas is the main gui of the Pretty Painter

    Attributes:
        queue_pos: points have drawn
        item_dict: all the items on the canvas
        selected_id: selected item's id
        selected_item: current selected item
        id_count: number of items

        status: status of the canvas
        clip_rect: # to remove

        pen_color: color to paint

        item_factory: factory of items
        clipboard: item to paste
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.setFocusPolicy(Qt.StrongFocus)

        '''
        context of the canvas
        '''
        self.queue_pos = 0 # TODO: move this to concrete item
        self.item_dict = {}
        self.selected_id = ''
        self.id_count = 0

        self.status = 'mouse'
        self.clip_rect = None
        self.temp_algorithm = ''
        self.temp_id = ''
        self.temp_item = None
        self.selected_item = None # current selected item
        self.pen_color = QColor(0, 0, 0)

        self.item_factory:ItemFactory = ItemFactory()  # 图元工厂类，用于生成各种类型的图元
        self.clipboard = None  # 剪切板，记录已经被复制的元素

        self.__clipboard = None
        self.history: CommandHistory = CommandHistory()

        self.verticalScrollBar().setVisible(False)
        self.horizontalScrollBar().setVisible(False)

        self.max_z = 999

        # for mix items
        self.compound_items = set()

    def set_clipboard(self, item):
        self.__clipboard = item
        return self

    def get_clipboard(self) :
        return self.__clipboard

    def execute_command(self, command: Command):
        if command.execute():
            self.history.push_command(command)

    def undo_command(self):
        command: Command = self.history.pop_command()
        if command is None:
            return

        command.undo()

    def get_context(self):
        return copy.copy(self.item_dict) # quick way

    def set_context(self, context):
        self.remove_all()
        self.item_dict = context
        self.update_all()

    def get_id(self):
        ret: int = self.id_count
        self.id_count += 1
        return ret

    def set_id(self, _id):
        self.id_count = max(self.id_count, _id)

    def remove_item(self, id):
        self.reset_selection()
        self.scene().removeItem(self.item_dict[id])
        del self.item_dict[id]
        self.updateScene([self.sceneRect()])

    def add_temp_item(self):
        if self.temp_item is None:
            return
        self.scene().removeItem(self.temp_item)
        self.selected_item = self.temp_item
        command = AddCommand(self, self).set_id(self.temp_id)
        self.execute_command(command)
        self.selected_item = None

    def add_item(self, item, id: int = None):
        if self.item_dict.get(int(item.id)) is not None or id is None:
            print("duplicated id")
            item.setId(self.get_id())
        else:
            item.setId(id)
        self.add_item_aux(int(item.id), item)

    def add_item_aux(self, id, item):
        self.item_dict[id] = item
        item.setFinish(True)
        self.scene().addItem(item)
        self.scene().update()
        self.update()
        self.updateScene([self.sceneRect()])

    def add_text_item(self, _text:str = "this is demo"):
        self.setStatus('mouse')
        item = self.item_factory.get_item(self.get_id(), 'text', None)
        item.set_text(_text)
        self.selected_item = item

        command = AddCommand(self, self).set_id(item.id)
        self.execute_command(command)
        self.selected_item = None

    def reset_compound_items(self):
        self.reset_selection()

        for item in self.compound_items:
            item.setSelect(False)

        self.compound_items = set()

    def add_compound_items(self, item):
        self.compound_items.add(item)

    def add_compound_item(self):
        self.setStatus('mouse')
        if len(self.compound_items) == 0:
            return
        item = self.item_factory.get_item(self.get_id(), 'composite', None)
        for tem in self.compound_items:
            item.appendItem(tem)

        if len(item.itemList) ==0:
            return

        self.selected_item = item
        self.selected_item.setZValue(self.max_z + 1)  # 将当前的图元放在最顶层
        self.max_z += 1
        command = AddCommand(self, self).set_id(item.id)
        self.execute_command(command)
        self.selected_item = None

    def update_all(self):
        self.status_changed()
        for key, item in self.item_dict.items():
            self.scene().addItem(self.item_dict[key])
        self.updateScene([self.sceneRect()])
        self.scene().update()
        self.updateScene([self.sceneRect()])

    def remove_all(self):
        self.status_changed()
        self.reset_selection()
        cnt = 0
        for key, item in self.item_dict.items():
            self.scene().removeItem(item)
            cnt += 1
        print("remove " + str(cnt) + " items.")
        self.item_dict.clear()
        self.updateScene([self.sceneRect()])

    def has_select_item(self):
        '''
        当前是否选中了图元
        :return:  如果当前选中了图元，返回真
        '''
        return self.selected_id != '' and self.selected_item is not None

    def get_selection(self):
        ret = self.selected_item
        return self.selected_item

    def save_all(self, save_path):
        '''
        保存当前画布中的item信息为json文件
        :param save_path: 保存的文件名
        '''
        self.status_changed()
        dump_dict = {}
        for index, item in self.item_dict.items():
            ans = item.dump_as_dict()
            if ans is None:
                continue
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
        self.reset_selection()
        self.id_count = 0
        max_key = -1
        try:
            for key, item in load_dict.items():
                new_item = self.item_factory.get_item(key, item['type'], item['p_list'], item['algorithm'])
                new_item.setFinish(True)
                new_item.setZValue(item['zvalue'])
                new_item.setColor(QColor(item['color'][0], item['color'][1], item['color'][2]))
                new_item.setId(self.get_id())
                if new_item.item_type == 'polygon':
                    if item["fill"]:
                        new_item.set_fill(QColor(item['fill_color'][0], item['fill_color'][1], item['fill_color'][2]))
                # self.add_item_aux(key, new_item)
                self.add_item(new_item)
        except:
            print("load failure")
            return
        self.temp_id = self.get_id()

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

    def setPenColor(self, color: QColor):
        self.pen_color = color

    def get_selected_item_type(self):
        if self.selected_item is None:
            return None
        else:
            return self.selected_item.item_type

    def get_status(self):
        return self.status

    def start_draw(self, status, algorithm, item_id):
        self.setStatus(status)
        self.temp_algorithm = algorithm
        self.temp_id = item_id
        self.queue_pos = -1

    def translate(self, dx, dy):
        if not self.has_select_item():
            return

        self.selected_item.translate(dx, dy)
        self.updateScene([self.sceneRect()])

    def rotate(self, xc, yc, r):
        if not self.has_select_item():
            return

        self.selected_item.rotate(xc, yc, r)
        self.updateScene([self.sceneRect()])

    def scale(self, xc, yc, s):
        if not self.has_select_item():
            return

        self.selected_item.scale(xc, yc, s)
        self.updateScene([self.sceneRect()])

    def clip(self, x_min, y_min, x_max, y_max, algorithm):
        if not self.has_select_item():
            return
        # TODO: modify the interface
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
            return
        else:
            if len(self.temp_item.p_list) < 3: # 不是一个多边形
                self.scene().removeItem(self.temp_item)
            else:
                self.add_temp_item()
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
                self.add_temp_item()
            self.update()
            self.queue_pos = -1
            self.finish_draw()

    def finish_draw(self):
        self.temp_id = self.get_id()
        self.temp_item = None

    def remove_selection(self):
        if self.selected_item is None or self.selected_id == '':
            return

        self.remove_item(self.selected_id)

    def status_changed(self):
        '''
        canvas的状态转移
        :return:
        '''
        if self.status == 'polygon':
            self.finish_draw_polygon()
            self.updateScene([self.sceneRect()])
        elif self.status == 'curve':
            self.finish_draw_curve()
            self.updateScene([self.sceneRect()])

    def reset_selection(self):
        if self.has_select_item():
            try:
                self.selected_item.setSelect(False)
                self.selected_id = ''
                self.selected_item = None
            except KeyError:
                print("reset: KeyError: {0} is not in the item dict.".format(self.selected_id))
        else:
            self.selected_id = ''
            self.selected_item = None

    def selection_changed(self, selected):
        if selected == '':
            return
        if selected == self.selected_id:
            return

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
        elif self.status == 'triangle' or self.status == 'square' or self.status == 'circle':
            p_list = [[x, y]]
            self.temp_item = self.item_factory.get_item(self.temp_id, self.status, p_list, self.temp_algorithm)
            self.temp_item.setColor(self.pen_color)
            self.scene().addItem(self.temp_item)
            self.add_temp_item()
            self.finish_draw()
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
                self.reset_selection()
        elif self.status == 'compound':
            print("compound mode")
            selected_item = self.itemAt(x, y)
            if selected_item is not None:
                selected_item.setSelect(True)
                self.add_compound_items(selected_item)
                self.scene().update()
                self.updateScene([self.sceneRect()])
            else:
                self.reset_selection()

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
            self.add_temp_item()
            self.finish_draw()

        elif self.status == 'polygon':
            def get_distance(point1, point2):
                return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

            if self.queue_pos > 1 and get_distance(self.temp_item.p_list[0],
                                                   self.temp_item.p_list[self.queue_pos]) < 15:
                # self.temp_item.p_list[self.queue_pos] = self.temp_item.p_list[0]
                self.add_temp_item()
                self.temp_item.update()
                self.finish_draw_polygon()

        elif self.status == 'ellipse':
            self.add_temp_item()
            self.finish_draw()


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

        if event.key() == Qt.Key_Alt:
            self.reset_selection()
            self.setStatus('compound')  # TODO: may be exclude all other events?
            print("begin compound")
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
                command = RemoveCommand(self, self)
                self.execute_command(command)
            elif event.key() == Qt.Key_C:
                command = CopyCommand(self, self)
                self.execute_command(command)
            elif event.key() == Qt.Key_V:
                command = PasteCommand(self, self)
                self.execute_command(command)
            elif event.key() == Qt.Key_Z:
                print("undo")
                command = UndoCommand(self, self)
                self.execute_command(command)

        self.updateScene([self.sceneRect()])
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Alt:
            assert self.status == "compound"
            print("set compound")
            self.setStatus('mouse')
            self.add_compound_item()
            self.reset_compound_items()


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


class AddTextWidget(QWidget):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas

        # self.setGeometry(200, 300, 500, 500)
        self.setWindowTitle('添加文字')
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.input_label = QLabel('请输入文字', self)

        self.input_line_edit = QLineEdit('I love NJU.', self)

        self.yes_pushbuuton = QPushButton('确定', self)
        self.no_pushbuuton = QPushButton('关闭', self)

        self.label_v_layout = QVBoxLayout()
        self.line_v_layout = QVBoxLayout()
        self.label_line_h_layout = QHBoxLayout()
        self.button_h_layout = QHBoxLayout()
        self.ui_v_layout = QVBoxLayout()

        self.label_v_layout.addWidget(self.input_label)
        self.line_v_layout.addWidget(self.input_line_edit)
        self.label_line_h_layout.addLayout(self.label_v_layout)
        self.label_line_h_layout.addLayout(self.line_v_layout)
        self.button_h_layout.addWidget(self.yes_pushbuuton)
        self.button_h_layout.addWidget(self.no_pushbuuton)
        self.ui_v_layout.addLayout(self.label_line_h_layout)
        self.ui_v_layout.addLayout(self.button_h_layout)
        self.setLayout(self.ui_v_layout)

        def finish_input():
            try:
                text = self.input_line_edit.text()
            except ValueError:
                print("Null is not valid input!")
                info = QMessageBox(self)
                info.setText("Null is not valid input!")
                info.setWindowTitle("警告！")
                info.exec_()
            else:
                print(text)
                self.canvas.add_text_item(text)
                self.close()

        self.yes_pushbuuton.clicked.connect(finish_input)
        self.no_pushbuuton.clicked.connect(self.close)


class PPApplication(QMainWindow):
    """
    主窗口类
    """

    def __init__(self):
        super().__init__()

        # init the PPCanvas
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 800, 800)
        self.canvas_widget = PPCanvas(self.scene, self)
        self.canvas_widget.setFixedSize(800, 800)
        self.canvas_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.canvas_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # init the window class
        self.translate_window = None
        self.rotate_window = None
        self.scale_window = None
        self.clip_window = None
        self.text_window = None

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
        add_text_act = draw_menu.addAction('Text')
        line_menu = draw_menu.addMenu('线段')
        line_naive_act = line_menu.addAction('Naive')
        line_naive_act.setIcon(QIcon('../../other_folder/other_folder/line.ico'))
        line_dda_act = line_menu.addAction('DDA')
        line_dda_act.setIcon(QIcon('../../other_folder/other_folder/line.ico'))
        line_bresenham_act = line_menu.addAction('Bresenham')
        line_bresenham_act.setIcon(QIcon('../../other_folder/other_folder/line.ico'))
        polygon_menu = draw_menu.addMenu('多边形')
        polygon_dda_act = polygon_menu.addAction('DDA')
        triangle_act = draw_menu.addAction('三角形')
        square_act = draw_menu.addAction('方形')
        circle_act = draw_menu.addAction('圆形')
        polygon_bresenham_act = polygon_menu.addAction('Bresenham')
        ellipse_act = draw_menu.addAction('椭圆')
        curve_menu = draw_menu.addMenu('曲线')
        curve_bezier_act = curve_menu.addAction('Bezier')
        curve_bezier_act.setIcon(QIcon('../../other_folder/other_folder/curve.ico'))
        curve_b_spline_act = curve_menu.addAction('B-spline')
        curve_b_spline_act.setIcon(QIcon('../../other_folder/other_folder/curve.ico'))
        edit_menu = menubar.addMenu('编辑')
        translate_act = edit_menu.addAction('平移')
        translate_act.setIcon(QIcon('../../other_folder/other_folder/translate.ico'))
        rotate_act = edit_menu.addAction('旋转')
        rotate_act.setIcon(QIcon('../../other_folder/other_folder/rotate.ico'))
        scale_act = edit_menu.addAction('缩放')
        scale_act.setIcon(QIcon('../../other_folder/other_folder/scale.ico'))
        clip_menu = edit_menu.addMenu('裁剪')
        clip_cohen_sutherland_act = clip_menu.addAction('Cohen-Sutherland')
        clip_cohen_sutherland_act.setIcon(QIcon('../../other_folder/other_folder/clip.ico'))
        clip_liang_barsky_act = clip_menu.addAction('Liang-Barsky')
        clip_liang_barsky_act.setIcon(QIcon('../../other_folder/other_folder/clip.ico'))
        fill_act = edit_menu.addAction('填充多边形')
        fill_act.setIcon(QIcon('../../other_folder/other_folder/paint_bucket.png'))

        # 连接信号和槽函数
        reset_canvas_act.triggered.connect(lambda: self.reset_canvas_action())
        set_pen_act.triggered.connect(lambda: self.pen_color_action())
        save_canvas_act.triggered.connect(lambda: self.save_canvas_as_json_action())
        save_canvas_as_bmp_act.triggered.connect(lambda: self.save_canvas_as_bmp_action())
        load_canvas_act.triggered.connect(lambda: self.load_canvas_from_json_action())

        exit_act.triggered.connect(qApp.quit)

        add_text_act.triggered.connect(lambda: self.add_text_action())
        line_naive_act.triggered.connect(lambda: self.line_action('Naive'))
        line_bresenham_act.triggered.connect(lambda: self.line_action('Bresenham'))
        line_dda_act.triggered.connect(lambda: self.line_action('DDA'))
        polygon_dda_act.triggered.connect(lambda: self.polygon_action('DDA'))
        polygon_dda_act.setIcon(QIcon('../../other_folder/other_folder/polygon.ico'))
        polygon_bresenham_act.triggered.connect(lambda: self.polygon_action('Bresenham'))
        polygon_bresenham_act.setIcon(QIcon('../../other_folder/other_folder/polygon.ico'))
        ellipse_act.triggered.connect(lambda: self.ellipse_action())
        ellipse_act.setIcon(QIcon('../../other_folder/other_folder/ellipse.ico'))
        curve_bezier_act.triggered.connect(lambda: self.curve_action('Bezier'))
        curve_b_spline_act.triggered.connect(lambda: self.curve_action('B-spline'))
        triangle_act.triggered.connect(lambda: self.triangle_action())
        square_act.triggered.connect(lambda: self.square_action())
        circle_act.triggered.connect(lambda: self.circle_action())

        translate_act.triggered.connect(lambda: self.translate_action())
        rotate_act.triggered.connect(lambda: self.rotate_action())
        scale_act.triggered.connect(lambda: self.scale_action())
        clip_cohen_sutherland_act.triggered.connect(lambda: self.clip_action('Cohen-Sutherland'))
        clip_liang_barsky_act.triggered.connect(lambda: self.clip_action('Liang-Barsky'))
        fill_act.triggered.connect(lambda: self.fill_action())

        tool_bar = self.addToolBar('选择')
        mouse_selection_act = tool_bar.addAction('选择')
        mouse_selection_act.triggered.connect(lambda: self.mouse_selection())
        mouse_selection_act.setIcon(QIcon('../../other_folder/other_folder/mouse.ico'))

        tool_bar = self.addToolBar('颜色')
        tool_bar.addAction(set_pen_act)
        set_pen_act.setIcon(QIcon('../../other_folder/other_folder/pen.ico'))

        tool_bar = self.addToolBar('文字')
        tool_bar.addAction(add_text_act)

        tool_bar = self.addToolBar('线段')
        tool_bar.addAction(line_dda_act)

        tool_bar = self.addToolBar('三角形')
        tool_bar.addAction(triangle_act)

        tool_bar = self.addToolBar('方形')
        tool_bar.addAction(square_act)

        tool_bar = self.addToolBar('圆形')
        tool_bar.addAction(circle_act)

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

        # 设置主窗口的布局
        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.addWidget(self.canvas_widget)
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.hbox_layout)
        self.setCentralWidget(self.central_widget)
        self.statusBar().showMessage('空闲')
        self.resize(600, 600)
        self.setWindowTitle('Pretty Printer')
        self.setWindowIcon(QIcon('../../other_folder/other_folder/cover.png'))

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

    def add_text_action(self):
        self.text_window = AddTextWidget(self.canvas_widget)
        self.text_window.show()

    def line_action(self, algorithm='Naive'):
        # self.canvas_widget.start_draw_line(algorithm, self.get_id())
        self.canvas_widget.start_draw('line', algorithm, self.canvas_widget.get_id())
        self.statusBar().showMessage(algorithm + '算法绘制线段')
        self.canvas_widget.reset_selection()

    def polygon_action(self, algorithm='DDA'):
        # self.canvas_widget.start_draw_polygon(algorithm, self.get_id())
        self.canvas_widget.start_draw('polygon', algorithm, self.canvas_widget.get_id())
        self.statusBar().showMessage(algorithm + '算法绘制多边形')
        self.canvas_widget.reset_selection()

    def ellipse_action(self):
        # self.canvas_widget.start_draw_ellipse(self.get_id())
        self.canvas_widget.start_draw('ellipse', None, self.canvas_widget.get_id())
        self.statusBar().showMessage('中点画圆分绘制椭圆')
        self.canvas_widget.reset_selection()

    def curve_action(self, algorithm):
        '''
        绘制曲线的action
        :param algorithm: 使用的算法
        :return:
        '''
        # self.canvas_widget.start_draw_curve(algorithm, self.get_id())
        self.canvas_widget.start_draw('curve', algorithm, self.canvas_widget.get_id())
        self.statusBar().showMessage(algorithm + '算法绘制曲线')
        self.canvas_widget.reset_selection()

    def triangle_action(self):
        self.canvas_widget.start_draw('triangle', 'DDA', self.canvas_widget.get_id())
        self.canvas_widget.reset_selection()

    def square_action(self):
        self.canvas_widget.start_draw('square', 'DDA', self.canvas_widget.get_id())
        self.canvas_widget.reset_selection()

    def circle_action(self):
        self.canvas_widget.start_draw('circle', 'none', self.canvas_widget.get_id())
        self.canvas_widget.reset_selection()

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

        super(PPApplication, self).keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = PPApplication()
    mw.show()
    sys.exit(app.exec_())

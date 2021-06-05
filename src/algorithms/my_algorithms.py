#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 本文件只允许依赖math库
import math


def line_naive(p_list):
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    result = []
    if x0 == x1:
        for y in range(y0, y1 + 1):
            result.append((x0, y))
    else:
        if x0 > x1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        k = (y1 - y0) / (x1 - x0)
        for x in range(x0, x1 + 1):
            result.append((x, int(y0 + k * (x - x0))))
    return result


def line_dda(p_list):
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    result = []
    dx = x1 - x0
    dy = y1 - y0
    absDx = abs(dx)
    absDy = abs(dy)
    step = max(absDx, absDy)  # 选择较大的一者作为遍历的跨度
    if step == 0:
        result.append((x0, y0))
    else:
        xInc = dx / step
        yInc = dy / step
        x = x0
        y = y0
        result.append((x, y))
        for i in range(0, int(step)):
            x += xInc
            y += yInc
            result.append((int(x), int(y)))
    return result


def line_Bresenham(p_list):
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    result = []
    dy = y1 - y0
    dx = x1 - x0
    absDy = abs(dy)
    absDx = abs(dx)
    x = 0
    y = 0
    x_e = 0
    y_e = 0
    # 决策变量初始值
    px = 2 * absDy - absDx
    py = 2 * absDx - absDy

    # 计算必须的一些常量
    const_2dy_m_2dx = 2 * absDy - 2 * absDx
    const_2dx_m_2dy = 2 * absDx - 2 * absDy
    const_2dy = 2 * absDy
    const_2dx = 2 * absDx

    # 斜率绝对值小于等于1
    if absDy <= absDx:
        if dx >= 0:
            x = x0
            y = y0
            x_e = x1
        # 区间转化为从左到右
        else:
            x = x1
            y = y1
            x_e = x0
        result.append((x, y))
        x_b = x
        # 遍历x区间
        for x in range(x_b + 1, x_e + 1):
            if px < 0:
                px += const_2dy
            else:
                px += const_2dy_m_2dx
                # 如果当前斜率为正
                if (dx < 0 and dy < 0) or (dx > 0 and dy > 0):
                    y += 1
                else:
                    y -= 1
            result.append((x, y))
    # 斜率绝对值大于1
    else:
        if dy >= 0:
            x = x0
            y = y0
            y_e = y1
        else:
            x = x1
            y = y1
            y_e = y0
        result.append((x, y))
        y_b = y
        # 遍历y区间
        for y in range(y_b + 1, y_e + 1):
            if py < 0:
                py += const_2dx
            else:
                py += const_2dx_m_2dy
                # 如果当前斜率为正
                if (dx < 0 and dy < 0) or (dx > 0 and dy > 0):
                    x += 1
                else:
                    x -= 1
            result.append((x, y))
    return result


def draw_line(p_list, algorithm):
    """绘制线段

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 线段的起点和终点坐标
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'，此处的'Naive'仅作为示例，测试时不会出现
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """

    if algorithm == 'Naive':
        return line_naive(p_list)
    elif algorithm == 'DDA':
        return line_dda(p_list)
    elif algorithm == 'Bresenham':
        return line_Bresenham(p_list)
    return None


def draw_polygon(p_list, algorithm, finish=True):
    """绘制多边形

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 多边形的顶点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    start = 0
    if finish:
        start = 0
    else:
        start = 1
    for i in range(start, len(p_list)):
        line = draw_line([p_list[i - 1], p_list[i]], algorithm)
        result += line
    return result


def ellipse_point(xc, yc, x, y):
    result = [(xc + x, yc + y), (xc + x, yc - y), (xc - x, yc + y), (xc - x, yc - y)]
    return result


def draw_ellipse(p_list):
    """绘制椭圆（采用中点圆生成算法）

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 椭圆的矩形包围框左上角和右下角顶点坐标
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    # 计算出需要a,b及其平方（计算时需要），并计算出椭圆的中心点
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    a = int(abs((x1 - x0) / 2))
    b = int(abs((y0 - y1) / 2))
    a2 = a * a
    b2 = b * b
    xc = int((x0 + x1) / 2)
    yc = int((y0 + y1) / 2)
    x, y = 0, b
    result = []
    result += ellipse_point(xc, yc, x, y)

    p = b2 + a2 * (-b + 1 / 4)  # 决策变量

    while b2 * (x + 1) < a2 * (y - 0.5):
        if p < 0:
            p += b2 * (2 * x + 3)
        else:
            p += b2 * (2 * x + 3) + a2 * (-2 * y + 2)
            y -= 1
        x += 1
        result += ellipse_point(xc, yc, x, y)

    p = b2 * (x + 0.5) ** 2 + a2 * (y - 1) ** 2 - a2 * b2
    while y >= 0:
        if p < 0:
            p += a2 * (-2 * y + 3) + b2 * (2 * x + 2)
            x += 1
        else:
            p += a2 * (-2 * y + 3)
        y -= 1
        result += ellipse_point(xc, yc, x, y)
    return result


def basic_bezier(p1, p2, t):
    '''
    bezier曲线的位置计算，递归算法的基础情况
    '''
    x1, y1 = p1
    x2, y2 = p2
    return t * x1 + (1 - t) * x2, t * y1 + (1 - t) * y2


def get_bezier(p_list, n, pos, t):
    '''
    通过递归的方式获得bezier曲线
    输入：控制点坐标，当前递归层数，当前的递归位置，时间戳
    '''
    if n == 1:
        return basic_bezier(p_list[pos], p_list[pos + 1], t)
    else:
        x1, y1 = get_bezier(p_list, n - 1, pos, t)
        x2, y2 = get_bezier(p_list, n - 1, pos + 1, t)
        return t * x1 + (1 - t) * x2, t * y1 + (1 - t) * y2


def get_bezier_by_math(p_list, t):
    '''
    通过组合数计算获得bezier曲线上的一个点的坐标
    输入：控制点坐标以及当前的时间戳t
    '''
    n = len(p_list) - 1
    c_m_n = lambda n_, r_: math.factorial(n_) / (math.factorial(r_) * math.factorial(n_ - r_))
    bezier_x = 0
    bezier_y = 0
    for i in range(0, n + 1):
        tem_t_pow = t ** i
        tem_mt_pow = (1 - t) ** (n - i)
        bezier_x += p_list[i][0] * c_m_n(n, i) * tem_t_pow * tem_mt_pow
        bezier_y += p_list[i][1] * c_m_n(n, i) * tem_t_pow * tem_mt_pow
    return bezier_x, bezier_y


def get_B_spline(p_list):
    '''
    获取b样条曲线
    输入： 当前所有的控制点坐标
    '''
    n = len(p_list)
    m = n + 3
    step = 1 / (m - 6)
    knot_vector = 3 * [0] + [tem * step for tem in range(m - 5)] + 3 * [1]
    seg_num = n - 3

    cof_x_3 = []
    cof_x_2 = []
    cof_x_1 = []
    cof_x_0 = []
    cof_y_3 = []
    cof_y_2 = []
    cof_y_1 = []
    cof_y_0 = []

    for i in range(seg_num):
        cof_x_3.append((-p_list[i][0] + 3 * p_list[i + 1][0] - 3 * p_list[i + 2][0] + p_list[i + 3][0]) / 6.0)
        cof_x_2.append((3 * p_list[i][0] - 6 * p_list[i + 1][0] + 3 * p_list[i + 2][0]) / 6.0)
        cof_x_1.append((-3 * p_list[i][0] + 3 * p_list[i + 2][0]) / 6.0)
        cof_x_0.append((p_list[i][0] + 4 * p_list[i + 1][0] + p_list[i + 2][0]) / 6.0)

        cof_y_3.append((-p_list[i][1] + 3 * p_list[i + 1][1] - 3 * p_list[i + 2][1] + p_list[i + 3][1]) / 6.0)
        cof_y_2.append((3 * p_list[i][1] - 6 * p_list[i + 1][1] + 3 * p_list[i + 2][1]) / 6.0)
        cof_y_1.append((-3 * p_list[i][1] + 3 * p_list[i + 2][1]) / 6.0)
        cof_y_0.append((p_list[i][1] + 4 * p_list[i + 1][1] + p_list[i + 2][1]) / 6.0)

    step_num = 1000
    step = 1.0 / step_num
    t = 0.0
    ret = []
    for i in range(step_num):
        for index in range(3, m - 3):
            if knot_vector[index] <= t and knot_vector[index + 1] > t:
                break
        t_index = index - 3
        t_for_cal = (t - knot_vector[index]) / (knot_vector[index + 1] - knot_vector[index])
        t_pow_2 = t_for_cal * t_for_cal
        t_pow_3 = t_pow_2 * t_for_cal
        x, y = cof_x_3[t_index] * (t_pow_3) + cof_x_2[t_index] * (t_pow_2) + cof_x_1[t_index] * t_for_cal + cof_x_0[
            t_index], \
               cof_y_3[t_index] * (t_pow_3) + cof_y_2[t_index] * (t_pow_2) + cof_y_1[t_index] * t_for_cal + cof_y_0[
                   t_index]
        ret += [[int(x), int(y)]]
        t += step
    return ret


def draw_curve(p_list, algorithm):
    """绘制曲线

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 曲线的控制点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'Bezier'和'B-spline'（三次均匀B样条曲线，曲线不必经过首末控制点）
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    step_num = 1000
    if algorithm == 'Bezier':
        step = 1.0 / step_num
        t = 0.0
        pLen = len(p_list)
        for i in range(step_num):
            # x,y=get_bezier(p_list,pLen-1,0,t)
            x, y = get_bezier_by_math(p_list, t)
            result += [(int(x), int(y))]
            t += step
    elif algorithm == 'B-spline':
        result += get_B_spline(p_list)
    return result


def draw_control_points(p_list, algorithm):
    """绘制曲线的控制点

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 曲线的控制点坐标
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    for i in range(1, len(p_list)):  # 不需要首尾相连
        line = draw_line([p_list[i - 1], p_list[i]], algorithm)
        result += line
    return result


def translate(p_list, dx, dy):
    """平移变换

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param dx: (int) 水平方向平移量
    :param dy: (int) 垂直方向平移量
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    for i in range(len(p_list)):
        p_list[i] = p_list[i][0] + dx, p_list[i][1] + dy
    return p_list


def rotate(p_list, x, y, r):
    """旋转变换（除椭圆外）

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param x: (int) 旋转中心x坐标
    :param y: (int) 旋转中心y坐标
    :param r: (int) 顺时针旋转角度（°）
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    # 首先平移到原点
    p_list = translate(p_list, -x, -y)

    # 旋转
    radian = r * math.pi / 180.0
    cal_val = math.cos(radian)
    sin_val = math.sin(radian)

    for i in range(len(p_list)):
        tx, ty = p_list[i]
        # p_list[i] = int(cal_val * tx - sin_val * ty), int(sin_val * tx + cal_val * ty)
        p_list[i] = round(cal_val * tx - sin_val * ty), round(sin_val * tx + cal_val * ty)
    # 平移到旋转中心
    return translate(p_list, x, y)


def scale(p_list, x, y, s):
    """缩放变换

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param x: (int) 缩放中心x坐标
    :param y: (int) 缩放中心y坐标
    :param s: (float) 缩放倍数
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    # 首先平移到原点
    p_list = translate(p_list, -x, -y)

    # 缩放
    for i in range(len(p_list)):
        p_list[i] = int(s * p_list[i][0]), int(s * p_list[i][1])

    # 平移到缩放中心
    return translate(p_list, x, y)


def encode(x_min, y_min, x_max, y_max, x, y):
    """
    使用比较法进行端点编码
    :param x_min: 裁剪窗口左上角x坐标
    :param y_min: 裁剪窗口左上角y坐标
    :param x_max: 裁剪窗口右下角x坐标
    :param y_max: 裁剪窗口右下角y坐标
    :param x,y : 线段端点坐标
    :return: 编码
    """
    code = 0
    if x < x_min:
        code += 1
    elif x > x_max:
        code += 1 << 1

    if y < y_max:
        code += 1 << 2
    elif y > y_min:
        code += 1 << 3
    return code


def clip_cohen(p_list, x_min, y_min, x_max, y_max):
    '''
    编码法裁剪
    :param p_list: 线段端点
    :param x_min: 裁剪窗口左上角x坐标
    :param y_min: 裁剪窗口左上角y坐标
    :param x_max: 裁剪窗口右下角x坐标
    :param y_max: 裁剪窗口右下角y坐标
    :return: 裁剪之后的线段顶点，如果舍弃线段，返回None
    '''
    x1, y1 = p_list[0]
    x2, y2 = p_list[1]
    left_code = 1
    right_code = 1 << 1
    bottom_code = 1 << 2
    top_code = 1 << 3
    x, y = 0, 0
    code_begin = encode(x_min, y_min, x_max, y_max, x1, y1)
    code_end = encode(x_min, y_min, x_max, y_max, x2, y2)
    while (code_begin | code_end) != 0: # 当前线段不在裁剪窗口内
        if code_begin & code_end != 0: # 当前线段在裁剪窗口之外
            return None
        code = code_begin
        if code == 0: # 使用裁剪窗口之外的顶点求交
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            code_begin, code_end = code_end, code_begin
            code = code_begin
        # 使用参数方程求交
        if code & left_code:
            k = (y2 - y1) / (x2 - x1)
            x = x_min
            y = (y1 + k * (x_min - x1))
        elif code & right_code:
            k = (y2 - y1) / (x2 - x1)
            x = x_max
            y = (y1 + k * (x_max - x1))
        elif code & bottom_code:
            k = (x2 - x1) / (y2 - y1)
            y = y_max
            x = (x1 + k * (y_max - y1))
        elif code & top_code:
            k = (x2 - x1) / (y2 - y1)
            y = y_min
            x = (x1 + k * (y_min - y1))

        x1, y1 = x, y
        code_begin = encode(x_min, y_min, x_max, y_max, x1, y1) #更新求交之后顶点的编码
    return [[round(x1), round(y1)], [round(x2), round(y2)]]


def clip_liang_barsky(p_list, x_min, y_min, x_max, y_max):
    '''
    使用Liang-Barsky算法进行裁剪
    :param p_list: 线段顶点坐标
    :param x_min: 裁剪窗口左上角x坐标
    :param y_min: 裁剪窗口左上角y坐标
    :param x_max: 裁剪窗口右下角x坐标
    :param y_max: 裁剪窗口右下角y坐标
    :return: 裁剪之后的线段顶点，如果舍弃线段，返回None
    '''
    x_0, y_0 = p_list[0]
    x_1, y_1 = p_list[1]
    delta_x = x_1 - x_0
    delta_y = y_1 - y_0
    p_q = [
        [-delta_x, x_0 - x_min],
        [delta_x, x_max - x_0],
        [-delta_y, y_0 - y_max],
        [delta_y, y_min - y_0]
    ]
    u_begin = 0
    u_end = 1

    for current_pq in p_q:
        p, q = current_pq
        if p == 0:
            if q < 0:
                return None
            else:
                continue

        u_tem = q / p
        if p < 0:
            u_begin = max(u_begin, u_tem)
        else:
            u_end = min(u_end, u_tem)

    if u_begin > u_end: #不存在解
        return None

    return [
        [round(x_0 + u_begin*delta_x), round(y_0 + u_begin * delta_y)],
        [round(x_0 + u_end*delta_x), round(y_0 + u_end*delta_y)]
    ]


def clip(p_list, x_min, y_min, x_max, y_max, algorithm):
    """线段裁剪

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 线段的起点和终点坐标
    :param x_min: 裁剪窗口左上角x坐标
    :param y_min: 裁剪窗口左上角y坐标
    :param x_max: 裁剪窗口右下角x坐标
    :param y_max: 裁剪窗口右下角y坐标
    :param algorithm: (string) 使用的裁剪算法，包括'Cohen-Sutherland'和'Liang-Barsky'
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1]]) 裁剪后线段的起点和终点坐标
    """
    # 确保输入正确
    if len(p_list) != 2: #顶点数量应为两个
        return None
    if x_min > x_max:
        x_min, x_max = x_max, x_min
    if y_min < y_max:
        y_min, y_max = y_max, y_min

    if algorithm == 'Cohen-Sutherland':
        return clip_cohen(p_list, x_min, y_min, x_max, y_max)
    elif algorithm == 'Liang-Barsky':
        return clip_liang_barsky(p_list, x_min, y_min, x_max, y_max)


class Node:
    def __init__(self, data, next=None):
        self.data = data
        self.next = next


class LinkList:
    def __init__(self):
        self.head = None

    def is_empty(self):
        return self.head is None

    def append(self, data):
        # 在链表的尾部添加一个节点
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            return

        cur_node = self.head
        while cur_node.next is not None:
            cur_node = cur_node.next
        cur_node.next = new_node

    def remove(self, val):
        pre_node = None
        cur_node = self.head
        while cur_node is not None and cur_node.data != val:
            pre_node = cur_node
            cur_node = cur_node.next
        if cur_node is not None:
            if pre_node is None:
                self.head = cur_node.next
            else:
                pre_node.next = cur_node.next
        else:
            pass

    def print(self):
        cur_node = self.head
        node_list = []
        while cur_node is not None:
            node_list.append(cur_node)
            cur_node = cur_node.next
        for node in node_list:
            print(node.data)


def polygon_fill(p_list, height):
    draw_points = []
    y_min = 999999999
    y_max = -1
    for edge in p_list:
        if edge[1] < y_min:
            y_min = edge[1]
        if edge[1] > y_max:
            y_max = edge[1]

    # y_min = max(0, y_min)
    y_max = min(height-1, y_max)
    polygon_len = len(p_list)

    def get_valid_index(index):
        return (index + polygon_len)%polygon_len
    NET = []
    for i in range(height):
        NET.append(None)

    def NET_add(index, item):
        if NET[index] is None:
            NET[index] = LinkList()
        NET[index].append(item)

    for y_index in range(y_min, y_max + 1):
        for p_index, edge in enumerate(p_list):
            if edge[1] == y_index:
                # 尝试将该点附近的两条边加入边表中
                [cur_x, cur_y] = edge
                if p_list[get_valid_index(p_index-1)][1] > cur_y:
                    [tem_x, tem_y] = p_list[get_valid_index(p_index-1)]
                    m = (cur_x - tem_x) / (cur_y - tem_y)
                    NET_add(y_index, [cur_x, m, tem_y])

                if p_list[get_valid_index(p_index+1)][1] > cur_y:
                    [tem_x, tem_y] = p_list[get_valid_index(p_index+1)]
                    m = (tem_x - cur_x) / (tem_y - cur_y)
                    NET_add(y_index, [cur_x, m, tem_y])

    def float_equal(x, y, threshold = 1e-3):
        return (x-y)<threshold

    AET = LinkList()
    for y_index in range(y_min, y_max+1):
        # 从边表中加边
        if NET[y_index] is not None:
            cur_node = NET[y_index].head
            while cur_node is not None:
                AET.append(cur_node.data)
                cur_node = cur_node.next

        # 删除边
        if not AET.is_empty():
            cur_node = AET.head
            while cur_node is not None:
                [pre_x, m, y_top] = cur_node.data
                if y_top == y_index:
                    cur_node = cur_node.next
                    AET.remove([pre_x, m, y_top])
                    continue
                cur_node = cur_node.next

        # 扫描填充
        x_list = []
        if not AET.is_empty():
            cur_node = AET.head
            while cur_node is not None:
                [pre_x, m, y_top] = cur_node.data
                cur_node = cur_node.next
                x_list.append(pre_x)

            x_list.sort()

            for x_index in range(0, len(x_list), 2):
                x_1 = x_list[x_index]
                x_2 = x_list[x_index+1]
                for tem_x in range(int(x_1), int(x_2+1) ):
                    draw_points.append([int(tem_x), int(y_index)])

        # 更新边
        if not AET.is_empty():
            cur_node = AET.head
            while cur_node is not None:
                [pre_x, m, y_top] = cur_node.data
                pre_x += m
                cur_node.data = [pre_x, m, y_top]
                cur_node = cur_node.next
    return draw_points


def polygon_fill_line(p_list, height):
    draw_points = []
    y_min = 999999999
    y_max = -1
    for edge in p_list:
        if edge[1] < y_min:
            y_min = edge[1]
        if edge[1] > y_max:
            y_max = edge[1]

    # y_min = max(0, y_min)
    y_max = min(height-1, y_max)
    polygon_len = len(p_list)

    def get_valid_index(index):
        return (index + polygon_len)%polygon_len
    NET = []
    for i in range(height):
        NET.append(None)

    def NET_add(index, item):
        if NET[index] is None:
            NET[index] = LinkList()
        NET[index].append(item)

    for y_index in range(y_min, y_max + 1):
        for p_index, edge in enumerate(p_list):
            if edge[1] == y_index:
                # 尝试将该点附近的两条边加入边表中
                [cur_x, cur_y] = edge
                if p_list[get_valid_index(p_index-1)][1] > cur_y:
                    [tem_x, tem_y] = p_list[get_valid_index(p_index-1)]
                    m = (cur_x - tem_x) / (cur_y - tem_y)
                    NET_add(y_index, [cur_x, m, tem_y])

                if p_list[get_valid_index(p_index+1)][1] > cur_y:
                    [tem_x, tem_y] = p_list[get_valid_index(p_index+1)]
                    m = (tem_x - cur_x) / (tem_y - cur_y)
                    NET_add(y_index, [cur_x, m, tem_y])

    def float_equal(x, y, threshold = 1e-3):
        return (x-y)<threshold

    AET = LinkList()
    for y_index in range(y_min, y_max+1):
        # 从边表中加边
        if NET[y_index] is not None:
            cur_node = NET[y_index].head
            while cur_node is not None:
                AET.append(cur_node.data)
                cur_node = cur_node.next

        # 删除边
        if not AET.is_empty():
            cur_node = AET.head
            while cur_node is not None:
                [pre_x, m, y_top] = cur_node.data
                if y_top == y_index:
                    cur_node = cur_node.next
                    AET.remove([pre_x, m, y_top])
                    continue
                cur_node = cur_node.next

        # 扫描填充
        x_list = []
        if not AET.is_empty():
            cur_node = AET.head
            while cur_node is not None:
                [pre_x, m, y_top] = cur_node.data
                cur_node = cur_node.next
                x_list.append(pre_x)

            x_list.sort()

            for x_index in range(0, len(x_list), 2):
                x_1 = x_list[x_index]
                x_2 = x_list[x_index+1]
                draw_points.append([[int(x_1), int(y_index)], [int(x_2), int(y_index)]])

        # 更新边
        if not AET.is_empty():
            cur_node = AET.head
            while cur_node is not None:
                [pre_x, m, y_top] = cur_node.data
                pre_x += m
                cur_node.data = [pre_x, m, y_top]
                cur_node = cur_node.next
    return draw_points

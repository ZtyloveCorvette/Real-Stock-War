# coding=utf8

import sys
import re
import urllib
import threading
import configparser
import logging
import http.cookiejar
import csv
import bs4
import time
import os
import hashlib
import glob
import json
import queue
import pathlib

import PyQt5

import gui.MainWindow
import gui.BuyStock

spacial_char = '↑↓←→↖↙↗↘↕'

url_stock_code = 'http://quote.eastmoney.com/stocklist.html'
url_currency_acronyms = 'http://www.easy-forex.com/int/zh-hans/currencyacronyms/'

api_sinajs = 'http://hq.sinajs.cn/rn={}&list={}'

key_stock_code = '">(.*?)\((.*?)\)<'


def get_current_time():
    return str(int(time.time()))


class App:
    """

    """

    isRunning = {}
    isRunning['app'] = True

    timeout = 10

    cookie = http.cookiejar.CookieJar()
    handler = urllib.request.HTTPCookieProcessor(cookie)
    opener = urllib.request.build_opener(handler)

    taskQueue = queue.Queue()

    def __init__(self):

        logging.basicConfig(filename='app.log', level=logging.DEBUG, filemode='w',
                            format='%(relativeCreated)d[%(levelname).4s][%(threadName)-.10s]%(message)s')

        self.gameData = {}

        self.first_run()
        self.load_config()
        self.load_save()
        self.load_cache()
        self.load_ai()
        self.show_gui()
        self.show_cache()
        self.start_star()
        self.fetch_current_data()

    def first_run(self):
        if not os.path.isdir('tmp'):
            os.mkdir('tmp')  # 用于外部代码资料储存
        if not os.path.isdir('save'):
            os.mkdir('save')  # 用于存档
        if not os.path.isdir('data'):
            os.mkdir('data')  # 用于内部代码资料储存
        if not os.path.isdir('ai'):
            os.mkdir('ai')  # 用于储存外部AI脚本
        for file in glob.glob('tmp/*'):
            os.remove(file)  # 清理tmp的外部代码资料储存

    def load_config(self):
        pass

    def load_save(self):
        if glob.glob('save/*.save') == []:  # 判断——没有存档
            print('当前没有存档，是否新建？[y]/n')
            ans = input('>')
            if ans == '' or ans == 'y' or ans == 'Y':  # 选择——是：新建存档
                self.gameData['user'] = {}
                while True:
                    print('请输入用户名：')
                    ans = input('>')
                    if ans == '':
                        print('用户名不能为空！')
                    else:
                        self.gameData['user']['name'] = ans
                        break
                while True:
                    print('请选择游戏模式：')
                    print('1：规定时间谁多谁嬴。')
                    print('2：规定金额谁快谁嬴。')
                    ans = input('>')
                    if ans == '1':
                        self.gameData['user']['mode'] = 'settime'
                        break
                    elif ans == '2':
                        self.gameData['user']['mode'] = 'setmoney'
                        break
                    else:
                        print('请输入[1-2]的数字！')
                while True:
                    print('请选择难度：')
                    print('1：简单。起始资金多。')
                    print('2：普通。起始资金中。')
                    print('3：困难。起始资金少。')
                    ans = input('>')
                    if ans == '1':
                        self.gameData['user']['difficulty'] = 1
                        break
                    elif ans == '2':
                        self.gameData['user']['difficulty'] = 2
                        break
                    elif ans == '3':
                        self.gameData['user']['difficulty'] = 3
                        break
                    else:
                        print('请输入[1-3]的数字！')
                with open('save/{}.save'.format(self.gameData['user']['name']), 'w') as save_file:
                    save_file.write(json.dumps(self.gameData['user']))
            else:  # 选择——放弃
                pass
        else:  # 判断——有存档
            if len(glob.glob('save/*.save')) == 1:  # 判断——单文件：直接加载
                with open(glob.glob('save/*.save')[0], 'r')as save_file:
                    data = save_file.read()
                    self.gameData['user'] = json.loads(data)
            else:  # 判断——多文件：列出后选择
                text = '{}：{}'
                while True:
                    num = 1
                    print('检测到多个存档文件，请选择一个以加载：')
                    for file in glob.glob('save/*.save'):
                        print(text.format(num, pathlib.PurePath(file).stem))
                        num += 1
                    ans = input('>')
                    if ans.isdigit():  # 判断——输入正常：检查是否在范围内
                        ans = int(ans)
                        if ans > 0 and ans < num:  # 判断——在范围内
                            ans -= 1
                            with open(glob.glob('save/*.save')[ans], 'r')as save_file:
                                data = save_file.read()
                                self.gameData['user'] = json.loads(data)
                            print(self.gameData['user'])
                        else:  # 判断——不在范围内
                            print('不存在该选项！')
                    else:  # 判断——输入非法
                        print('请输入数字！')

    def load_cache(self):
        pass

    def load_ai(self):
        pass

    def show_gui(self):
        def show():
            app = PyQt5.QtWidgets.QApplication(sys.argv)
            main_window = PyQt5.QtWidgets.QMainWindow()
            self.ui = Main_Window()
            self.ui.setupUi(main_window)
            self.ui.init(self.gameData)
            main_window.show()
            sys.exit(app.exec_())

        t_gui = threading.Thread(target=show)
        t_gui.start()

    def show_cache(self):
        pass

    def start_star(self):
        def star():
            """伴飞卫星"""
            self.isRunning['Star'] = True
            shStatus = ''
            szStatus = ''
            while self.isRunning['Star']:
                if self.taskQueue.qsize() > 0:
                    task = self.taskQueue.get_nowait()

                if 'stockCode_sh' in self.gameData:
                    self.shStatus = '正在获取信息：{:.2f}%'
                    if 'new_data_sh' in self.gameData:
                        rate = len(self.gameData['new_data_sh'].items()) / len(self.gameData['stockCode_sh'])
                        self.shStatus = self.shStatus.format(rate * 100)
                else:
                    self.shStatus = '正在获取代码'

                if 'stockCode_sz' in self.gameData:
                    self.szStatus = '正在获取信息：{:.2f}%'
                    if 'new_data_sz' in self.gameData:
                        rate = len(self.gameData['new_data_sz'].items()) / len(self.gameData['stockCode_sz'])
                        self.szStatus = self.szStatus.format(rate * 100)
                else:
                    self.szStatus = '正在获取代码'

                if 'ui' in dir(self):
                    self.ui.set_status_bar_text('上海：{}；深圳：{}。'.format(self.shStatus, self.szStatus))
                time.sleep(0.1)

        t_star = threading.Thread(target=star)
        t_star.start()

    def fetch_current_data(self):
        # 根据游戏内容，综合当前网络速度与延迟，拟决定用10个线程处理以下任务：
        # 以下任务同时进行：
        def fetchDaPanData():
            """查询大盘信息"""
            self.isRunning['fetchDaPanData'] = True
            while self.isRunning['fetchDaPanData']:
                try:
                    logging.info('正在获取查询大盘指数…')
                    logging.info('大盘指数获取完毕。')
                    self.isRunning['fetchDaPanData'] = False
                except:
                    pass

        def fetchStockCode():
            """查询股票代码"""
            self.isRunning['fetchStockCode'] = True
            while self.isRunning['fetchStockCode']:
                try:
                    logging.info('正在获取股票代码…')
                    # 构建请求
                    request = urllib.request.Request(url_stock_code)
                    # 获取响应
                    response = self.opener.open(request, timeout=self.timeout)
                    # 解码
                    stockList = response.read().decode('gbk')
                    soup = bs4.BeautifulSoup(stockList, 'lxml')
                    pattern = re.compile('">(.*?)\((.*?)\)<')
                    self.gameData['stockCode_sh'] = re.findall(pattern, str(soup.find_all('ul')[7]))
                    self.gameData['stockCode_sz'] = re.findall(pattern, str(soup.find_all('ul')[8]))
                    self.isRunning['fetchStockCode'] = False
                except Exception as e:
                    logging.debug('fetchStockCode崩溃')

        def fetchSHStock():
            """用已保存的股票代码查询上证综合股票当前信息"""
            self.isRunning['fetchSHStock'] = True
            while self.isRunning['fetchSHStock']:
                if 'stockCode_sh' not in self.gameData:
                    time.sleep(0.1)
                else:
                    load_list = []
                    for each in self.gameData['stockCode_sh']:
                        load_list.append(each)
                    ###
                    newList = []
                    for each in load_list:
                        newList.append('sh' + each[1])
                    self.gameData['new_data_sh'] = self.api_get_sinajs(get_current_time(), newList)
                    self.isRunning['fetchSHStock'] = False
            for each in self.gameData['new_data_sh'].keys():
                self.ui.add_list_widget_sh(self.gameData['new_data_sh'][each][0])

        def fetchSZStock():
            """用已保存的股票代码查询深证成份股票当前信息"""
            self.isRunning['fetchSZStock'] = True
            while self.isRunning['fetchSZStock']:
                if 'stockCode_sz' not in self.gameData:
                    time.sleep(0.1)
                else:
                    load_list = []
                    for each in self.gameData['stockCode_sz']:
                        load_list.append(each)
                    ###
                    newList = []
                    for each in load_list:
                        newList.append('sz' + each[1])
                    self.gameData['new_data_sz'] = self.api_get_sinajs(get_current_time(), newList)
                    self.isRunning['fetchSZStock'] = False
            for each in self.gameData['new_data_sz'].keys():
                self.ui.add_list_widget_sz(self.gameData['new_data_sz'][each][0])

        dapan = threading.Thread(target=fetchDaPanData)
        stockCode = threading.Thread(target=fetchStockCode)
        shStock = threading.Thread(target=fetchSHStock)
        szStock = threading.Thread(target=fetchSZStock)
        dapan.start()
        stockCode.start()
        shStock.start()
        szStock.start()

    def api(self, cmd):
        pass

    def api_get_sinajs(self, time, codeList):
        """
        :param time:int
        :param codeList:string_list
        :return info_dict:list_dict
        """
        num_of_each_ask = 10  # 每次网络请求所询问的资料数量
        ask_times = int(len(codeList) / num_of_each_ask) + 1  # 计算出一共需请求多少次
        # 把请求进行组合
        request_code_dict = {}
        for i in range(ask_times):
            request_code_dict[','.join(codeList[i * num_of_each_ask:i * num_of_each_ask + num_of_each_ask])] = False
        # 生成代码与回复对应的字典
        code_raw_dict = {}
        retry = True
        while retry:
            for each in request_code_dict.keys():
                # 构建请求
                request = urllib.request.Request(api_sinajs.format(time, each))
                # 获取响应
                response = self.opener.open(request, timeout=self.timeout)
                # 解码
                try:
                    raw_respond = response.read().decode('gbk')
                except urllib.error.URLError as e:
                    pass
                else:
                    respond_string_list = raw_respond.split('\n')
                    for i, every in enumerate(respond_string_list):
                        if every != '':
                            code_raw_dict[each.split(',')[i]] = every
                        else:
                            pass
                    request_code_dict[each] = True
                finally:
                    retry = False
                    for every in request_code_dict.keys():
                        if not request_code_dict[every]:
                            retry = True
        # 生成列表
        code_info_dict = {}
        for each in code_raw_dict.keys():
            value = code_raw_dict[each].split('"')[1]
            if value == '':
                text = 'api返回Null。{}'
                text = text.format(each)
                logging.debug(text)
            elif value == 'FAILED':
                text = 'api返回FAILED。{}'
                text = text.format(each)
                logging.debug(text)
            else:
                info = value.split(',')
                info[0] = info[0].replace(' ', '')
                code_info_dict[each] = info
        return code_info_dict


class Main_Window(PyQt5.QtWidgets.QMainWindow, gui.MainWindow.Ui_MainWindow):
    change_status_text = PyQt5.QtCore.pyqtSignal(str)  # 信号——改变状态条文字
    add_list_widget_sh_item = PyQt5.QtCore.pyqtSignal(str)  # 信号——增加上海表单元素
    add_list_widget_sz_item = PyQt5.QtCore.pyqtSignal(str)  # 信号——增加深圳表单元素

    def init(self, gameData):
        self.gameData = gameData  # 传参
        self.change_status_text.connect(self._set_status_bar_text)  # 连接——改变状态条文字
        self.add_list_widget_sh_item.connect(self._add_list_widget_sh)  # 连接——增加上海表单元素
        self.add_list_widget_sz_item.connect(self._add_list_widget_sz)  # 连接——增加深圳表单元素
        self.listWidget_sh.itemClicked.connect(self._list_widget_sh_item_clicked)  # 连接——点击上海表单元素
        self.listWidget_sz.itemClicked.connect(self._list_widget_sz_item_clicked)  # 连接——点击深圳表单元素
        self.pushButton_sh.released.connect(self._push_button_sh_buy_clicked)  # 连接——买入上海股票
        self.pushButton_sz.released.connect(self._push_button_sz_buy_clicked)  # 连接——买入深圳股票

    def set_status_bar_text(self, text):
        self.change_status_text.emit(text)

    def _set_status_bar_text(self, text):
        self.statusbar.showMessage(text)

    def add_list_widget_sh(self, text):
        self.add_list_widget_sh_item.emit(text)

    def _add_list_widget_sh(self, text):
        item = PyQt5.QtWidgets.QListWidgetItem()
        item.setText(text)
        self.listWidget_sh.addItem(item)

    def add_list_widget_sz(self, text):
        self.add_list_widget_sz_item.emit(text)

    def _add_list_widget_sz(self, text):
        item = PyQt5.QtWidgets.QListWidgetItem()
        item.setText(text)
        self.listWidget_sz.addItem(item)

    def _list_widget_sh_item_clicked(self, item):
        print(item.text())
        for each in self.gameData['new_data_sh'].keys():
            if self.gameData['new_data_sh'][each][0] == item.text():
                newList = self.gameData['new_data_sh'][each]
                newList[0] = '名称：' + newList[0]
                newList[1] = '今开：' + newList[1]
                newList[2] = '昨收：' + newList[2]
                newList[3] = '当前：' + newList[3]
                newList[4] = '最高：' + newList[4]
                newList[5] = '最低：' + newList[5]
                tmp = '\n'.join(newList[:6])
                self.label_sh.setText(tmp)
                break

    def _list_widget_sz_item_clicked(self, item):
        print(item.text())
        for each in self.gameData['new_data_sz'].keys():
            if self.gameData['new_data_sz'][each][0] == item.text():
                newList = self.gameData['new_data_sz'][each]
                newList[0] = '名称：' + newList[0]
                newList[1] = '今开：' + newList[1]
                newList[2] = '昨收：' + newList[2]
                newList[3] = '当前：' + newList[3]
                newList[4] = '最高：' + newList[4]
                newList[5] = '最低：' + newList[5]
                tmp = '\n'.join(newList[:6])
                self.label_sz.setText(tmp)
                break

    def _push_button_sh_buy_clicked(self):
        def show():
            app = PyQt5.QtWidgets.QApplication(sys.argv)
            BuyStock = PyQt5.QtWidgets.QWidget()
            ui = Ui_BuyStock()
            ui.setupUi(BuyStock)
            ui.init(self.gameData)
            BuyStock.show()
            sys.exit(app.exec_())

        t_widget_sh_buy = threading.Thread(target=show)
        t_widget_sh_buy.start()

    def _push_button_sz_buy_clicked(self):
        print(self.listWidget_sz.currentItem().text())


class Ui_BuyStock(PyQt5.QtWidgets.QWidget, gui.BuyStock.Ui_BuyStock):
    def init(self, gameData):
        self.gameData = gameData


if __name__ == '__main__':
    I = App()

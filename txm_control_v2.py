import sys
import matplotlib.pyplot as plt
import numpy as np
import os
import threading
import time
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QRadioButton, QApplication, QWidget, QFrame,
                             QLineEdit, QPlainTextEdit, QWidget, QPushButton, QLabel, QCheckBox, QGroupBox,
                             QScrollBar, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
                             QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea,
                             QSlider, QComboBox, QButtonGroup, QMessageBox, QSizePolicy)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont
from qtconsole.rich_jupyter_widget import RichIPythonWidget, RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
#from IPython.lib import guisupport
from qtconsole.manager import QtKernelManager
#from IPython import get_ipython
#from scan_list import *
import threading
import bluesky.plan_stubs as bps
import ast
import numpy as np
from inspect import getmembers, isfunction

#from extract_scan_list import prepare_scan_list, convert_fun_dict
from scan_list_common import fxi_load_scan_list_common
from scan_list_other import fxi_load_scan_list_other
from scan_list_user import fxi_load_scan_list_user
from scan_list_pzt import fxi_load_scan_list_pzt

#get_ipython().run_line_magic("run", "-i /nsls2/data/fxi-new/shared/software/fxi_control/scan_list.py")

global txm, CALIBER, scan_list
scan_list = {}



def motor_list(n=1):
    motor1 = {}
    motor2 = {}
    motor3 = {}
    motor4 = {}
    motor5 = {}
    motor6 = {}
    motor7 = {}

    try:
        motor1['XEng'] = XEng
        motor1['beam_current'] = beam_current
        motor1['zps.sx'] = zps.sx
        motor1['zps.sy'] = zps.sy
        motor1['zps.sz'] = zps.sz
        motor1['zps.pi_r'] = zps.pi_r
        motor1['DetU.x'] = DetU.x
        motor1['DetU.y'] = DetU.y
        motor1['DetU.z'] = DetU.z

        motor2['clens.x'] = clens.x
        motor2['clens.y1'] = clens.y1
        motor2['clens.y2'] = clens.y2
        motor2['clens.z1'] = clens.z1
        motor2['clens.z2'] = clens.z2
        motor2['clens.p'] = clens.p
        motor2['zp.x'] = zp.x
        motor2['zp.y'] = zp.y
        motor2['zp.z'] = zp.z
        motor2['aper.x'] = aper.x
        motor2['aper.y'] = aper.y
        motor2['aper.z'] = aper.z

        motor3['ssa.v_gap'] = ssa.v_gap
        motor3['ssa.v_ctr'] = ssa.v_ctr
        motor3['ssa.h_gap'] = ssa.h_gap
        motor3['ssa.h_ctr'] = ssa.h_ctr
        motor3['filter1'] = filter1
        motor3['filter2'] = filter2
        motor3['filter3'] = filter3
        motor3['filter4'] = filter4

        motor4['cm.x'] = cm.x
        motor4['cm.yaw'] = cm.yaw
        motor4['cm.y'] = cm.y
        motor4['cm.p'] = cm.p
        motor4['cm.r'] = cm.r
        motor4['tm.x'] = tm.x
        motor4['tm.yaw'] = tm.yaw
        motor4['tm.y'] = tm.y
        motor4['tm.p'] = tm.p
        motor4['tm.r'] = tm.r

        motor5['pbsl.x_gap'] = pbsl.x_gap
        motor5['pbsl.x_ctr'] = pbsl.x_ctr
        motor5['pbsl.y_gap'] = pbsl.y_gap
        motor5['pbsl.y_ctr'] = pbsl.y_ctr
        motor5['dcm.eng'] = dcm.eng
        motor5['dcm.th1'] = dcm.th1
        motor5['dcm.th2'] = dcm.th2
        motor5['dcm.dy2'] = dcm.dy2
        motor5['dcm.chi2'] = dcm.chi2

        motor6['pzt_dcm_chi2.pos'] = pzt_dcm_chi2.pos
        motor6['pzt_dcm_th2.pos'] = pzt_dcm_th2.pos
        motor6['pzt_cm_loadcell'] = pzt_cm_loadcell
        motor6['pzt_tm_loadcell'] = pzt_tm_loadcell

        motor7['ic3'] = ic3
        motor7['ic4'] = ic4
    except Exception as err:
        print(err)

    if n == 1:
        return motor1
    elif n == 2:
        return motor2
    elif n == 3:
        return motor3
    elif n == 4:
        return motor4
    elif n == 5:
        return motor5
    elif n == 6:
        return motor6
    elif n == 7:
        return motor7
    else:
        return 0


def make_jupyter_widget_with_kernel():
    """Start a kernel, connect to it, and create a RichJupyterWidget to use it
    """
    kernel_manager = QtKernelManager(kernel_name='python3')
    kernel_manager.start_kernel()

    kernel_client = kernel_manager.client()
    kernel_client.start_channels()

    jupyter_widget = RichJupyterWidget()
    jupyter_widget.kernel_manager = kernel_manager
    jupyter_widget.kernel_client = kernel_client
    return jupyter_widget


class ConsoleWidget(RichIPythonWidget):
    def __init__(self, namespace={}, customBanner=None, *args, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)

        if customBanner is not None:
            self.banner = customBanner

        #self.set_default_style('linux')
        #self.font_size = 20
 
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel(show_banner=False)

        self.kernel = self.kernel_manager.kernel        
        self.kernel.gui = 'qt'

        self.kernel_client = kernel_client = self._kernel_manager.client()
        self.kernel_client.start_channels()
        
        #self.push_vars(namespace)
        #kernel.shell.push({'foo': 43, 'print_process_id': print_process_id})
        #fn = '/home/gemy/.ipython/profile_default/startup/00.py'
        #kernel.shell.safe_execfile(fn, kernel.shell.user_global_ns)  
        #print(fn)
        
        '''
        self.set_default_style('linux')
        self.font = QtGui.QFont(self.font.family(), 16);
        '''
        
        def stop():
            self.kernel_client.stop_channels()
            self.kernel_manager.shutdown_kernel()
            guisupport.get_app_qt().exit()

        self.exit_requested.connect(stop)


    def execfile(self, fn):
        self.kernel.shell.safe_execfile(fn, self.kernel.shell.user_global_ns)

    def push_vars(self, variableDict):
        """
        Given a dictionary containing name / value pairs, push those variables
        to the Jupyter console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clear(self):
        """
        Clears the terminal
        """
        self._control.clear()

        # self.kernel_manager

    def print_text(self, text):
        """
        Prints some plain text to the console
        """
        self._append_plain_text(text)

    def execute_command(self, command):
        """
        Execute a command in the frame of the console widget
        """
        self._execute(command, False)


class Xyze_motor(QObject):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj
    def run(self):
        x = zps.sx.position
        y = zps.sy.position
        z = zps.sz.position
        r = zps.pi_r.position
        eng = XEng.position
        self.obj.lb_motor_pos_x.setText(f'{x:5.4f}')
        self.obj.lb_motor_pos_y.setText(f'{y:5.4f}')
        self.obj.lb_motor_pos_z.setText(f'{z:5.4f}')
        self.obj.lb_motor_pos_r.setText(f'{r:5.4f}')
        self.obj.lb_motor_pos_e.setText(f'{eng:2.5f}')
        time.sleep(0.2)


class Beam_current_status(QObject):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj
    def run(self):
        beam_value = beam_current.read()['beam_current']['value']
        shutter_value = shutter_status.read()['shutter_status']['value']
        if shutter_value == 1:
            sh_status = 'Closed' 
            stylesheet = 'color: rgb(200, 50, 50)' # display red
        else:
            sh_status = 'Open' 
            stylesheet = 'color: rgb(50, 200, 50)' # display green
        self.obj.lb_beam_current.setText(f'{beam_value:3.1f} mA')
        self.obj.lb_shutter_status.setText(sh_status)
        self.obj.lb_shutter_status.setStyleSheet(stylesheet)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'TXM Control'
        screen_resolution = QApplication.desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        self.width = 1020
        self.height = 800
        self.left = (width - self.width) // 2
        self.top = (height - self.height) // 2
        self.initUI()
        self.global_sync()
        self.beam_shutter_sync()
        self.display_calib_eng_only()

    '''
    def global_sync(self):
        thread = threading.Thread(target=self.repeat_pos_sync, args=())
        thread.daemon = True
        thread.start()
    '''
    def global_sync(self):
        self.thread_pos = QThread()
        self.xyze_motor = Xyze_motor(obj=self)
        self.xyze_motor.moveToThread(self.thread_pos)        
        self.thread_pos.started.connect(self.xyze_motor.run)
        self.thread_pos.start()

    def beam_shutter_sync(self):
        self.thread_beam_shutter = QThread()
        self.beam_current_status = Beam_current_status(obj=self)
        self.beam_current_status.moveToThread(self.thread_beam_shutter)        
        self.thread_beam_shutter.started.connect(self.beam_current_status.run)
        self.thread_beam_shutter.start()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.font1 = QtGui.QFont('Arial', 12, QtGui.QFont.Bold)
        self.font2 = QtGui.QFont('Arial', 12, QtGui.QFont.Normal)
        self.fpath = os.getcwd()
        self.pos = {}
        self.sample_pos = {}
        self.scan_name = ''
        self.pos_num = 0
        self.txm_eng_list = {}
        self.txm_scan = {}
        self.txm_record_scan = {}
        self.fn_calib_eng_file = "/nsls2/data/fxi-new/legacy/log/calib_new.csv"
        self.fpath_bluesky_startup = '/nsls2/data/fxi-new/shared/config/bluesky/profile_collection/startup'
        self.timestamp_cache_for_calib_eng_file = os.stat(self.fn_calib_eng_file)
        grid = QGridLayout()
        # gpbox_prep = self.layout_GP_prepare()
        # gpbox_msg = self.layout_msg()
        # gpbox_xanes = self.layout_xanes()

        #
        grid.addWidget(self.layout_motor(), 0, 1)
        grid.addWidget(self.layout_instruction(), 1, 1)
        grid.addWidget(self.layout_scan(), 2, 1)
        # grid.addLayout(gpbox_msg, 1, 1)
        # grid.addWidget(gpbox_xanes, 2, 1)

        layout = QVBoxLayout()
        layout.addLayout(grid)
        layout.addStretch()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.pos_sync()

    def layout_instruction(self):
        gpbox = QGroupBox()
        gpbox.setTitle("Instruction")
        gpbox.setFont(self.font1)
        gpbox.setStyleSheet('background-color: rgb(250, 250, 220);')
        lb_1 = QLabel()
        lb_1.setFont(self.font2)
        lb_1.setText('Type 1 (single scan): choose "scan type" -> '
                     'input parameters (load and select "Energy list" if needed) ->' 
                     '"check scan" -> "Run"')
        lb_2 = QLabel()
        lb_2.setFont(self.font2)
        lb_2.setText('Type 2 (multi scans): after "check scan" -> '
                     '"record" (beside "Recorded scan") -> choose "Operators" -> '
                     '"assemble" (beside "Assembled scan") -> "Run"')
        vbox = QVBoxLayout()
        vbox.addWidget(lb_1)
        vbox.addWidget(lb_2)
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignTop)
        gpbox.setLayout(vbox)
        return gpbox

    def layout_motor(self):
        lb_empty = QLabel()
        lb_empty.setFixedWidth(40)
        lb_empty1 = QLabel()
        lb_empty1.setFixedWidth(40)
        lb_empty2 = QLabel()
        lb_empty2.setFixedWidth(40)
        gpbox = QGroupBox('Sample position')
        gpbox.setFont(self.font1)
        #gpbox.setStyleSheet('color: rgb(0, 80, 255);')
        hbox_motor = QHBoxLayout()
        hbox_motor.addLayout(self.vbox_motor_pos())
        hbox_motor.addWidget(lb_empty)
        #hbox_motor.addLayout(self.vbox_motor_step())
        hbox_motor.addLayout(self.vbox_pos_list())
        hbox_motor.addWidget(lb_empty)

        hbox_motor.addLayout(self.vbox_pos_select_for_scan())
        hbox_motor.addWidget(lb_empty2)

        hbox_motor.addLayout(self.vbox_beam_shutter())
        hbox_motor.setAlignment(QtCore.Qt.AlignLeft)
        hbox_motor.addStretch()
        vbox_motor = QVBoxLayout()
        vbox_motor.addLayout(hbox_motor)
        # vbox_motor.addWidget(lb_empty2)
        vbox_motor.setAlignment(QtCore.Qt.AlignTop)
        gpbox.setLayout(vbox_motor)
        return gpbox

    def vbox_motor_pos(self):
        lb_title = QLabel()
        lb_title.setFixedWidth(120)
        lb_title.setText('TXM motors')
        lb_title.setFont(self.font1)

        self.pb_pos_sync = QPushButton('Sync. CSS pos. / update energy calib.')
        self.pb_pos_sync.setFixedWidth(350)
        self.pb_pos_sync.setFont(self.font2)
        self.pb_pos_sync.clicked.connect(self.pos_sync)

        self.pb_reset_rot_speed = QPushButton('Reset rotation speed to 30 deg/s')
        self.pb_reset_rot_speed.setFixedWidth(350)
        self.pb_reset_rot_speed.setFont(self.font2)
        self.pb_reset_rot_speed.clicked.connect(self.reset_r_speed)

        hbox = QHBoxLayout()
        hbox.addWidget(self.pb_pos_sync)
        hbox.addWidget(self.pb_reset_rot_speed)
        hbox.addStretch()
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        layout_motor_x = self.hbox_motor_x()
        layout_motor_y = self.hbox_motor_y()
        layout_motor_z = self.hbox_motor_z()
        layout_motor_r = self.hbox_motor_r()
        layout_motor_e = self.hbox_motor_e()
        vbox_motor_pos = QVBoxLayout()
        vbox_motor_pos.addWidget(lb_title)
        vbox_motor_pos.addLayout(layout_motor_x)
        vbox_motor_pos.addLayout(layout_motor_y)
        vbox_motor_pos.addLayout(layout_motor_z)
        vbox_motor_pos.addLayout(layout_motor_r)
        vbox_motor_pos.addLayout(layout_motor_e)
        vbox_motor_pos.addLayout(hbox)
        vbox_motor_pos.setAlignment(QtCore.Qt.AlignTop)
        return vbox_motor_pos

    def vbox_motor_step(self):
        lb_title = QLabel()
        lb_title.setFixedWidth(200)
        lb_title.setText('step size (x, y, z)')
        lb_title.setFont(self.font1)
        lb_title2 = QLabel()
        lb_title2.setFixedWidth(80)
        lb_title2.setText('     r step')
        lb_title2.setFont(self.font2)

        self.rd_step_10nm = QRadioButton('10 nm')
        self.rd_step_10nm.setFixedWidth(80)
        self.rd_step_10nm.setFont(self.font2)
        self.rd_step_100nm = QRadioButton('100 nm')
        self.rd_step_100nm.setFixedWidth(80)
        self.rd_step_100nm.setFont(self.font2)
        self.rd_step_1um = QRadioButton('1 um')
        self.rd_step_1um.setFixedWidth(80)
        self.rd_step_1um.setFont(self.font2)
        self.rd_step_5um = QRadioButton('5 um')
        self.rd_step_5um.setFixedWidth(80)
        self.rd_step_5um.setFont(self.font2)
        self.rd_step_20um = QRadioButton('20 um')
        self.rd_step_20um.setFixedWidth(80)
        self.rd_step_20um.setFont(self.font2)
        self.rd_step_50um = QRadioButton('50 um')
        self.rd_step_50um.setFixedWidth(80)
        self.rd_step_50um.setFont(self.font2)
        self.rd_step_200um = QRadioButton('200 um')
        self.rd_step_200um.setFixedWidth(80)
        self.rd_step_200um.setFont(self.font2)
        self.rd_step_1mm = QRadioButton('1 mm')
        self.rd_step_1mm.setFixedWidth(80)
        self.rd_step_1mm.setFont(self.font2)
        self.rd_step_custom = QRadioButton('custom')
        self.rd_step_custom.setFixedWidth(80)
        self.rd_step_custom.setFont(self.font2)

        self.rd_step_20um.setChecked(True)

        self.tx_step_custom = QLineEdit()
        self.tx_step_custom.setFont(self.font2)
        self.tx_step_custom.setText('100')
        self.tx_step_custom.setFixedWidth(60)
        self.tx_step_custom.setValidator(QDoubleValidator())
        lb_step_custom_unit = QLabel()
        lb_step_custom_unit.setFont(self.font2)
        lb_step_custom_unit.setText('um')
        lb_step_custom_unit.setFixedWidth(80)

        self.rd_rot_step_custom = QRadioButton('custom')
        self.rd_rot_step_custom.setFixedWidth(80)
        self.rd_rot_step_custom.setFont(self.font2)
        self.tx_rot_step_custom = QLineEdit()
        self.tx_rot_step_custom.setFont(self.font2)
        self.tx_rot_step_custom.setText('90')
        self.tx_rot_step_custom.setFixedWidth(60)
        self.tx_rot_step_custom.setValidator(QDoubleValidator())
        lb_rot_step_custom_unit = QLabel()
        lb_rot_step_custom_unit.setFont(self.font2)
        lb_rot_step_custom_unit.setText('deg')
        lb_rot_step_custom_unit.setFixedWidth(80)

        self.step_size_group = QButtonGroup()
        self.step_size_group.setExclusive(True)
        self.step_size_group.addButton(self.rd_step_10nm)
        self.step_size_group.addButton(self.rd_step_100nm)
        self.step_size_group.addButton(self.rd_step_1um)
        self.step_size_group.addButton(self.rd_step_5um)
        self.step_size_group.addButton(self.rd_step_20um)
        self.step_size_group.addButton(self.rd_step_50um)
        self.step_size_group.addButton(self.rd_step_200um)
        self.step_size_group.addButton(self.rd_step_1mm)
        self.step_size_group.addButton(self.rd_step_custom)

        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(self.rd_step_10nm)
        hbox_1.addWidget(self.rd_step_100nm)
        hbox_1.setAlignment(QtCore.Qt.AlignLeft)
        hbox_2 = QHBoxLayout()
        hbox_2.addWidget(self.rd_step_1um)
        hbox_2.addWidget(self.rd_step_5um)
        hbox_2.setAlignment(QtCore.Qt.AlignLeft)
        hbox_3 = QHBoxLayout()
        hbox_3.addWidget(self.rd_step_20um)
        hbox_3.addWidget(self.rd_step_50um)
        hbox_3.setAlignment(QtCore.Qt.AlignLeft)
        hbox_4 = QHBoxLayout()
        hbox_4.addWidget(self.rd_step_200um)
        hbox_4.addWidget(self.rd_step_1mm)
        hbox_4.setAlignment(QtCore.Qt.AlignLeft)
        hbox_5 = QHBoxLayout()
        hbox_5.addWidget(self.rd_step_custom)
        hbox_5.addWidget(self.tx_step_custom)
        hbox_5.addWidget(lb_step_custom_unit)
        hbox_5.setAlignment(QtCore.Qt.AlignLeft)
        hbox_6 = QHBoxLayout()
        hbox_6.addWidget(lb_title2)
        hbox_6.addWidget(self.tx_rot_step_custom)
        hbox_6.addWidget(lb_rot_step_custom_unit)
        hbox_6.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_title)
        vbox.addLayout(hbox_1)
        vbox.addLayout(hbox_2)
        vbox.addLayout(hbox_3)
        vbox.addLayout(hbox_4)
        vbox.addLayout(hbox_5)
        vbox.addLayout(hbox_6)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        return vbox

    def hbox_motor_x(self):
        # lb_empty = QLabel()
        # lb_empty.setFixedWidth(10)
        lb_motor = QLabel()
        lb_motor.setFixedWidth(70)
        lb_motor.setText('piezo x:')
        lb_motor.setFont(self.font2)

        self.tx_setpos_x = QLineEdit()
        self.tx_setpos_x.setFont(self.font2)
        self.tx_setpos_x.setFixedWidth(100)
        self.tx_setpos_x.setValidator(QDoubleValidator())
        self.tx_setpos_x.returnPressed.connect(lambda: self.move_to_pos('x'))

        self.lb_limit_x = QLabel()
        self.lb_limit_x.setFixedWidth(120)
        self.lb_limit_x.setText('(-4000, 4000)')
        self.lb_limit_x.setFont(self.font2)

        lb_unit = QLabel()
        lb_unit.setText('um')
        lb_unit.setFont(self.font2)
        lb_unit.setFixedWidth(50)
        lb_unit2 = QLabel()
        lb_unit2.setText('um')
        lb_unit2.setFont(self.font2)
        lb_unit2.setFixedWidth(50)
        lb_unit3 = QLabel()
        lb_unit3.setText('um')
        lb_unit3.setFont(self.font2)
        lb_unit3.setFixedWidth(30)

        self.lb_motor_pos_x = QLabel()
        self.lb_motor_pos_x.setFixedWidth(80)
        self.lb_motor_pos_x.setText('0')
        self.lb_motor_pos_x.setFont(self.font2)
        pb_motor_minus = QPushButton('-')
        pb_motor_minus.setFixedWidth(40)
        pb_motor_minus.setFont(self.font2)
        pb_motor_minus.clicked.connect(lambda: self.move_motor_negative('x'))
        pb_motor_plus = QPushButton('+')
        pb_motor_plus.setFixedWidth(40)
        pb_motor_plus.setFont(self.font2)
        pb_motor_plus.clicked.connect(lambda: self.move_motor_positive('x'))

        self.tx_step_x = QLineEdit()
        self.tx_step_x.setFont(self.font2)
        self.tx_step_x.setFixedWidth(80)
        self.tx_step_x.setText('0')
        self.tx_step_x.setValidator(QDoubleValidator())      

        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.lb_motor_pos_x)
        hbox.addWidget(lb_unit)
        hbox.addWidget(self.tx_setpos_x)
        hbox.addWidget(lb_unit2)
        hbox.addWidget(self.lb_limit_x)
        hbox.addWidget(pb_motor_minus)
        hbox.addWidget(self.tx_step_x)
        hbox.addWidget(lb_unit3)
        hbox.addWidget(pb_motor_plus)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

    def hbox_motor_y(self):
        # lb_empty = QLabel()
        # lb_empty.setFixedWidth(10)
        lb_motor = QLabel()
        lb_motor.setFixedWidth(70)
        lb_motor.setText('piezo y:')
        lb_motor.setFont(self.font2)

        self.tx_setpos_y = QLineEdit()
        self.tx_setpos_y.setFont(self.font2)
        self.tx_setpos_y.setFixedWidth(100)
        self.tx_setpos_y.returnPressed.connect(lambda: self.move_to_pos('y'))
        self.tx_setpos_y.setValidator(QDoubleValidator())

        self.lb_limit_y = QLabel()
        self.lb_limit_y.setFixedWidth(120)
        self.lb_limit_y.setText('(-2000, 4000)')
        self.lb_limit_y.setFont(self.font2)

        lb_unit = QLabel()
        lb_unit.setText('um')
        lb_unit.setFont(self.font2)
        lb_unit.setFixedWidth(50)
        lb_unit2 = QLabel()
        lb_unit2.setText('um')
        lb_unit2.setFont(self.font2)
        lb_unit2.setFixedWidth(50)
        lb_unit3 = QLabel()
        lb_unit3.setText('um')
        lb_unit3.setFont(self.font2)
        lb_unit3.setFixedWidth(30)

        self.lb_motor_pos_y = QLabel()
        self.lb_motor_pos_y.setFixedWidth(80)
        self.lb_motor_pos_y.setText('0')
        self.lb_motor_pos_y.setFont(self.font2)
        pb_motor_minus = QPushButton('-')
        pb_motor_minus.setFixedWidth(40)
        pb_motor_minus.setFont(self.font2)
        pb_motor_minus.clicked.connect(lambda: self.move_motor_negative('y'))
        pb_motor_plus = QPushButton('+')
        pb_motor_plus.setFixedWidth(40)
        pb_motor_plus.setFont(self.font2)
        pb_motor_plus.clicked.connect(lambda: self.move_motor_positive('y'))

        self.tx_step_y = QLineEdit()
        self.tx_step_y.setFont(self.font2)
        self.tx_step_y.setFixedWidth(80)
        self.tx_step_y.setText('0')
        self.tx_step_y.setValidator(QDoubleValidator())   

        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.lb_motor_pos_y)
        hbox.addWidget(lb_unit)
        hbox.addWidget(self.tx_setpos_y)
        hbox.addWidget(lb_unit2)
        hbox.addWidget(self.lb_limit_y)
        hbox.addWidget(pb_motor_minus)
        hbox.addWidget(self.tx_step_y)
        hbox.addWidget(lb_unit3)
        hbox.addWidget(pb_motor_plus)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

    def hbox_motor_z(self):
        # lb_empty = QLabel()
        # lb_empty.setFixedWidth(10)
        lb_motor = QLabel()
        lb_motor.setFixedWidth(70)
        lb_motor.setText('piezo z:')
        lb_motor.setFont(self.font2)

        self.tx_setpos_z = QLineEdit()
        self.tx_setpos_z.setFont(self.font2)
        self.tx_setpos_z.setFixedWidth(100)
        self.tx_setpos_z.returnPressed.connect(lambda: self.move_to_pos('z'))
        self.tx_setpos_z.setValidator(QDoubleValidator())

        self.lb_limit_z = QLabel()
        self.lb_limit_z.setFixedWidth(120)
        self.lb_limit_z.setText('(-2000, 2000)')
        self.lb_limit_z.setFont(self.font2)

        lb_unit = QLabel()
        lb_unit.setText('um')
        lb_unit.setFont(self.font2)
        lb_unit.setFixedWidth(50)
        lb_unit2 = QLabel()
        lb_unit2.setText('um')
        lb_unit2.setFont(self.font2)
        lb_unit2.setFixedWidth(50)
        lb_unit3 = QLabel()
        lb_unit3.setText('um')
        lb_unit3.setFont(self.font2)
        lb_unit3.setFixedWidth(30)

        self.lb_motor_pos_z = QLabel()
        self.lb_motor_pos_z.setFixedWidth(80)
        self.lb_motor_pos_z.setText('0')
        self.lb_motor_pos_z.setFont(self.font2)
        pb_motor_minus = QPushButton('-')
        pb_motor_minus.setFont(self.font2)
        pb_motor_minus.setFixedWidth(40)
        pb_motor_minus.clicked.connect(lambda: self.move_motor_negative('z'))
        pb_motor_plus = QPushButton('+')
        pb_motor_plus.setFont(self.font2)
        pb_motor_plus.setFixedWidth(40)
        pb_motor_plus.clicked.connect(lambda: self.move_motor_positive('z'))

        self.tx_step_z = QLineEdit()
        self.tx_step_z.setFont(self.font2)
        self.tx_step_z.setFixedWidth(80)
        self.tx_step_z.setText('0')
        self.tx_step_z.setValidator(QDoubleValidator())   

        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.lb_motor_pos_z)
        hbox.addWidget(lb_unit)
        hbox.addWidget(self.tx_setpos_z)
        hbox.addWidget(lb_unit2)
        hbox.addWidget(self.lb_limit_z)
        hbox.addWidget(pb_motor_minus)
        hbox.addWidget(self.tx_step_z)
        hbox.addWidget(lb_unit3)
        hbox.addWidget(pb_motor_plus)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

    def hbox_motor_r(self):
        # lb_empty = QLabel()
        # lb_empty.setFixedWidth(10)
        lb_motor = QLabel()
        lb_motor.setFixedWidth(70)
        lb_motor.setText('rotary r:')
        lb_motor.setFont(self.font2)

        self.tx_setpos_r = QLineEdit()
        self.tx_setpos_r.setFont(self.font2)
        self.tx_setpos_r.setFixedWidth(100)
        self.tx_setpos_r.setValidator(QDoubleValidator())
        self.tx_setpos_r.returnPressed.connect(lambda: self.move_to_pos('r'))

        self.lb_limit_r = QLabel()
        self.lb_limit_r.setFixedWidth(120)
        self.lb_limit_r.setText('(-180, 180)')
        self.lb_limit_r.setFont(self.font2)

        lb_unit = QLabel()
        lb_unit.setText('deg')
        lb_unit.setFont(self.font2)
        lb_unit.setFixedWidth(50)

        lb_unit2 = QLabel()
        lb_unit2.setText('deg')
        lb_unit2.setFont(self.font2)
        lb_unit2.setFixedWidth(50)

        lb_unit3 = QLabel()
        lb_unit3.setText('deg')
        lb_unit3.setFont(self.font2)
        lb_unit3.setFixedWidth(30)

        self.lb_motor_pos_r = QLabel()
        self.lb_motor_pos_r.setFixedWidth(80)
        self.lb_motor_pos_r.setText('0')
        self.lb_motor_pos_r.setFont(self.font2)
        pb_motor_minus = QPushButton('-')
        pb_motor_minus.setFont(self.font2)
        pb_motor_minus.setFixedWidth(40)
        pb_motor_minus.clicked.connect(lambda: self.move_motor_negative('r'))
        pb_motor_plus = QPushButton('+')
        pb_motor_plus.setFont(self.font2)
        pb_motor_plus.setFixedWidth(40)
        pb_motor_plus.clicked.connect(lambda: self.move_motor_positive('r'))

        self.tx_step_r = QLineEdit()
        self.tx_step_r.setFont(self.font2)
        self.tx_step_r.setFixedWidth(80)
        self.tx_step_r.setText('0')
        self.tx_step_r.setValidator(QDoubleValidator())   

        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.lb_motor_pos_r)
        hbox.addWidget(lb_unit)
        hbox.addWidget(self.tx_setpos_r)
        hbox.addWidget(lb_unit2)
        hbox.addWidget(self.lb_limit_r)
        hbox.addWidget(pb_motor_minus)
        hbox.addWidget(self.tx_step_r)
        hbox.addWidget(lb_unit3)
        hbox.addWidget(pb_motor_plus)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

    def hbox_motor_e(self):
        # lb_empty = QLabel()
        # lb_empty.setFixedWidth(10)
        lb_motor = QLabel()
        lb_motor.setFixedWidth(70)
        lb_motor.setText('XEng:')
        lb_motor.setFont(self.font2)

        self.tx_setpos_e = QLineEdit()
        self.tx_setpos_e.setFont(self.font2)
        self.tx_setpos_e.setFixedWidth(100)
        self.tx_setpos_e.setValidator(QDoubleValidator())
        self.tx_setpos_e.returnPressed.connect(self.move_to_energy)

        lb_unit = QLabel()
        lb_unit.setText('keV')
        lb_unit.setFont(self.font2)
        lb_unit.setFixedWidth(50)

        lb_unit2 = QLabel()
        lb_unit2.setText('keV')
        lb_unit2.setFont(self.font2)
        lb_unit2.setFixedWidth(50)

        self.lb_note = QLabel()
        self.lb_note.setFixedWidth(300)
        self.lb_note.setText('(calib. pos)')
        self.lb_note.setFont(self.font2)

        self.lb_motor_pos_e = QLabel()
        self.lb_motor_pos_e.setFixedWidth(80)
        self.lb_motor_pos_e.setText('0')
        self.lb_motor_pos_e.setFont(self.font2)
        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.lb_motor_pos_e)
        hbox.addWidget(lb_unit)
        hbox.addWidget(self.tx_setpos_e)
        hbox.addWidget(lb_unit2)
        hbox.addWidget(self.lb_note)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

    def vbox_pos_select_for_scan(self):
        lb_pos = QLabel()
        lb_pos.setFixedWidth(200)
        lb_pos.setText('Position used in scan')
        lb_pos.setFont(self.font1)
        lb_pos.setStyleSheet('color: rgb(0, 80, 255)')

        self.lst_scan_pos = QListWidget()
        self.lst_scan_pos.setFixedWidth(100)
        self.lst_scan_pos.setFixedHeight(120)
        self.lst_scan_pos.setFont(self.font2)
        #self.lst_scan_pos.itemClicked.connect(self.show_pos_clicked)
        #self.lst_scan_pos.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_pos_rm_select = QPushButton('remove')
        self.pb_pos_rm_select.setFixedWidth(100)
        self.pb_pos_rm_select.setFont(self.font2)
        self.pb_pos_rm_select.clicked.connect(self.pos_remove_select)

        self.pb_pos_rm_all_select = QPushButton('remove all')
        self.pb_pos_rm_all_select.setFixedWidth(100)
        self.pb_pos_rm_all_select.setFont(self.font2)
        self.pb_pos_rm_all_select.clicked.connect(self.pos_remove_all_select)

        lb_note1 = QLabel()
        lb_note1.setText('1. if empty, use current pos.')
        lb_note1.setFont(self.font2)
        lb_note1.setFixedWidth(210)
        lb_note1.setFixedHeight(30)

        lb_note2 = QLabel()
        lb_note2.setText('2. Bkg. is automatically added')
        lb_note2.setFont(self.font2)
        lb_note1.setFixedWidth(210)

        vbox_select = QVBoxLayout()
        vbox_select.addWidget(self.pb_pos_rm_select)
        vbox_select.addWidget(self.pb_pos_rm_all_select)
        vbox_select.setAlignment(QtCore.Qt.AlignTop)

        hbox = QHBoxLayout()
        hbox.addWidget(self.lst_scan_pos)
        hbox.addLayout(vbox_select)        
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_pos)
        vbox.addLayout(hbox)
        vbox.addWidget(lb_note1)
        vbox.addWidget(lb_note2)
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignTop)

        return vbox
       

    def vbox_pos_list(self):
        lb_pos = QLabel()
        lb_pos.setFixedWidth(160)
        lb_pos.setText('Position saved')
        lb_pos.setFont(self.font1)

        lb_pos_x = QLabel()
        lb_pos_x.setText('x:')
        lb_pos_x.setFont(self.font2)
        lb_pos_x.setFixedWidth(20)
        self.lb_pos_x = QLabel()
        self.lb_pos_x.setFont(self.font2)
        self.lb_pos_x.setFixedWidth(75)

        lb_pos_y = QLabel()
        lb_pos_y.setText('y:')
        lb_pos_y.setFont(self.font2)
        lb_pos_y.setFixedWidth(20)
        self.lb_pos_y = QLabel()
        self.lb_pos_y.setFont(self.font2)
        self.lb_pos_y.setFixedWidth(75)

        lb_pos_z = QLabel()
        lb_pos_z.setText('z:')
        lb_pos_z.setFont(self.font2)
        lb_pos_z.setFixedWidth(20)
        self.lb_pos_z = QLabel()
        self.lb_pos_z.setText('')
        self.lb_pos_z.setFont(self.font2)
        self.lb_pos_z.setFixedWidth(75)

        lb_pos_r = QLabel()
        lb_pos_r.setText('r:')
        lb_pos_r.setFont(self.font2)
        lb_pos_r.setFixedWidth(20)
        self.lb_pos_r = QLabel()
        self.lb_pos_r.setFont(self.font2)
        self.lb_pos_r.setFixedWidth(75)

        hbox_pos1 = QHBoxLayout()
        hbox_pos1.addWidget(lb_pos_x)
        hbox_pos1.addWidget(self.lb_pos_x)
        hbox_pos1.addWidget(lb_pos_y)
        hbox_pos1.addWidget(self.lb_pos_y)
        hbox_pos1.setAlignment(QtCore.Qt.AlignLeft)

        hbox_pos2 = QHBoxLayout()
        hbox_pos2.addWidget(lb_pos_z)
        hbox_pos2.addWidget(self.lb_pos_z)
        hbox_pos2.addWidget(lb_pos_r)
        hbox_pos2.addWidget(self.lb_pos_r)
        hbox_pos2.setAlignment(QtCore.Qt.AlignLeft)

        self.lst_pos = QListWidget()
        self.lst_pos.setFixedWidth(100)
        self.lst_pos.setFixedHeight(180)
        self.lst_pos.setFont(self.font2)
        self.lst_pos.itemClicked.connect(self.show_pos_clicked)
        self.lst_pos.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_pos_rec = QPushButton('record')
        self.pb_pos_rec.setFixedWidth(100)
        self.pb_pos_rec.setFont(self.font2)
        self.pb_pos_rec.clicked.connect(self.pos_record)

        self.pb_pos_out = QPushButton('bkg. pos')
        self.pb_pos_out.setFixedWidth(100)
        self.pb_pos_out.setFont(self.font2)
        self.pb_pos_out.clicked.connect(self.pos_record_bkg)

        self.pb_pos_rm = QPushButton('remove')
        self.pb_pos_rm.setFixedWidth(100)
        self.pb_pos_rm.setFont(self.font2)
        self.pb_pos_rm.clicked.connect(self.pos_remove)

        self.pb_pos_rm_all = QPushButton('remove all')
        self.pb_pos_rm_all.setFixedWidth(100)
        self.pb_pos_rm_all.setFont(self.font2)
        self.pb_pos_rm_all.clicked.connect(self.pos_remove_all)

        self.pb_pos_update = QPushButton('update')
        self.pb_pos_update.setFixedWidth(100)
        self.pb_pos_update.setFont(self.font2)
        self.pb_pos_update.clicked.connect(self.pos_update)

        self.pb_pos_go = QPushButton('Go To')
        self.pb_pos_go.setFixedWidth(100)
        self.pb_pos_go.setFont(self.font2)
        self.pb_pos_go.clicked.connect(self.pos_go_to)

        self.pb_pos_select = QPushButton('select for scan --->')
        self.pb_pos_select.setFixedWidth(205)
        self.pb_pos_select.setFont(self.font2)
        self.pb_pos_select.setStyleSheet('color: rgb(0, 80, 255)')
        self.pb_pos_select.clicked.connect(self.pos_select_for_scan)


        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.pb_pos_rec)
        hbox1.addWidget(self.pb_pos_out)
        hbox1.setAlignment(QtCore.Qt.AlignLeft)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.pb_pos_rm)
        hbox2.addWidget(self.pb_pos_rm_all)
        hbox2.setAlignment(QtCore.Qt.AlignLeft)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.pb_pos_update)
        hbox3.addWidget(self.pb_pos_go)
        hbox3.setAlignment(QtCore.Qt.AlignLeft)

        vbox_rec_go = QVBoxLayout()
        vbox_rec_go.addLayout(hbox1)
        vbox_rec_go.addLayout(hbox2)
        vbox_rec_go.addLayout(hbox3)
        vbox_rec_go.addWidget(self.pb_pos_select)
        vbox_rec_go.addLayout(hbox_pos1)
        vbox_rec_go.addLayout(hbox_pos2)
        vbox_rec_go.setAlignment(QtCore.Qt.AlignTop)

        hbox = QHBoxLayout()
        hbox.addWidget(self.lst_pos)
        hbox.addLayout(vbox_rec_go)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        vbox_lst = QVBoxLayout()
        vbox_lst.addWidget(lb_pos)
        vbox_lst.addLayout(hbox)
        vbox_lst.addStretch()
        vbox_lst.setAlignment(QtCore.Qt.AlignTop)
        return vbox_lst

    def vbox_beam_shutter(self):
        lb_beam = QLabel()
        lb_beam.setText('Beam current:')
        lb_beam.setFont(self.font1)
        lb_beam.setFixedWidth(120)
        
        self.lb_beam_current = QLabel()
        #self.lb_beam_current.setText('Beam current:')
        self.lb_beam_current.setFixedWidth(120)
        self.lb_beam_current.setFont(self.font1)
        self.lb_beam_current.setStyleSheet('color: rgb(200, 50, 50);')

        hbox_beam = QHBoxLayout()
        hbox_beam.addWidget(lb_beam)
        hbox_beam.addWidget(self.lb_beam_current)
        hbox_beam.setAlignment(QtCore.Qt.AlignLeft)

        lb_shutter = QLabel()
        lb_shutter.setText('Shutter status:')
        lb_shutter.setFixedHeight(40)
        lb_shutter.setFont(self.font1)
        lb_shutter.setFixedWidth(120)

        self.lb_shutter_status = QLabel()
        self.lb_shutter_status.setFixedWidth(120)
        self.lb_shutter_status.setFixedHeight(40)
        self.lb_shutter_status.setFont(self.font1)
        self.lb_shutter_status.setStyleSheet('color: rgb(200, 50, 50);')

        hbox_shutter = QHBoxLayout()
        hbox_shutter.addWidget(lb_shutter)
        hbox_shutter.addWidget(self.lb_shutter_status)
        hbox_shutter.setAlignment(QtCore.Qt.AlignLeft)

        self.pb_open_shutter = QPushButton("Open shutter")
        self.pb_open_shutter.setFont(self.font2)
        self.pb_open_shutter.setFixedHeight(40)
        self.pb_open_shutter.setFixedWidth(120)
        self.pb_open_shutter.clicked.connect(self.open_shutter)

        self.pb_close_shutter = QPushButton("Close shutter")
        self.pb_close_shutter.setFont(self.font2)
        self.pb_close_shutter.setFixedHeight(40)
        self.pb_close_shutter.setFixedWidth(120)
        self.pb_close_shutter.clicked.connect(self.close_shutter)

        vbox_shutter_click = QVBoxLayout()
        vbox_shutter_click.addWidget(self.pb_open_shutter)
        vbox_shutter_click.addWidget(self.pb_close_shutter)
        vbox_shutter_click.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_beam)
        vbox.addLayout(hbox_shutter)
        vbox.addLayout(vbox_shutter_click)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox



    #############################

    def layout_scan(self):
        lb_empty = QLabel()
        lb_empty.setFixedHeight(200)
        gpbox = QGroupBox('TXM scan')
        gpbox.setFont(self.font1)
        #gpbox.setStyleSheet('QGroupBox: title {color: rgb(0, 80, 255);}')

        tabs = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()

        lay1 = QVBoxLayout()
        lay1.addLayout(self.layout_pre_defined_scan())
        tab1.setLayout(lay1)

        lay2 = QVBoxLayout()
        #lay2.addLayout(self.hbox_optics_1())
        lay2.addLayout(self.vbox_optics())
        tab2.setLayout(lay2)

        tabs.addTab(tab1, 'Pre-defined scan')
        tabs.addTab(tab2, 'Advanced')
        vbox = QVBoxLayout()
        vbox.addWidget(tabs)
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignTop)
        gpbox.setLayout(vbox)
        gpbox.setAlignment(QtCore.Qt.AlignTop)
        return gpbox

    def layout_pre_defined_scan(self):
        lb_space1 = QLabel()
        lb_space1.setFixedWidth(20)

        lb_space2 = QLabel()
        lb_space2.setFixedWidth(10)

        lb_space3 = QLabel()
        lb_space3.setFixedWidth(10)

        lb_space4 = QLabel()
        lb_space4.setFixedWidth(10)

        lb_space5 = QLabel()
        lb_space5.setFixedWidth(10)

        lb_space6 = QLabel()
        lb_space6.setFixedWidth(10)

        lb_v_space1 = QLabel()
        lb_v_space1.setFixedHeight(10)

        sep = QLabel()
        sep.setFixedWidth(10)
        sep.setFixedHeight(180)
        #sep.setStyleSheet('background-color: rgb(0, 80, 255);')
        sep.setStyleSheet('background-color: rgb(0, 80, 255);')

        scan_cmd = self.vbox_scan_cmd()
        lst_pre_scan = self.vbox_lst_pre_defined_scan()
        lst_eng_list = self.vbox_eng_list()
        lst_record_scan = self.vbox_record_scan()
        scan_arg = self.layout_matrix_scan_argument()
        oper = self.vbox_operator()
        lst_assemble = self.vbox_assemble_scan()

        hbox_scan = QHBoxLayout()
        hbox_scan.addLayout(lst_pre_scan)
        hbox_scan.addWidget(lb_space1)
        hbox_scan.addLayout(lst_eng_list)
        hbox_scan.addWidget(lb_space2)
        hbox_scan.addLayout(lst_record_scan)
        hbox_scan.addWidget(lb_space3)
        # hbox_scan.addWidget(Separador_v)
        hbox_scan.addWidget(sep)
        hbox_scan.addWidget(lb_space4)
        hbox_scan.addLayout(oper)
        hbox_scan.addWidget(lb_space5)
        hbox_scan.addLayout(lst_assemble)

        hbox_scan.addStretch()
        hbox_scan.setAlignment(QtCore.Qt.AlignLeft)
        hbox_scan.addStretch()

        vbox_scan = QVBoxLayout()

        vbox_scan.addLayout(hbox_scan)
        vbox_scan.addWidget(lb_v_space1)
        vbox_scan.addLayout(scan_arg)
        vbox_scan.addLayout(scan_cmd)
        # vbox_scan.addLayout(custom_script)
        vbox_scan.setAlignment(QtCore.Qt.AlignTop)

        return vbox_scan

    def vbox_scan_cmd(self):
        self.lb_scan_msg = QLabel()
        self.lb_scan_msg.setFixedWidth(500)
        self.lb_scan_msg.setText("Scan command / Message:")
        self.lb_scan_msg.setFixedHeight(28)
        self.tx_scan_msg = QPlainTextEdit()
        self.tx_scan_msg.setFixedWidth(700)
        self.tx_scan_msg.setFixedHeight(240)
        self.tx_scan_msg.setFont(self.font2)

        tx_empty = QLineEdit()
        tx_empty.setVisible(False)
        tx_empty.setEnabled(False)
        
        lb_ipython_msg1 = QLabel()
        lb_ipython_msg1.setFont(self.font1)
        lb_ipython_msg1.setFixedWidth(450)        
        lb_ipython_msg1.setText('To initiate scan environment, run this command first:')

        lb_ipython_msg2 = QLabel()
        lb_ipython_msg2.setFont(self.font1)
        lb_ipython_msg2.setFixedWidth(450)
        lb_ipython_msg2.setText('If witch from GUI, before any scan, update scan-id by:')

        tx_ipython_msg1 = QLineEdit()
        tx_ipython_msg1.setFont(self.font2)
        tx_ipython_msg1.setFixedWidth(400)
        tx_ipython_msg1.setText('%run -i load_base.py')

        tx_ipython_msg2 = QLineEdit()
        tx_ipython_msg2.setFont(self.font2)
        tx_ipython_msg2.setFixedWidth(400)
        tx_ipython_msg2.setText('RE.md["scan_id"] = db[-1].start["scan_id"]')

        hbox_ipython1 = QHBoxLayout()
        hbox_ipython1.addWidget(lb_ipython_msg1)
        hbox_ipython1.addWidget(tx_ipython_msg1)
        hbox_ipython1.addStretch()
        hbox_ipython1.setAlignment(QtCore.Qt.AlignLeft)

        hbox_ipython2 = QHBoxLayout()
        hbox_ipython2.addWidget(lb_ipython_msg2)
        hbox_ipython2.addWidget(tx_ipython_msg2)
        hbox_ipython2.addStretch()
        hbox_ipython2.setAlignment(QtCore.Qt.AlignLeft)
    
        #self.ip_widget = ConsoleWidget()
        self.ip_widget = make_jupyter_widget_with_kernel()        
        self.ip_widget.setFixedWidth(900)
        self.ip_widget.setFixedHeight(300)
        self.ip_widget.set_default_style('linux')
        self.ip_widget.font = QtGui.QFont(self.ip_widget.font.family(), 12);
        
        #fn = '/home/mingyuan/Work/txm_control/00_base.py'
        #self.ip_widget.execfile(fn)
        hbox_run_sid = self.hbox_run_sid()
        hbox_scan_id = self.hbox_scan_id()

        hbox_commd_msg = QHBoxLayout()
        hbox_commd_msg.addWidget(self.lb_scan_msg)
        hbox_commd_msg.addWidget(tx_empty)
        hbox_commd_msg.setAlignment(QtCore.Qt.AlignLeft)
        hbox_commd_msg.addStretch()

        vbox1 = QVBoxLayout()
        vbox1.addLayout(hbox_commd_msg)
        vbox1.addLayout(hbox_scan_id)
        vbox1.addWidget(self.tx_scan_msg)
        vbox1.addLayout(hbox_run_sid)
        vbox1.addStretch()

        vbox2 = QVBoxLayout()
        vbox2.addLayout(hbox_ipython1)
        vbox2.addLayout(hbox_ipython2)
        vbox2.addWidget(self.ip_widget)
        vbox2.addStretch()

        hbox = QHBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)
        hbox.addStretch()
        #hbox.setAlignment(QtCore.Qt.AlignLeft)
        #vbox = QVBoxLayout()
        #vbox.addWidget(self.lb_scan_msg)
        #vbox.addLayout(hbox)
        #vbox.addWidget(self.ip_widget)
        
        #vbox.setAlignment(QtCore.Qt.AlignTop)
        return hbox

    def hbox_run_sid(self):
        lb_empty = QLabel()
        lb_empty.setFixedHeight(10)

        self.pb_run_scan = QPushButton('Run')
        self.pb_run_scan.setFont(self.font1)
        self.pb_run_scan.setFixedHeight(40)
        self.pb_run_scan.setFixedWidth(120)
        #self.pb_run_scan.setDisabled(True)
        self.pb_run_scan.setStyleSheet('color: rgb(200, 50, 50);')
        self.pb_run_scan.clicked.connect(self.run_scan)

        self.pb_pause_scan = QPushButton('Pause')
        self.pb_pause_scan.setFont(self.font1)
        self.pb_pause_scan.setFixedHeight(40)
        self.pb_pause_scan.setFixedWidth(80)
        self.pb_pause_scan.setStyleSheet('color: rgb(200, 200, 200)')
        self.pb_pause_scan.setEnabled(False)        
        self.pb_pause_scan.clicked.connect(self.run_pause)

        self.pb_resume_scan = QPushButton('Resume')
        self.pb_resume_scan.setFont(self.font1)
        self.pb_resume_scan.setFixedHeight(40)
        self.pb_resume_scan.setFixedWidth(80)
        self.pb_resume_scan.setStyleSheet('color: rgb(200, 200, 200);')
        self.pb_resume_scan.setEnabled(False)
        self.pb_resume_scan.clicked.connect(self.run_resume)

        self.pb_stop_scan = QPushButton('Stop')
        self.pb_stop_scan.setFont(self.font1)
        self.pb_stop_scan.setFixedHeight(40)
        self.pb_stop_scan.setFixedWidth(80)
        self.pb_stop_scan.setStyleSheet('color: rgb(200, 200, 200);')
        self.pb_stop_scan.setEnabled(False)
        self.pb_stop_scan.clicked.connect(self.run_stop)

        self.pb_abort_scan = QPushButton('Abort')
        self.pb_abort_scan.setFont(self.font1)
        self.pb_abort_scan.setFixedHeight(40)
        self.pb_abort_scan.setFixedWidth(80)
        self.pb_abort_scan.setStyleSheet('color: rgb(200, 200, 200);')
        self.pb_abort_scan.setEnabled(False)
        self.pb_abort_scan.clicked.connect(self.run_abort)

        hbox = QHBoxLayout()
        hbox.addWidget(self.pb_run_scan)
        hbox.addWidget(self.pb_pause_scan)
        hbox.addWidget(self.pb_resume_scan)
        hbox.addWidget(self.pb_stop_scan)
        hbox.addWidget(self.pb_abort_scan)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addStretch()

        return hbox

    def hbox_scan_id(self):
        lb_empty = QLabel()

        lb_sid = QLabel()
        lb_sid.setText('Latest scan ID:')
        lb_sid.setAlignment(QtCore.Qt.AlignLeft)
        lb_sid.setAlignment(QtCore.Qt.AlignVCenter)
        lb_sid.setFont(self.font1)
        lb_sid.setFixedWidth(120)

        self.lb_current_sid = QLabel()
        self.lb_current_sid.setText('')
        self.lb_current_sid.setFont(self.font1)
        self.lb_current_sid.setFixedWidth(80)
        self.lb_current_sid.setAlignment(QtCore.Qt.AlignLeft)
        self.lb_current_sid.setAlignment(QtCore.Qt.AlignVCenter)
        self.lb_current_sid.setStyleSheet('color: rgb(200, 50, 50);')

        self.tx_sid = QLineEdit()
        self.tx_sid.setFixedWidth(120)
        self.tx_sid.setFont(self.font2)
        self.tx_sid.setValidator(QIntValidator())

        self.pb_sid = QPushButton('Reset scan ID to:')
        self.pb_sid.clicked.connect(self.reset_sid)
        self.pb_sid.setFont(self.font2)
        self.pb_sid.setFixedWidth(160)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(lb_sid)
        hbox1.addWidget(self.lb_current_sid)
        hbox1.addStretch()

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.pb_sid)
        hbox2.addWidget(self.tx_sid)
        hbox2.addStretch()

        hbox = QHBoxLayout()
        hbox.addLayout(hbox1)
        hbox.addLayout(hbox2)
        hbox.addWidget(lb_empty)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addStretch()
        return hbox

    def vbox_lst_pre_defined_scan(self):
        # lb_empty = QLabel()
        # lb_empty.setFixedWidth(40)
        lb_title = QLabel()
        lb_title.setText('Scan type')
        lb_title.setFont(self.font1)

        #n = len(scan_list)

        self.lst_scan = QListWidget()
        self.lst_scan.setFixedWidth(200)
        self.lst_scan.setFixedHeight(160)
        self.lst_scan.setFont(self.font2)
        self.lst_scan.setSelectionMode(QAbstractItemView.SingleSelection)
        self.load_scan_type_list(1) # load commonly used scans
        '''
        for k in scan_list.keys():
            name = ' '.join(t for t in k.split('_')[1:])
            self.lst_scan.addItem(name)
        '''
        self.lst_scan.itemClicked.connect(self.show_scan_example)
        self.lst_scan.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_scan_list1 = QPushButton('Common')
        self.pb_scan_list1.setFixedWidth(100)
        self.pb_scan_list1.setFont(self.font2)
        self.pb_scan_list1.clicked.connect(lambda: self.load_scan_type_list(1))

        self.pb_scan_list2 = QPushButton('Other scan')
        self.pb_scan_list2.setFixedWidth(100)
        self.pb_scan_list2.setFont(self.font2)
        self.pb_scan_list2.clicked.connect(lambda: self.load_scan_type_list(2))

        self.pb_scan_list3 = QPushButton('User scan')
        self.pb_scan_list3.setFixedWidth(100)
        self.pb_scan_list3.setFont(self.font2)
        self.pb_scan_list3.clicked.connect(lambda: self.load_scan_type_list(3))

        self.pb_scan_list1_update = QPushButton('U')
        self.pb_scan_list1_update.setFixedWidth(30)
        self.pb_scan_list1_update.setFont(self.font2)
        self.pb_scan_list1_update.clicked.connect(lambda: self.update_scan_type_list(1))

        self.pb_scan_list2_update = QPushButton('U')
        self.pb_scan_list2_update.setFixedWidth(30)
        self.pb_scan_list2_update.setFont(self.font2)
        self.pb_scan_list2_update.clicked.connect(lambda: self.update_scan_type_list(2))

        self.pb_scan_list3_update = QPushButton('U')
        self.pb_scan_list3_update.setFixedWidth(30)
        self.pb_scan_list3_update.setFont(self.font2)
        self.pb_scan_list3_update.clicked.connect(lambda: self.update_scan_type_list(3))

        hbox_scan_list1 = QHBoxLayout()
        hbox_scan_list1.addWidget(self.pb_scan_list1)
        hbox_scan_list1.addWidget(self.pb_scan_list1_update)
        hbox_scan_list1.setAlignment(QtCore.Qt.AlignLeft)

        hbox_scan_list2 = QHBoxLayout()
        hbox_scan_list2.addWidget(self.pb_scan_list2)
        hbox_scan_list2.addWidget(self.pb_scan_list2_update)
        hbox_scan_list2.setAlignment(QtCore.Qt.AlignLeft)

        hbox_scan_list3 = QHBoxLayout()
        hbox_scan_list3.addWidget(self.pb_scan_list3)
        hbox_scan_list3.addWidget(self.pb_scan_list3_update)
        hbox_scan_list3.setAlignment(QtCore.Qt.AlignLeft)

        vbox_load_scan = QVBoxLayout()
        vbox_load_scan.addLayout(hbox_scan_list1)
        vbox_load_scan.addLayout(hbox_scan_list2)
        vbox_load_scan.addLayout(hbox_scan_list3)
        vbox_load_scan.setAlignment(QtCore.Qt.AlignTop)

        hbox = QHBoxLayout()
        hbox.addWidget(self.lst_scan)
        hbox.addLayout(vbox_load_scan)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_title)
        vbox.addLayout(hbox)       
        vbox.setAlignment(QtCore.Qt.AlignTop)

        return vbox

    def vbox_eng_list(self):
        lb_title = QLabel()
        lb_title.setText('Energy list')
        lb_title.setFixedWidth(120)
        lb_title.setFont(self.font1)

        self.lst_eng_list = QListWidget()
        self.lst_eng_list.setFixedWidth(160)
        self.lst_eng_list.setFixedHeight(160)
        self.lst_eng_list.setFont(self.font2)
        self.lst_eng_list.setSelectionMode(QAbstractItemView.SingleSelection)

        lb_name = QLabel()
        lb_name.setText('Name:')
        lb_name.setFont(self.font2)
        lb_name.setFixedWidth(80)

        self.tx_eng_name = QLineEdit()
        self.tx_eng_name.setFont(self.font2)
        self.tx_eng_name.setFixedWidth(80)

        self.pb_load_eng_list = QPushButton('load (.txt)')
        self.pb_load_eng_list.setFixedWidth(80)
        self.pb_load_eng_list.setFont(self.font2)
        self.pb_load_eng_list.clicked.connect(self.load_eng_list)

        self.pb_select_eng_list = QPushButton('select')
        self.pb_select_eng_list.setFixedWidth(80)
        self.pb_select_eng_list.setFont(self.font2)
        self.pb_select_eng_list.clicked.connect(self.select_eng_list)
        self.pb_select_eng_list.setDisabled(True)

        self.pb_plot_eng_list = QPushButton('plot')
        self.pb_plot_eng_list.setFixedWidth(80)
        self.pb_plot_eng_list.setFont(self.font2)
        self.pb_plot_eng_list.clicked.connect(self.plot_eng_list)

        self.pb_save_eng_list = QPushButton('save')
        self.pb_save_eng_list.setFixedWidth(80)
        self.pb_save_eng_list.setFont(self.font2)
        self.pb_save_eng_list.clicked.connect(self.save_eng_list)

        self.pb_rm_eng_list = QPushButton('delete')
        self.pb_rm_eng_list.setFixedWidth(80)
        self.pb_rm_eng_list.setFont(self.font2)
        self.pb_rm_eng_list.clicked.connect(self.remove_eng_list)

        self.pb_rmall_eng_list = QPushButton('del. all')
        self.pb_rmall_eng_list.setFixedWidth(80)
        self.pb_rmall_eng_list.setFont(self.font2)
        self.pb_rmall_eng_list.clicked.connect(self.remove_all_eng_list)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(lb_name)
        hbox1.addWidget(self.tx_eng_name)
        hbox1.setAlignment(QtCore.Qt.AlignLeft)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.pb_load_eng_list)
        hbox2.addWidget(self.pb_select_eng_list)
        hbox2.setAlignment(QtCore.Qt.AlignLeft)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.pb_plot_eng_list)
        hbox3.addWidget(self.pb_save_eng_list)
        hbox3.setAlignment(QtCore.Qt.AlignLeft)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.pb_rm_eng_list)
        hbox4.addWidget(self.pb_rmall_eng_list)
        hbox4.setAlignment(QtCore.Qt.AlignLeft)

        vbox1 = QVBoxLayout()
        vbox1.addLayout(hbox1)
        vbox1.addLayout(hbox2)
        vbox1.addLayout(hbox3)
        vbox1.addLayout(hbox4)
        vbox1.setAlignment(QtCore.Qt.AlignTop)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.lst_eng_list)
        hbox2.addLayout(vbox1)
        hbox2.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_title)
        vbox.addLayout(hbox2)
        vbox.setAlignment(QtCore.Qt.AlignTop)

        return vbox

    def vbox_record_scan(self):
        lb_title = QLabel()
        lb_title.setText('Recorded scan')
        lb_title.setFont(self.font1)

        self.lst_record_scan = QListWidget()
        self.lst_record_scan.setFixedWidth(160)
        self.lst_record_scan.setFixedHeight(160)
        self.lst_record_scan.setFont(self.font2)
        self.lst_record_scan.itemClicked.connect(self.show_recorded_scan)
        self.lst_record_scan.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_record = QPushButton('record')
        self.pb_record.setFixedWidth(80)
        self.pb_record.setFont(self.font2)
        self.pb_record.setDisabled(True)
        self.pb_record.clicked.connect(self.record_scan)

        self.pb_record_remove = QPushButton('delete')
        self.pb_record_remove.setFixedWidth(80)
        self.pb_record_remove.setFont(self.font2)
        self.pb_record_remove.clicked.connect(self.remove_recorded_scan)

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.pb_record)
        vbox1.addWidget(self.pb_record_remove)
        vbox1.setAlignment(QtCore.Qt.AlignTop)

        hbox = QHBoxLayout()
        hbox.addWidget(self.lst_record_scan)
        hbox.addLayout(vbox1)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_title)
        vbox.addLayout(hbox)
        vbox.setAlignment(QtCore.Qt.AlignTop)

        return vbox

    def vbox_operator(self):
        lb_title = QLabel()
        lb_title.setText('Operators')
        lb_title.setFont(self.font1)
        # lb_title.setStyleSheet('color: rgb(0, 80, 255);')

        # radio button for operators

        self.rd_op_repeat_s = QRadioButton('Repeat')
        # self.rd_op_repeat_s.setStyleSheet('color: rgb(0, 80, 255);')
        self.rd_op_repeat_s.setFixedWidth(90)
        self.rd_op_repeat_s.setFont(self.font2)
        self.rd_op_repeat_s.setChecked(True)

        self.rd_op_repeat_e = QRadioButton('End repeat')
        # self.rd_op_repeat_e.setStyleSheet('color: rgb(0, 80, 255);')
        self.rd_op_repeat_e.setFixedWidth(110)
        self.rd_op_repeat_e.setFont(self.font2)

        self.rd_op_sleep = QRadioButton('sleep (s)')
        # self.rd_op_sleep.setStyleSheet('color: rgb(0, 80, 255);')
        self.rd_op_sleep.setFixedWidth(90)
        self.rd_op_sleep.setFont(self.font2)

        self.rd_op_select_scan = QRadioButton('select scan')
        # self.rd_op_select_scan.setStyleSheet('color: rgb(0, 80, 255);')
        self.rd_op_select_scan.setFixedWidth(110)
        self.rd_op_select_scan.setFont(self.font2)

        self.operator_group = QButtonGroup()
        self.operator_group.setExclusive(True)
        self.operator_group.addButton(self.rd_op_repeat_s)
        self.operator_group.addButton(self.rd_op_repeat_e)
        self.operator_group.addButton(self.rd_op_sleep)
        self.operator_group.addButton(self.rd_op_select_scan)

        self.tx_op_repeat = QLineEdit()
        self.tx_op_repeat.setText('1')
        # self.tx_op_repeat.setStyleSheet('color: rgb(0, 80, 255);')
        self.tx_op_repeat.setValidator(QIntValidator())
        self.tx_op_repeat.setFixedWidth(60)
        self.tx_op_repeat.setFont(self.font2)

        self.tx_op_sleep = QLineEdit()
        self.tx_op_sleep.setValidator(QDoubleValidator())
        self.tx_op_sleep.setFixedWidth(60)
        self.tx_op_sleep.setFont(self.font2)

        self.pb_op_insert = QPushButton('Insert')
        # self.pb_op_insert.setStyleSheet('color: rgb(0, 80, 255);')
        self.pb_op_insert.setFixedWidth(140)
        self.pb_op_insert.setFont(self.font2)
        self.pb_op_insert.clicked.connect(self.insert_operator)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.rd_op_repeat_s)
        hbox1.addWidget(self.tx_op_repeat)
        hbox1.setAlignment(QtCore.Qt.AlignLeft)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.rd_op_sleep)
        hbox2.addWidget(self.tx_op_sleep)
        hbox2.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_title)
        vbox.addLayout(hbox1)
        vbox.addWidget(self.rd_op_repeat_e)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.rd_op_select_scan)
        vbox.addWidget(self.pb_op_insert)
        vbox.setAlignment(QtCore.Qt.AlignTop)

        return vbox

    def vbox_assemble_scan(self):
        lb_title = QLabel()
        lb_title.setText('Assembled scan')
        lb_title.setFont(self.font1)
        # lb_title.setStyleSheet('color: rgb(0, 80, 255);')

        self.lst_assembled_scan = QListWidget()
        self.lst_assembled_scan.setFixedWidth(160)
        self.lst_assembled_scan.setFixedHeight(160)
        self.lst_assembled_scan.setFont(self.font2)
        self.lst_assembled_scan.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_assembled_scan_remove = QPushButton('delete')
        self.pb_assembled_scan_remove.setFixedWidth(80)
        self.pb_assembled_scan_remove.setFont(self.font2)
        self.pb_assembled_scan_remove.clicked.connect(self.remove_assemble_scan)

        self.pb_assembled_scan_remove_all = QPushButton('del. all')
        self.pb_assembled_scan_remove_all.setFixedWidth(80)
        self.pb_assembled_scan_remove_all.setFont(self.font2)
        self.pb_assembled_scan_remove_all.clicked.connect(self.remove_all_assemble_scan)

        self.pb_assembled_scan_up = QPushButton('mv up')
        self.pb_assembled_scan_up.setFixedWidth(80)
        self.pb_assembled_scan_up.setFont(self.font2)
        self.pb_assembled_scan_up.clicked.connect(self.assemble_scan_mv_up)

        self.pb_assembled_scan_down = QPushButton('mv down')
        self.pb_assembled_scan_down.setFixedWidth(80)
        self.pb_assembled_scan_down.setFont(self.font2)
        self.pb_assembled_scan_down.clicked.connect(self.assemble_scan_mv_down)

        self.pb_assembled = QPushButton('assemble')
        self.pb_assembled.setFixedWidth(165)
        self.pb_assembled.setFont(self.font2)
        self.pb_assembled.clicked.connect(self.assemble_scan_assemble)

        lb_name = QLabel()
        lb_name.setText('fun. name')
        lb_name.setFixedWidth(80)
        lb_name.setFont(self.font2)

        self.tx_fun_name = QLineEdit()
        self.tx_fun_name.setFont(self.font2)
        self.tx_fun_name.setFixedWidth(80)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.pb_assembled_scan_up)
        hbox1.addWidget(self.pb_assembled_scan_down)
        hbox1.setAlignment(QtCore.Qt.AlignLeft)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.pb_assembled_scan_remove)
        hbox2.addWidget(self.pb_assembled_scan_remove_all)
        hbox2.setAlignment(QtCore.Qt.AlignLeft)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(lb_name)
        hbox3.addWidget(self.tx_fun_name)
        hbox3.setAlignment(QtCore.Qt.AlignLeft)

        vbox1 = QVBoxLayout()
        vbox1.addLayout(hbox1)
        vbox1.addLayout(hbox2)
        vbox1.addLayout(hbox3)
        vbox1.addWidget(self.pb_assembled)
        vbox1.setAlignment(QtCore.Qt.AlignTop)

        hbox = QHBoxLayout()
        hbox.addWidget(self.lst_assembled_scan)
        hbox.addLayout(vbox1)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_title)
        vbox.addLayout(hbox)
        vbox.setAlignment(QtCore.Qt.AlignTop)

        return vbox

    def layout_matrix_scan_argument(self):
        self.scan_lb = {}
        self.scan_tx = {}
        hbox = {}
        vbox = QVBoxLayout()
        for i in range(20):
            self.scan_lb[f'lb_{i}'] = QLabel()
            self.scan_lb[f'lb_{i}'].setText(f'param {i}:')
            self.scan_lb[f'lb_{i}'].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.scan_lb[f'lb_{i}'].setFixedWidth(160)
            self.scan_lb[f'lb_{i}'].setFont(self.font2)
            self.scan_lb[f'lb_{i}'].setVisible(False)
            self.scan_tx[f'tx_{i}'] = QLineEdit()
            self.scan_tx[f'tx_{i}'].setFixedWidth(120)
            self.scan_tx[f'tx_{i}'].setFont(self.font2)
            self.scan_tx[f'tx_{i}'].setVisible(False)
        self.scan_lb['note'] = QLabel()
        self.scan_lb['note'].setText('Sample infor:')
        self.scan_lb['note'].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.scan_lb['note'].setFont(self.font1)
        self.scan_lb['note'].setFixedWidth(160)
        self.scan_lb['note'].setVisible(True)
        self.scan_tx['note'] = QLineEdit()
        self.scan_tx['note'].setFont(self.font2)
        self.scan_tx['note'].setFixedWidth(290)
        self.scan_tx['note'].setVisible(True)

        self.scan_lb['XEng'] = QLabel()
        self.scan_lb['XEng'].setText('X-ray Energy:')
        self.scan_lb['XEng'].setFont(self.font1)
        self.scan_lb['XEng'].setFixedWidth(120)
        self.scan_lb['XEng'].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.scan_tx['XEng'] = QLineEdit()
        self.scan_tx['XEng'].setValidator(QDoubleValidator())
        self.scan_tx['XEng'].setFont(self.font2)
        self.scan_tx['XEng'].setFixedWidth(120)

        self.pb_read_current_eng = QPushButton('use curr. XEng')
        self.pb_read_current_eng.clicked.connect(self.use_current_eng)
        self.pb_read_current_eng.setFixedWidth(120)
        self.pb_read_current_eng.setFont(self.font2)

        for i in range(4):
            hbox[f'hbox_{i}'] = QHBoxLayout()
            for j in range(5):
                hbox[f'hbox_{i}'].addWidget(self.scan_lb[f'lb_{i * 5 + j}'])
                hbox[f'hbox_{i}'].addWidget(self.scan_tx[f'tx_{i * 5 + j}'])
                hbox[f'hbox_{i}'].setAlignment(QtCore.Qt.AlignLeft)
        hbox['note'] = QHBoxLayout()
        hbox['note'].addWidget(self.scan_lb['note'])
        hbox['note'].addWidget(self.scan_tx['note'])
        hbox['note'].addWidget(self.scan_lb['XEng'])
        hbox['note'].addWidget(self.scan_tx['XEng'])
        hbox['note'].addWidget(self.pb_read_current_eng)
        hbox['note'].setAlignment(QtCore.Qt.AlignLeft)

        lb_empty = QLabel()
        lb_pos = QLabel()
        lb_pos.setText('Sample / Bkg. Pos.:')
        lb_pos.setFont(self.font1)
        lb_pos.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        lb_pos.setFixedWidth(160)

        self.lb_sampel_pos_msg = QLabel()
        self.lb_sampel_pos_msg.setFont(self.font2)
        self.lb_sampel_pos_msg.setText('  If empty, use current position')

        self.tx_pos = QLineEdit()
        self.tx_pos.setFixedWidth(290)
        self.tx_pos.setFont(self.font2)

        self.pb_choose_pos = QPushButton('add from list')
        self.pb_choose_pos.setFixedWidth(120)
        self.pb_choose_pos.setFont(self.font2)
        self.pb_choose_pos.clicked.connect(self.add_sample_pos)

        self.pb_clear_pos = QPushButton('clear positions')
        self.pb_clear_pos.setFixedWidth(120)
        self.pb_clear_pos.setFont(self.font2)
        self.pb_clear_pos.clicked.connect(self.clear_scan_pos)

        self.pb_assemble_scan = QPushButton('check scan')
        self.pb_assemble_scan.setFont(self.font1)
        self.pb_assemble_scan.setFixedWidth(120)
        self.pb_assemble_scan.setStyleSheet('color: rgb(200, 50, 50);')
        self.pb_assemble_scan.clicked.connect(self.check_scan)


        hbox_pos = QHBoxLayout()
        hbox_pos.addWidget(lb_pos)
        hbox_pos.addWidget(self.tx_pos)
        hbox_pos.addWidget(self.pb_choose_pos)
        hbox_pos.addWidget(self.pb_clear_pos)
        hbox_pos.addWidget(self.lb_sampel_pos_msg)
        hbox_pos.addWidget(lb_empty)
        hbox_pos.setAlignment(QtCore.Qt.AlignLeft)

        hbox_scan = QHBoxLayout()
        hbox_scan.addWidget(self.pb_assemble_scan)
        # hbox_scan.addWidget(self.pb_run_scan)
        hbox_scan.setAlignment(QtCore.Qt.AlignLeft)

        lb_empty2 = QLabel()
        lb_empty2.setFixedHeight(10)
        lb_empty3 = QLabel()
        lb_empty3.setFixedHeight(10)

        vbox.addLayout(hbox['note'])
        #vbox.addLayout(hbox_pos)
        vbox.addWidget(lb_empty2)
        for i in range(4):
            vbox.addLayout(hbox[f'hbox_{i}'])
        vbox.addWidget(lb_empty3)
        vbox.addLayout(hbox_scan)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        return vbox

    def get_step_size(self):
        if self.rd_step_10nm.isChecked():
            ss = 0.01
        elif self.rd_step_100nm.isChecked():
            ss = 0.1
        elif self.rd_step_1um.isChecked():
            ss = 1
        elif self.rd_step_5um.isChecked():
            ss = 5
        elif self.rd_step_20um.isChecked():
            ss = 20
        elif self.rd_step_50um.isChecked():
            ss = 50
        elif self.rd_step_200um.isChecked():
            ss = 200
        elif self.rd_step_1mm.isChecked():
            ss = 1000
        elif self.rd_step_custom.isChecked():
            ss = float(self.tx_step_custom.text())
        return ss

    def move_motor_positive(self, label):
        #ss = self.get_step_size()
        if label == 'x':
            ss = float(self.tx_step_x.text())
            current_set = float(self.lb_motor_pos_x.text())
            self.tx_setpos_x.setText(f'{(current_set + ss):4.3f}')
            self.move_to_pos('x')
        elif label == 'y':
            ss = float(self.tx_step_y.text())
            current_set = float(self.lb_motor_pos_y.text())
            self.tx_setpos_y.setText(f'{(current_set + ss):4.3f}')
            self.move_to_pos('y')
        elif label == 'z':
            ss = float(self.tx_step_z.text())
            current_set = float(self.lb_motor_pos_z.text())
            self.tx_setpos_z.setText(f'{(current_set + ss):4.3f}')
            self.move_to_pos('z')
        elif label == 'r':
            ss = float(self.tx_step_r.text())
            current_set = float(self.lb_motor_pos_r.text())
            ss = float(self.tx_rot_step_custom.text())
            self.tx_setpos_r.setText(f'{(current_set + ss):4.3f}')
            self.move_to_pos('r')

    def move_motor_negative(self, label):
        # ss = self.get_step_size()
        if label == 'x':
            ss = float(self.tx_step_x.text())
            current_set = float(self.lb_motor_pos_x.text())
            self.tx_setpos_x.setText(f'{(current_set - ss):4.3f}')
            self.move_to_pos('x')
        elif label == 'y':
            ss = float(self.tx_step_y.text())
            current_set = float(self.lb_motor_pos_y.text())
            self.tx_setpos_y.setText(f'{(current_set - ss):4.3f}')
            self.move_to_pos('y')
        elif label == 'z':
            ss = float(self.tx_step_z.text())
            current_set = float(self.lb_motor_pos_z.text())
            self.tx_setpos_z.setText(f'{(current_set - ss):4.3f}')
            self.move_to_pos('z')
        elif label == 'r':
            ss = float(self.tx_step_r.text())
            current_set = float(self.lb_motor_pos_r.text())
            ss = float(self.tx_rot_step_custom.text())
            self.tx_setpos_r.setText(f'{(current_set - ss):4.3f}')
            self.move_to_pos('r')

    def check_pos_limit(self, label):
        if label == 'x':
            limit = self.lb_limit_x.text()[1:-1].split(',')
            l_l = float(limit[0])
            l_h = float(limit[1])
            try:
                val = np.float(self.tx_setpos_x.text())
            except:
                val = np.float(self.lb_motor_pos_x.text())
            if val >= l_l and val <= l_h:
                flag = 1
            else:
                flag = 0
        if label == 'y':
            limit = self.lb_limit_y.text()[1:-1].split(',')
            l_l = float(limit[0])
            l_h = float(limit[1])
            try:
                val = np.float(self.tx_setpos_y.text())
            except:
                val = np.float(self.lb_motor_pos_y.text())
            if val >= l_l and val <= l_h:
                flag = 1
            else:
                flag = 0
        if label == 'z':
            limit = self.lb_limit_z.text()[1:-1].split(',')
            l_l = float(limit[0])
            l_h = float(limit[1])
            try:
                val = np.float(self.tx_setpos_z.text())
            except:
                val = np.float(self.lb_motor_pos_z.text())
            if val >= l_l and val <= l_h:
                flag = 1
            else:
                flag = 0
        if label == 'r':
            limit = self.lb_limit_r.text()[1:-1].split(',')
            l_l = float(limit[0])
            l_h = float(limit[1])
            try:
                val = np.float(self.tx_setpos_r.text())
            except:
                val = np.float(self.lb_motor_pos_r.text())
            if val >= l_l and val <= l_h:
                flag = 1
            else:
                flag = 0
        return flag, val

    def move_to_pos(self, label):
        if label == 'x':
            flag, val = self.check_pos_limit('x')
            if flag:
                try:
                    self.tx_setpos_x.setDisabled(True)
                    RE(mv(zps.sx, val))
                    #RE(abs_set(zps.sx, val))
                    val_rb = zps.sx.position
                    self.lb_motor_pos_x.setText(f'{val_rb:4.4f}')
                except:
                    msg = 'fails to move motor x'
                    print(msg)
                    self.tx_scan_msg.setPlainText(msg)
                finally:
                    self.tx_setpos_x.setEnabled(True)
            else:
                self.tx_setpos_x.setText(self.lb_motor_pos_x.text())
                msg = 'out of limit'
                print(msg)
                self.tx_scan_msg.setPlainText(msg)
        if label == 'y':
            flag, val = self.check_pos_limit('y')
            if flag:
                try:
                    self.tx_setpos_y.setDisabled(True)
                    RE(mv(zps.sy, val))
                    #RE(abs_set(zps.sy, val))
                    val_rb = zps.sy.position
                    self.lb_motor_pos_y.setText(f'{val_rb:4.4f}')
                except:
                    msg = 'fails to move motor y'
                    print(msg)
                    self.tx_scan_msg.setPlainText(msg)
                finally:
                    self.tx_setpos_y.setEnabled(True)
            else:
                self.tx_setpos_y.setText(self.lb_motor_pos_y.text())
                msg = 'out of limit'
                print(msg)
                self.tx_scan_msg.setPlainText(msg)
        if label == 'z':
            flag, val = self.check_pos_limit('z')
            if flag:
                try:
                    self.tx_setpos_z.setDisabled(True)
                    RE(mv(zps.sz, val))
                    #RE(abs_set(zps.sz, val))
                    val_rb = zps.sz.position
                    self.lb_motor_pos_z.setText(f'{val_rb:4.4f}')
                except:
                    msg = 'fails to move motor z'
                    print(msg)
                    self.tx_scan_msg.setPlainText(msg)
                finally:
                    self.tx_setpos_z.setEnabled(True)
            else:
                self.tx_setpos_z.setText(self.lb_motor_pos_z.text())
                msg = 'out of limit'
                print(msg)
                self.tx_scan_msg.setPlainText(msg)
        if label == 'r':
            flag, val = self.check_pos_limit('r')
            if flag:
                try:
                    self.tx_setpos_r.setDisabled(True)
                    RE(mv(zps.pi_r, val))
                    #RE(abs_set(zps.pi_r, val))
                    val_rb = zps.pi_r.position
                    self.lb_motor_pos_r.setText(f'{val_rb:4.4f}')
                    self.tx_setpos_r.setEnabled(True)
                except:
                    msg = 'fails to move motor r'
                    print(msg)
                    self.tx_scan_msg.setPlainText(msg)
                finally:
                    self.tx_setpos_r.setEnabled(True)
            else:
                self.tx_setpos_r.setText(self.lb_motor_pos_r.text())
                msg = 'out of limit'
                print(msg)
                self.tx_scan_msg.setPlainText(msg)

    def move_to_energy(self):
        try:
            val = float(self.tx_setpos_e.text())
        except:
            val = float(self.lb_motor_pos_e.text())

        try:
            print(f'TEST: will do: RE(move_zp_ccd({val}))')
            self.tx_setpos_e.setDisabled(True)
            RE(move_zp_ccd(val))
            val = XEng.position
        except Exception as err:
            msg = str(err)
            print(msg)
            self.tx_scan_msg.setPlainText(msg)
        finally:
            self.tx_setpos_e.setEnabled(True)
        self.lb_motor_pos_e.setText(f'{val:2.5f}')
        self.scan_tx['XEng'].setText(f'{val:2.5f}')

    def pos_sync(self):
        try:
            msg = ''
            sid = RE.md['scan_id']
            self.lb_current_sid.setText(str(sid))
            sid2 = db[-1].start['scan_id']
            if not (sid == sid2):
                msg += f'''discrepancy found: RE.md["scan_id"] != db[-1].start["scan_id"]\
                \n RE.md["scan_id"] = {sid}\ndb[-1].start["scan_id"] = {sid2}\n'''
                msg += f'set scan_id to {max(sid2, sid)}'
                self.lb_current_sid.setText(str(max(sid, sid2)))
                print(msg)
                self.tx_scan_msg.setPlainText(msg)
            else:
                self.lb_current_sid.setText(str(sid2))
            
            self.display_calib_eng_only()
            msg += 'update energy calibration finished.\n'
        except:
            msg += 'fails to connect database to retrieve scan_ID\n'
        finally:
            print(msg)
            self.tx_scan_msg.setPlainText(msg)
        try:
            x = zps.sx.position
            y = zps.sy.position
            z = zps.sz.position
            r = zps.pi_r.position
            eng = XEng.position
            self.lb_motor_pos_x.setText(f'{x:5.4f}')
            self.lb_motor_pos_y.setText(f'{y:5.4f}')
            self.lb_motor_pos_z.setText(f'{z:5.4f}')
            self.lb_motor_pos_r.setText(f'{r:5.4f}')
            self.lb_motor_pos_e.setText(f'{eng:2.5f}')
        except:
            msg += 'fails to connect physical motor (zps.sx, zps.sy, spz.sz and zps.pi_r)\n'
        finally:
            print(msg)
            self.tx_scan_msg.setPlainText(msg)
        try:
            self.display_calib_eng_only()
        except:
            msg += 'fails to read energy calibration file)\n'
        finally:
            print(msg)
            self.tx_scan_msg.setPlainText(msg)
        # need to synchronize with CSS
        self.tx_setpos_x.setText(self.lb_motor_pos_x.text())
        self.tx_setpos_y.setText(self.lb_motor_pos_y.text())
        self.tx_setpos_z.setText(self.lb_motor_pos_z.text())
        self.tx_setpos_r.setText(self.lb_motor_pos_r.text())
        self.tx_setpos_e.setText(self.lb_motor_pos_e.text())

        try:
            lim_x = zps.sx.limits
            lim_y = zps.sy.limits
            lim_z = zps.sz.limits
            lim_r = zps.pi_r.limits
            self.lb_limit_x.setText(f'({int(lim_x[0])}, {int(lim_x[1])})')
            self.lb_limit_y.setText(f'({int(lim_y[0])}, {int(lim_y[1])})')
            self.lb_limit_z.setText(f'({int(lim_z[0])}, {int(lim_z[1])})')
            self.lb_limit_r.setText(f'({int(lim_r[0])}, {int(lim_r[1])})')
        except:
            msg += 'fails to connect physical motor (zps.sx, zps.sy, spz.sz and zps.pi_r) to retieve motor limits\n'
        finally:    
            print(msg)
        msg += 'motor synchronization finshed.'    
        self.tx_scan_msg.setPlainText(msg)

    def repeat_pos_sync(self):
        while(True):
            try:
                x = zps.sx.position
                y = zps.sy.position
                z = zps.sz.position
                r = zps.pi_r.position
                eng = XEng.position
                self.lb_motor_pos_x.setText(f'{x:5.4f}')
                self.lb_motor_pos_y.setText(f'{y:5.4f}')
                self.lb_motor_pos_z.setText(f'{z:5.4f}')
                self.lb_motor_pos_r.setText(f'{r:5.4f}')
                self.lb_motor_pos_e.setText(f'{eng:2.5f}')
                '''
                timestamp_calib_eng_file = os.stat(self.fn_calib_eng_file)
                if self.timestamp_cache_for_calib_eng_file != timestamp_calib_eng_file:
                    print('update the energy calibration file')
                    self.display_calib_eng_only()
                '''
                #sid = db[-1].start['scan_id']
                #self.lb_current_sid.setText(str(sid))
                time.sleep(0.2)
            except Exception as err:
                print(err)

    def open_shutter(self):
        try:
            self.pb_open_shutter.setDisabled(True)
            RE(_open_shutter())
        except Exception as err:
            print(err)
        finally:
            self.pb_open_shutter.setDisabled(False)
        

    def close_shutter(self):
        try:
            self.pb_close_shutter.setDisabled(True)
            RE(_close_shutter())
        except Exception as err:
            print(err)
        finally:
            self.pb_close_shutter.setDisabled(False)
        

    def reset_r_speed(self):
        try:
            RE(mv(zps.pi_r.velocity, 30))
            msg = f'rotation speed set to {zps.pi_r.velocity.value} deg/sec'
            print(msg)
            self.tx_scan_msg.setPlainText(msg)
        except:
            msg = 'fails to reset'
            print(msg)
            self.tx_scan_msg.setPlainText(msg)

    def get_available_pos_id(self):
        pos_available = 1
        for i in range(1, self.pos_num + 1):
            if not f'pos_{i:02d}' in self.pos.keys():
                pos_available = i
                break
        pos_available = min(pos_available, self.pos_num + 1)
        return pos_available

    def show_pos_clicked(self):
        item = self.lst_pos.selectedItems()
        pos = item[0].text()  # 'e.g., pos_01'
        x = float(self.pos[pos]['x'])
        y = float(self.pos[pos]['y'])
        z = float(self.pos[pos]['z'])
        r = float(self.pos[pos]['r'])
        self.lb_pos_x.setText(f'{x:4.3f}')
        self.lb_pos_y.setText(f'{y:4.3f}')
        self.lb_pos_z.setText(f'{z:4.3f}')
        self.lb_pos_r.setText(f'{r:4.3f}')

    def pos_record(self):
        x = float(self.lb_motor_pos_x.text())
        y = float(self.lb_motor_pos_y.text())
        z = float(self.lb_motor_pos_z.text())
        r = float(self.lb_motor_pos_r.text())
        self.pos_num += 1
        pos_id = self.get_available_pos_id()
        self.pos[f'pos_{pos_id:02d}'] = {}
        self.pos[f'pos_{pos_id:02d}']['x'] = x
        self.pos[f'pos_{pos_id:02d}']['y'] = y
        self.pos[f'pos_{pos_id:02d}']['z'] = z
        self.pos[f'pos_{pos_id:02d}']['r'] = r
        self.lst_pos.addItem(f'pos_{pos_id:02d}')
        self.lst_pos.sortItems()

    def pos_remove(self):
        item = self.lst_pos.selectedItems()
        if len(item):
            pos = item[0].text()  # 'e.g., pos_1'
            del self.pos[pos]
            if pos != 'Bkg':
                self.pos_num -= 1
            self.lst_pos.takeItem(self.lst_pos.row(item[0]))
            self.lst_pos.sortItems()
        item = self.lst_pos.selectedItems()
        msg = f'num of position: {self.pos_num}'
        print(msg)
        self.tx_scan_msg.setPlainText(msg)
        if len(item):
            self.show_pos_clicked()

        # also remove item in list "Position selected for scan", if exist
        i = 0
        while i < min(self.lst_scan_pos.count(), 99):
            rm_item = self.lst_scan_pos.item(i)
            pos_exist = rm_item.text()
            if pos == pos_exist:
                self.lst_scan_pos.takeItem(self.lst_scan_pos.row(rm_item))
            i = i + 1

    def pos_remove_all(self):
        self.pos = {}
        self.lst_pos.clear()
        self.lst_scan_pos.clear()

    def pos_update(self):
        item = self.lst_pos.selectedItems()
        if len(item):
            x = float(self.lb_motor_pos_x.text())
            y = float(self.lb_motor_pos_y.text())
            z = float(self.lb_motor_pos_z.text())
            r = float(self.lb_motor_pos_r.text())
            pos = item[0].text()
            self.pos[pos]['x'] = x
            self.pos[pos]['y'] = y
            self.pos[pos]['z'] = z
            self.pos[pos]['r'] = r
            self.show_pos_clicked()
            self.add_bkg_pos()

    def pos_go_to(self):
        item = self.lst_pos.selectedItems()
        if len(item):
            pos = item[0].text()
            x, y = self.pos[pos]['x'], self.pos[pos]['y']
            z, r = self.pos[pos]['z'], self.pos[pos]['r']
            self.tx_setpos_x.setText(f'{x:4.3f}')
            self.tx_setpos_y.setText(f'{y:4.3f}')
            self.tx_setpos_z.setText(f'{z:4.3f}')
            self.tx_setpos_r.setText(f'{r:4.3f}')

            self.move_to_pos('x')
            self.move_to_pos('y')
            self.move_to_pos('z')
            self.move_to_pos('r')

    def pos_record_bkg(self):
        x = float(self.lb_motor_pos_x.text())
        y = float(self.lb_motor_pos_y.text())
        z = float(self.lb_motor_pos_z.text())
        r = float(self.lb_motor_pos_r.text())
        self.pos['Bkg'] = {}
        self.pos['Bkg']['x'] = x
        self.pos['Bkg']['y'] = y
        self.pos['Bkg']['z'] = z
        self.pos['Bkg']['r'] = r
        if not self.lst_pos.findItems('Bkg', QtCore.Qt.MatchExactly):
            self.lst_pos.addItem('Bkg')
        self.lst_pos.sortItems()
        item = self.lst_pos.findItems('Bkg', QtCore.Qt.MatchExactly)
        item[0].setSelected(True)
        self.show_pos_clicked()
        self.add_bkg_pos()

    def show_scan_example_sub(self, txm_scan):
        
        for i in range(20):
            self.scan_lb[f'lb_{i}'].setText(f'param {i}:')
            self.scan_lb[f'lb_{i}'].setVisible(False)
            self.scan_tx[f'tx_{i}'].setVisible(False)
        self.pb_record.setDisabled(True)
        n = len(txm_scan)
        i = 0
        flag_eng_list = 0
        intro = ''
        for key in txm_scan.keys():
            if 'eng_list' in key:
                flag_eng_list += 1
            if 'introduction' in key:
                intro = txm_scan['introduction']
                continue
            self.scan_lb[f'lb_{i}'].setText(key + ':')
            self.scan_lb[f'lb_{i}'].setVisible(True)
            self.scan_lb[f'lb_{i}'].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.scan_tx[f'tx_{i}'].setText(str(txm_scan[key]))
            self.scan_tx[f'tx_{i}'].setVisible(True)
            i += 1
        if flag_eng_list > 0:
            self.pb_select_eng_list.setEnabled(True)
        else:
            self.pb_select_eng_list.setDisabled(True)
        self.tx_pos.setText('')
        self.sample_pos = {}
        scan_name = self.scan_name
        try:
            intro += eval(scan_name[4:]).__doc__
        except:
            print(f'function "{scan_name}" does not have description')
        print(scan_name[4:])
        self.tx_scan_msg.setPlainText(intro)

    def show_scan_example(self):
        item = self.lst_scan.selectedItems()
        self.scan_name = 'txm_' + item[0].text().replace(' ', '_')
        txm_scan = scan_list[self.scan_name]
        self.show_scan_example_sub(txm_scan)
        self.add_bkg_pos()

    def add_bkg_pos(self):
        try:
            i = 0
            while i < min(self.lst_pos.count(), 99):
                item = self.lst_pos.item(i)
                pos = item.text()
                #print(f'\nbkg_pos={pos}')
                if 'Bkg' in pos:  # background /out position
                    x = self.pos[pos]['x']
                    y = self.pos[pos]['y']
                    z = self.pos[pos]['z']
                    r = self.pos[pos]['r']
                    for i in range(20):
                        txt = self.scan_lb[f'lb_{i}'].text()
                        if 'out_x' in txt:
                            self.scan_tx[f'tx_{i}'].setText(str(x))
                        elif 'out_y' in txt:
                            self.scan_tx[f'tx_{i}'].setText(str(y))
                        elif 'out_z' in txt:
                            self.scan_tx[f'tx_{i}'].setText(str(z))
                        elif 'out_r' in txt:
                            self.scan_tx[f'tx_{i}'].setText(str(r))
                        elif 'relative_move' in txt:
                            self.scan_tx[f'tx_{i}'].setText('False')
                i = i + 1
        except Exception as err:
            print(err)

    def add_sample_pos(self):
        try:
            item = self.lst_pos.selectedItems()
            pos = item[0].text()  # 'e.g., pos_01'
            if 'pos' in pos and (not pos in self.tx_pos.text()):  # not background position, and selected position has not been added
                pos_tmp = {pos: self.pos[pos]}
                # self.sample_pos.append(pos_tmp)
                self.sample_pos[pos] = self.pos[pos]
                pos_info = self.tx_pos.text()
                if 'pos_00' in pos_info:
                    self.tx_pos.setText('')
                    pos_info = ''
                if len(pos_info):
                    pos_info = pos_info + f', {pos}'
                else:
                    pos_info = pos
                self.tx_pos.setText(pos_info)
            # Now backgound position is automatically added when created    
            '''
            elif 'Bkg' in pos:  # background /out position
                x = self.pos[pos]['x']
                y = self.pos[pos]['y']
                z = self.pos[pos]['z']
                r = self.pos[pos]['r']
                for i in range(20):
                    txt = self.scan_lb[f'lb_{i}'].text()
                    if 'out_x' in txt:
                        self.scan_tx[f'tx_{i}'].setText(str(x))
                    elif 'out_y' in txt:
                        self.scan_tx[f'tx_{i}'].setText(str(y))
                    elif 'out_z' in txt:
                        self.scan_tx[f'tx_{i}'].setText(str(z))
                    elif 'out_r' in txt:
                        self.scan_tx[f'tx_{i}'].setText(str(r))
                    elif 'relative_move' in txt:
                        self.scan_tx[f'tx_{i}'].setText('False')
                '''
        except:
            self.sample_pos = {}

    def clear_scan_pos(self):
        self.sample_pos = {}
        self.tx_pos.setText('')

    def pos_select_for_scan(self):
        item = self.lst_pos.selectedItems()
        if len(item):
            pos = item[0].text()
            if not 'Bkg' in pos:  
                i = 0
                flag_exist = False
                while i < min(self.lst_scan_pos.count(), 99):
                    pos_exist = self.lst_scan_pos.item(i).text()
                    if pos == pos_exist:
                        flag_exist = True
                        break
                    i = i + 1
                if not flag_exist:
                    self.lst_scan_pos.addItem(pos)
                else:
                    print(f'{pos} has already been added to scan list')

    def pos_remove_select(self):
        item = self.lst_scan_pos.selectedItems()
        if len(item):
            pos = item[0].text()  # 'e.g., pos_1'
            self.lst_scan_pos.takeItem(self.lst_scan_pos.row(item[0]))
    
    def pos_remove_all_select(self):
        self.lst_scan_pos.clear()

    def get_scan_pos_from_list(self):
        self.sample_pos = {}
        for i in range(self.lst_scan_pos.count()):
            item = self.lst_scan_pos.item(i)
            pos = item.text()
            self.sample_pos[pos] = self.pos[pos]


    def check_scan(self):
        self.txm_scan = {}
        flag_multi_pos_scan = 0
        self.get_scan_pos_from_list()
        num_pos = len(self.sample_pos)
        if num_pos == 0:
            flag_pos_selected = 0
            x, y, z, r = self.get_current_pos()
            pos_tmp = {'x': x, 'y': y, 'z': z, 'r': r}
            self.sample_pos['pos_00'] = pos_tmp
            self.tx_pos.setText('pos_00')
        self.txm_scan['pos'] = self.sample_pos.copy()
        x_list = []
        y_list = []
        z_list = []
        r_list = []
        for key in self.sample_pos.keys():
            x_list.append(self.sample_pos[key]['x'])
            y_list.append(self.sample_pos[key]['y'])
            z_list.append(self.sample_pos[key]['z'])
            r_list.append(self.sample_pos[key]['r'])
        try:
            flag_pos_selected = 1
            # self.txm_scan = scan_list[self.scan_name].copy()
            scan_name = '_'.join(self.scan_name.split('_')[1:])

            self.txm_scan['name'] = scan_name
            cmd = ''
            cmd_eng_list = ''
            eng_list_error = 0
            for i in range(20):
                if self.scan_lb[f'lb_{i}'].isVisible():
                    param = self.scan_lb[f'lb_{i}'].text()[:-1]
                    val = self.scan_tx[f'tx_{i}'].text()
                    param_val = val
                    if 'intro' in param:
                        continue

                    # special case 1: eng_list
                    if 'eng_list' in param:
                        if val == '[]':
                            eng_list_error = 1
                        else:
                            try:
                                eng_list = np.loadtxt(self.txm_eng_list[val])
                                cmd_eng_list = f'{val} = np.loadtxt("{self.txm_eng_list[val]}")'
                                self.txm_scan[val] = f'np.loadtxt("{self.txm_eng_list[val]}")'
                            except:
                                try:
                                    exec(val)
                                    cmd_eng_list = f'EL = {val}'
                                    param_val = 'EL'
                                    self.txm_scan['EL'] = val
                                except:
                                    eng_list_error = 1
                    # end case 1

                    # special case 2: multi_pos_scan
                    if 'x_list' in param:
                        param_val = x_list
                        flag_multi_pos_scan = 1
                    if 'y_list' in param:
                        param_val = y_list
                        flag_multi_pos_scan = 1
                    if 'z_list' in param:
                        param_val = z_list
                        flag_multi_pos_scan = 1
                    if 'r_list' in param:
                        param_val = r_list
                        flag_multi_pos_scan = 1
                    # end case 2
                    cmd += f'{param}={param_val}, '
                    self.txm_scan[param] = param_val
            note = self.scan_tx['note'].text()
            if not len(note):
                note = None
            cmd += f'note="{note}"'
            self.txm_scan['note'] = f'"{note}"'
            cmd = f'RE({scan_name}({cmd}))'
            if eng_list_error:
                cmd = '\neng_list is empty !'
                #self.pb_run_scan.setDisabled(True)
                #self.pb_run_scan.setStyleSheet('color: rgb(200, 200, 200);')
            else:
                self.pb_record.setEnabled(True)
                #self.pb_run_scan.setEnabled(True)
                #self.pb_run_scan.setStyleSheet('color: rgb(200, 50, 50);')
        except:
            self.pb_record.setDisabled(True)
            cmd = '# no scan scheduled'
        cmd_move_pos = {}
        cmd_all = ''

        try:
            eng = eval(self.scan_tx['XEng'].text())
        except:
            self.use_current_eng()
            eng = eval(self.scan_tx['XEng'].text())


        cmd_check_sid = 'RE.md["scan_id"] = db[-1].start["scan_id"]\n'
        cmd_all += cmd_check_sid + '\n'

        self.txm_scan['XEng'] = eng
        cmd_move_eng = f'RE(move_zp_ccd({eng}))\n'
        cmd_all += cmd_move_eng + '\n'

        if len(cmd_eng_list):
            cmd_all += cmd_eng_list + '\n\n'

        if not flag_multi_pos_scan:
            for key in self.sample_pos.keys():
                x, y = self.sample_pos[key]['x'], self.sample_pos[key]['y']
                z, r = self.sample_pos[key]['z'], self.sample_pos[key]['r']
                cmd_move_pos[key] = f'RE(mv(zps.sx, {x}, zps.sy, {y}, zps.sz, {z}, zps.pi_r, {r}))  #{key}'
            for key in self.sample_pos.keys():
                cmd_all += cmd_move_pos[key] + '\n'
                cmd_all += cmd + '\n\n'
        else:
            cmd_all += cmd + '\n\n'
        if flag_pos_selected == 0:
            del self.sample_pos['pos_00']
            self.pos_num = 0
        self.tx_scan_msg.setPlainText(cmd_all)

    def get_current_pos(self):
        x = eval(self.lb_motor_pos_x.text())
        y = eval(self.lb_motor_pos_y.text())
        z = eval(self.lb_motor_pos_z.text())
        r = eval(self.lb_motor_pos_r.text())
        return x, y, z, r

    def get_available_eng_list_id(self):
        pos_available = 1
        l = list(self.txm_eng_list.keys())
        key_name = ['_'.join(a.split('_')[:2]) for a in l]
        for i in range(1, len(self.txm_eng_list) + 2):
            if not f'E_{i:02d}' in key_name:
                pos_available = i
                break
        pos_available = min(pos_available, len(self.txm_eng_list) + 2)
        return pos_available

    def load_eng_list(self):
        options = QFileDialog.Option()
        file_type = 'txt files (*.txt)'
        fn, _ = QFileDialog.getOpenFileName(txm, "QFileDialog.getOpenFileName()", "", file_type, options=options)
        if fn:
            try:
                eng_list = np.array(np.loadtxt(fn))
            except:
                eng_list = [eval(self.lb_motor_pos_e.text())]
            eng_name = self.tx_eng_name.text()
            available_id = self.get_available_eng_list_id()
            eng_name = f'E_{available_id:02d}_{eng_name}'
            # self.txm_eng_list[eng_name] = eng_list
            self.txm_eng_list[eng_name] = fn

            self.lst_eng_list.addItem(eng_name)
            self.lst_eng_list.sortItems()

    def select_eng_list(self):
        global EL
        # EL = {}
        item = self.lst_eng_list.selectedItems()
        if len(item):
            eng_name = item[0].text()
            eng_val = self.txm_eng_list[eng_name]
            for i in range(20):
                if 'eng_list' in self.scan_lb[f'lb_{i}'].text():
                    break
            # EL[eng_name] = eng_val
            # self.scan_tx[f'tx_{i}'].setText(f'EL["{eng_name}"]')
            self.scan_tx[f'tx_{i}'].setText(eng_name)

    def save_eng_list(self):
        item = self.lst_eng_list.selectedItems()
        if len(item):
            eng_name = self.tx_eng_name.text()
            eng_file_origin = self.txm_eng_list[eng_name]
        try:
            options = QFileDialog.Option()
            options |= QFileDialog.DontUseNativeDialog
            file_type = 'txt files (*.txt)'
            fn, _ = QFileDialog.getSaveFileName(self, 'Save Spectrum', "", file_type, options=options)
            if fn[-4:] != '.txt':
                fn += '.txt'
            _ = os.system(f'cp {eng_file_origin} {fn}')
        except:
            print('fails to save file')

    def plot_eng_list(self):
        item = self.lst_eng_list.selectedItems()
        if len(item):
            eng_name = item[0].text()
            try:
                eng_val = np.loadtxt(self.txm_eng_list[eng_name])
                plt.figure()
                plt.plot(eng_val, '.')
                plt.title(f'{eng_name}: {len(eng_val)} energies')
                plt.show()
                print(eng_val)
            except:
                msg = 'un-supported energy file'
                print(msg)
                self.tx_scan_msg.setPlainText(msg)
        else:
            msg = 'Select energy list first'
            print(msg)
            self.tx_scan_msg.setPlainText(msg)

    def remove_eng_list(self):
        item = self.lst_eng_list.selectedItems()
        if len(item):
            eng_name = item[0].text()  # 'e.g., E_01'
            del self.txm_eng_list[eng_name]
            self.lst_eng_list.takeItem(self.lst_eng_list.row(item[0]))
        self.lst_eng_list.sortItems()

    def remove_all_eng_list(self):
        self.txm_eng_list = {}
        self.lst_eng_list.clear()

    def use_current_eng(self):
        eng = self.lb_motor_pos_e.text()
        self.scan_tx['XEng'].setText(eng)

    def run_pause(self):
        try:
            msg = ''
            self.pb_pause_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_resume_scan.setStyleSheet('color: rgb(200, 50, 50);')
            self.pb_stop_scan.setStyleSheet('color: rgb(200, 50, 50);')
            self.pb_abort_scan.setStyleSheet('color: rgb(200, 50, 50);')
            self.pb_abort_scan.setEnabled(True)
            self.pb_resume_scan.setEnabled(True)
            self.pb_stop_scan.setEnabled(True)
            self.pb_pause_scan.setEnabled(False)
            QApplication.processEvents()   
            RE.request_pause()         
        except Exception as err:
            msg += str(err) + '\n'
            print(msg)
            self.tx_scan_msg.setPlainText(msg)

    def run_resume(self):
        try:
            msg = ''
            self.pb_resume_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_pause_scan.setStyleSheet('color: rgb(200, 50, 50);')     
            self.pb_stop_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_abort_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_resume_scan.setEnabled(False)
            self.pb_pause_scan.setEnabled(True)
            self.pb_stop_scan.setEnabled(False)
            self.pb_abort_scan.setEnabled(False)
            self.tx_scan_msg.setPlainText('Scan resumed ...')
            QApplication.processEvents()             
            RE.resume()            
        except Exception as err:
            msg = str(err) + '\n'
            print(msg)
            self.tx_scan_msg.setPlainText(msg)

    def run_stop(self):
        try:
            msg = ''
            self.pb_resume_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_pause_scan.setStyleSheet('color: rgb(200, 200, 200);')     
            self.pb_stop_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_abort_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_resume_scan.setEnabled(False)
            self.pb_pause_scan.setEnabled(False)
            self.pb_stop_scan.setEnabled(False)
            self.pb_abort_scan.setEnabled(False)
            self.tx_scan_msg.setPlainText('Scan Stopped ...')
            QApplication.processEvents()   
            RE.stop()
        except Exception as err:
            msg += str(err) + '\n'
            print(msg)
            self.tx_scan_msg.setPlainText(msg)

    def run_abort(self):
        try:
            msg = ''
            self.pb_resume_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_pause_scan.setStyleSheet('color: rgb(200, 200, 200);')     
            self.pb_stop_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_abort_scan.setStyleSheet('color: rgb(200, 200, 200);')
            self.pb_resume_scan.setEnabled(False)
            self.pb_pause_scan.setEnabled(False)
            self.pb_stop_scan.setEnabled(False)
            self.pb_abort_scan.setEnabled(False)
            self.tx_scan_msg.setPlainText('Scan Aborted ...')
            QApplication.processEvents()   
            RE.abort()
        except Exception as err:
            msg += str(err) + '\n'
            print(msg)
            self.tx_scan_msg.setPlainText(msg)

    def run_scan(self):
        msg = ''
        cmd = self.tx_scan_msg.toPlainText()
        print(cmd)
        try:
            self.pb_run_scan.setStyleSheet('color: rgb(200, 200, 200);')
            #self.pb_run_scan.setEnabled(False)
            self.pb_run_scan.setText('Running...\nDo not touch')
            self.pb_pause_scan.setEnabled(True)
            self.pb_pause_scan.setStyleSheet('color: rgb(200, 50, 50);')
            exec(cmd)
            if 'RE(' in cmd:
                print('\n\nscan finished\n\n')
                self.tx_scan_msg.setPlainText('\n\nscan finished\n\n')
        except Exception as err:
            msg += str(err) + '\n'
            print(msg)
            self.tx_scan_msg.setPlainText(str(msg))
            #self.pb_run_scan.setDisabled(True)
            #self.pb_run_scan.setStyleSheet('color: rgb(200, 200, 200);')
        finally:
            self.pb_run_scan.setStyleSheet('color: rgb(200, 50, 50);')
            self.pb_run_scan.setText('Run')
            self.pb_run_scan.setEnabled(True)
            self.pb_pause_scan.setEnabled(False)
            self.pos_sync()
            print(msg)
            self.tx_scan_msg.setPlainText(msg)
            try:
                sid = db[-1].start['scan_id']
                self.lb_current_sid.setText(str(sid))
            except Exception as err:
                msg += str(err) + '\n'
                print(msg)
                self.tx_scan_msg.setPlainText(msg)

    def load_scan_type_list(self, scan_type=1):
        global scan_list
        try:
            if scan_type == 1: # commonly used scan
                fpath_scan_list = '/nsls2/data/fxi-new/shared/software/fxi_control/scan_list_common.py'
                msg = f'load common scan in: 41-scans.py'
                print(msg)
                #get_ipython().run_line_magic("run", f"-i {fpath_scan_list}")
                tmp_scan_list = fxi_load_scan_list_common()
                
            if scan_type == 2: # other scans, e.g., for beamline alignment
                fpath_scan_list = '/nsls2/data/fxi-new/shared/software/fxi_control/scan_list_pzt.py'
                msg = f'load other scan in: 43-scans_pzt.py and 44-scans_other.py'
                #msg = f'load other scan in: 44-scans_other.py'
                get_ipython().run_line_magic("run", f"-i {fpath_scan_list}")
                tmp_scan_list1 = fxi_load_scan_list_pzt()
                
                fpath_scan_list = '/nsls2/data/fxi-new/shared/software/fxi_control/scan_list_other.py'
                get_ipython().run_line_magic("run", f"-i {fpath_scan_list}")
                tmp_scan_list2 = fxi_load_scan_list_other()
                tmp_scan_list = merge_dict(tmp_scan_list1, tmp_scan_list2)
                #tmp_scan_list = fxi_load_scan_list_other()
            if scan_type == 3: # customized scans, e.g., temporary created 
                fpath_scan_list = '/nsls2/data/fxi-new/shared/software/fxi_control/scan_list_user.py'
                msg = f'load user scan in: 98-user_scan.py'
                #get_ipython().run_line_magic("run", f"-i {fpath_scan_list}")
                tmp_scan_list = fxi_load_scan_list_user()
                
            scan_list = merge_dict(scan_list, tmp_scan_list)
            
            self.lst_scan.clear()
            QApplication.processEvents() 
            for k in tmp_scan_list.keys():
                name = ' '.join(t for t in k.split('_')[1:])
                self.lst_scan.addItem(name)
                print(name)
            QApplication.processEvents()  
        except Exception as err:
            msg = str(err) + '\n'
        finally:
            print(msg)
            self.tx_scan_msg.setPlainText(msg)

    def update_scan_type_list(self, scan_type=1):
        
        if scan_type == 1: # update common scan
            fname_read = self.fpath_bluesky_startup + '/41-scans.py'
            fname_write = '/nsls2/data/fxi-new/shared/software/fxi_control/scan_list_common.py'
            prepare_scan_list(fname_read, fname_write)  
            self.load_scan_type_list(1)
        if scan_type == 2: # update other+pzt scan
            #fname_read = self.fpath_bluesky_startup + '/43-scans_pzt.py'
            #fname_write = '/nsls2/data/fxi-new/shared/software/fxi_control/scan_list_pzt.py'
            #prepare_scan_list(fname_read, fname_write)  

            fname_read = self.fpath_bluesky_startup + '/44-scans_other.py'
            fname_write = '/nsls2/data/fxi-new/shared/software/fxi_control/scan_list_other.py'
            prepare_scan_list(fname_read, fname_write)  
            self.load_scan_type_list(2)
        if scan_type == 3: # update user scan
            fname_read = self.fpath_bluesky_startup + '/98-user_scan.py'
            fname_write = '/nsls2/data/fxi-new/shared/software/fxi_control/scan_list_user.py'
            prepare_scan_list(fname_read, fname_write)  
            self.load_scan_type_list(3)
        
        

    def record_scan(self):
        # need to 'check scan' first
        n = self.lst_record_scan.count()
        exist_scan_name = [self.lst_record_scan.item(i).text() for i in range(n)]
        scan_name = '_'.join(self.scan_name.split('_')[1:])
        tmp_id = np.sum([scan_name in exist_scan_name[i] for i in range(n)])

        record_scan_name = f'{scan_name}_{int(tmp_id + 1)}'
        self.txm_record_scan[record_scan_name] = self.txm_scan.copy()
        self.lst_record_scan.addItem(record_scan_name)
        self.pb_record.setDisabled(True)

    def show_recorded_scan(self):
        item = self.lst_record_scan.selectedItems()
        record_scan_name = item[0].text()
        scan_name = '_'.join(record_scan_name.split('_')[:-1])

        self.show_scan_example_sub(scan_list[f'txm_{scan_name}'])  # default view first
        self.txm_scan = self.txm_record_scan[record_scan_name].copy()
        for i in range(20):
            if self.scan_lb[f'lb_{i}'].isVisible():
                param = self.scan_lb[f'lb_{i}'].text()[:-1]  # remove ":" at end of string
                if 'eng_list' in param:
                    tmp = self.txm_scan[self.txm_scan[param]]
                    if 'np.loadtxt' in tmp:
                        val = self.txm_scan[param]
                    else:
                        val = tmp
                else:
                    val = self.txm_scan[param]
                self.scan_tx[f'tx_{i}'].setText(str(val))

        note = str(self.txm_scan['note'])
        if note[0] == '\'' or note[0] == '\"':
            note = note[1:-1]
        self.scan_tx['note'].setText(note)
        self.scan_tx['XEng'].setText(str(self.txm_scan['XEng']))
        pos = ''
        for k in self.txm_scan['pos'].keys():
            pos += f'{k},'
        self.tx_pos.setText(pos[:-1])
        self.scan_name = 'txm_' + scan_name  # this is global
        self.sample_pos = self.txm_scan['pos'].copy()
        self.check_scan()

    def remove_recorded_scan(self):
        item = self.lst_record_scan.selectedItems()
        if len(item):
            scan_name = item[0].text()
            self.lst_record_scan.takeItem(self.lst_record_scan.row(item[0]))
            del self.txm_record_scan[scan_name]
            print(f'recored scan: {scan_name} has been deleted')

    def insert_operator(self):
        if self.rd_op_repeat_s.isChecked():
            rep = int(self.tx_op_repeat.text())
            self.lst_assembled_scan.addItem(f'Repeat_{rep}')
        if self.rd_op_repeat_e.isChecked():
            self.lst_assembled_scan.addItem('End repeat')
        if self.rd_op_sleep.isChecked():
            try:
                sleep_time = float(self.tx_op_sleep.text())
            except:
                sleep_time = 0
                msg = 'sleep time need to be a number, reset sleep_time = 0'
                print(msg)
                self.tx_scan_msg.setPlainText(msg)
            self.lst_assembled_scan.addItem(f'sleep_{sleep_time}s')
        if self.rd_op_select_scan.isChecked():
            item = self.lst_record_scan.selectedItems()
            scan_name = item[0].text()
            self.lst_assembled_scan.addItem(scan_name)

    def remove_assemble_scan(self):
        item = self.lst_assembled_scan.selectedItems()
        if len(item):
            self.lst_assembled_scan.takeItem(self.lst_assembled_scan.row(item[0]))

    def remove_all_assemble_scan(self):
        self.lst_assembled_scan.clear()

    def assemble_scan_mv_up(self):
        n = self.lst_assembled_scan.count()
        item_list = [self.lst_assembled_scan.item(i).text() for i in range(n)]
        item_list_new = item_list.copy()
        item = self.lst_assembled_scan.selectedItems()
        if len(item):
            item_name = item[0].text()
            for i in range(n):
                if item_name == item_list[i]:
                    break
            if i > 0:
                item_list_new[i] = item_list[i - 1]
                item_list_new[i - 1] = item_list[i]
            self.lst_assembled_scan.clear()
            for j in range(n):
                self.lst_assembled_scan.addItem(item_list_new[j])

    def assemble_scan_mv_down(self):
        n = self.lst_assembled_scan.count()
        item_list = [self.lst_assembled_scan.item(i).text() for i in range(n)]
        item_list_new = item_list.copy()
        item = self.lst_assembled_scan.selectedItems()
        if len(item):
            item_name = item[0].text()
            for i in range(n):
                if item_name == item_list[i]:
                    break
            if i < n - 1:
                item_list_new[i] = item_list[i + 1]
                item_list_new[i + 1] = item_list[i]
            self.lst_assembled_scan.clear()
            for j in range(n):
                self.lst_assembled_scan.addItem(item_list_new[j])

    def assemble_scan_assemble(self):
        fun_name = self.tx_fun_name.text()
        if not len(fun_name):  # empty
            fun_name = 'txm_custom_scan'
        n = self.lst_assembled_scan.count()
        item_list = [self.lst_assembled_scan.item(i).text() for i in range(n)]
        loop_flag = 0  # first evaluation: "repeat" vs. "repeat_end"
        for i in range(n):  # check loop: "repeat" vs. "repeat_end"
            if "Repeat_" in item_list[i]:
                loop_flag += 1
            if "End repeat" in item_list[i]:
                loop_flag -= 1
            if loop_flag < 0:
                break
        if loop_flag != 0:
            msg = 'un-paired "repeat" and "end repeat"'
            print(msg)
            self.tx_scan_msg.setPlainText(msg)
        else:
            cmd = ''
            cmd_scan = ''
            n_repeat = 0
            rep_symbol = ['i ', 'j', 'k', 'l', 'm', 'n']
            rep_id = 0
            for i in range(n):
                item = self.lst_assembled_scan.item(i).text()
                if 'Repeat_' in item:
                    rep = item.split('_')[-1]
                    cmd_tmp = ' ' * (n_repeat * 4 + 4) + f'for {rep_symbol[rep_id]} in range ({int(rep)}):\n'
                    cmd += cmd_tmp
                    t1, t2 = '{', '}'
                    cmd += ' ' * (n_repeat * 4 + 8) + f'print(f"repeat #{t1}{rep_symbol[rep_id]}{t2}")\n'
                    n_repeat += 1
                    rep_id += 1
                elif 'End repeat' in item:
                    n_repeat -= 1
                    rep_id -= 1
                elif 'sleep' in item:
                    sleep_time = float(item[:-1].split('_')[-1])
                    #cmd += f'sleep for {sleep_time} sec ...\n'
                    cmd += ' ' * (n_repeat * 4 + 4) + f'print("sleep for {sleep_time} sec ...")\n'
                    cmd += ' ' * (n_repeat * 4 + 4) + f'yield from bps.sleep({sleep_time})\n'
                else:
                    cmd_scan = self.assemble_scan_cmd(item, n_repeat)
                    cmd += cmd_scan + '\n'

            cmd = f'def {fun_name}():\n' + cmd
            cmd_run = f'RE({fun_name}())'
            cmd += cmd_run
            self.tx_scan_msg.setPlainText(cmd)

    def assemble_scan_cmd(self, scan_name, n_repeat):
        if 'multipos' in scan_name:
            flag_multi_pos_scan = 1
        else:
            flag_multi_pos_scan = 0
        cmd = 'RE.md["scan_id"] = db[-1].start["scan_id"]\n'
        scan = self.txm_record_scan[scan_name]
        for k in scan.keys():
            if k == 'name' or k == 'pos' or k == 'XEng':
                continue
            if 'eng_list' in scan.keys():
                if k == scan['eng_list']:
                    continue
            val = scan[k]
            cmd += f'{k}={val}, '
        cmd = ' ' * (n_repeat * 4 + 4) + f'yield from {scan["name"]}({cmd[:-2]})'

        cmd_move_pos = {}
        cmd_all = ''
        if flag_multi_pos_scan == 0:
            for key in scan['pos'].keys():
                x, y = scan['pos'][key]['x'], scan['pos'][key]['y']
                z, r = scan['pos'][key]['z'], scan['pos'][key]['r']
                cmd_move_pos[key] = ' ' * (
                            n_repeat * 4 + 4) + f'yield from mv(zps.sx, {x}, zps.sy, {y}, zps.sz, {z}, zps.pi_r, {r})  #{key}'

        # get energy
        eng = scan['XEng']
        cmd_move_eng = ' ' * (n_repeat * 4 + 4) + f'yield from move_zp_ccd({eng})'
        cmd_all += cmd_move_eng + '\n'

        cmd_eng_list = ''
        if 'eng_list' in scan.keys():
            k = scan["eng_list"]
            cmd_eng_list = ' ' * (n_repeat * 4 + 4) + f'{k} = {scan[k]}'
        cmd_all += cmd_eng_list + '\n'
        if flag_multi_pos_scan == 0:
            for key in scan['pos'].keys():
                cmd_all += cmd_move_pos[key] + '\n'
                cmd_all += cmd + '\n'
        else:
            cmd_all += cmd
        return cmd_all

    def reset_sid(self):
        sid = self.tx_sid.text()
        try:
            RE.md['scan_id'] = int(sid)
            self.lb_current_sid.setText(sid)
        except Exception as err:
            msg = 'fails to reset scan_id\n' + str(err)
            print(msg)
            self.tx_scan_msg.setPlainText(msg)

    '''
    Tab 2: motors and detectors and advanced operation
    '''

    def vbox_optics(self):

        hbox_optics = self.hbox_optics_1()
        vbox_record = self.layout_record_eng_calib()

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_optics)
        vbox.addLayout(vbox_record)
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignTop)

        return vbox

    def hbox_optics_1(self):
        w = 160
        h = 180
        bkg = 'background-color: rgb(240, 240, 240);'
        h1 = 30
        # sample and XEng and DetA
        lb_1 = QLabel()
        lb_1.setText('General')
        lb_1.setFont(self.font2)
        lb_1.setFixedWidth(w)
        self.lst_op_1 = QListWidget()
        self.lst_op_1.setFixedWidth(w)
        self.lst_op_1.setFixedHeight(h)
        self.lst_op_1.setFont(self.font2)
        self.lst_op_1.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lst_op_1.itemClicked.connect(lambda: self.show_op_position(1))

        self.lst_op_1.addItem('XEng')
        self.lst_op_1.addItem('beam_current')
        self.lst_op_1.addItem('zps.sx')
        self.lst_op_1.addItem('zps.sy')
        self.lst_op_1.addItem('zps.sz')
        self.lst_op_1.addItem('zps.pi_r')
        self.lst_op_1.addItem('DetU.x')
        self.lst_op_1.addItem('DetU.y')
        self.lst_op_1.addItem('DetU.z')

        self.lb_op_1 = QLabel()
        self.lb_op_1.setFixedWidth(w)
        self.lb_op_1.setFixedHeight(h1)
        self.lb_op_1.setStyleSheet(bkg)
        self.lb_op_1.setFont(self.font2)
        vbox_1 = QVBoxLayout()
        vbox_1.addWidget(lb_1)
        vbox_1.addWidget(self.lst_op_1)
        vbox_1.addWidget(self.lb_op_1)
        vbox_1.addStretch()
        vbox_1.setAlignment(QtCore.Qt.AlignTop)

        # lens and zp and aper
        lb_2 = QLabel()
        lb_2.setText('txm optics')
        lb_2.setFont(self.font2)
        lb_2.setFixedWidth(w)
        self.lst_op_2 = QListWidget()
        self.lst_op_2.setFixedWidth(w)
        self.lst_op_2.setFixedHeight(h)
        self.lst_op_2.setFont(self.font2)
        self.lst_op_2.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lst_op_2.itemClicked.connect(lambda: self.show_op_position(2))

        self.lst_op_2.addItem('clens.x')
        self.lst_op_2.addItem('clens.y1')
        self.lst_op_2.addItem('clens.y2')
        self.lst_op_2.addItem('clens.z1')
        self.lst_op_2.addItem('clens.z2')
        self.lst_op_2.addItem('clens.p')
        self.lst_op_2.addItem('zp.x')
        self.lst_op_2.addItem('zp.y')
        self.lst_op_2.addItem('zp.z')
        self.lst_op_2.addItem('aper.x')
        self.lst_op_2.addItem('aper.y')
        self.lst_op_2.addItem('aper.z')
        self.lb_op_2 = QLabel()
        self.lb_op_2.setFixedWidth(w)
        self.lb_op_2.setFixedHeight(h1)
        self.lb_op_2.setStyleSheet(bkg)
        self.lb_op_2.setFont(self.font2)
        vbox_2 = QVBoxLayout()
        vbox_2.addWidget(lb_2)
        vbox_2.addWidget(self.lst_op_2)
        vbox_2.addWidget(self.lb_op_2)
        vbox_2.addStretch()
        vbox_2.setAlignment(QtCore.Qt.AlignTop)

        # ssa and filter
        lb_3 = QLabel()
        lb_3.setText('ssa, filter')
        lb_3.setFont(self.font2)
        lb_3.setFixedWidth(w)
        self.lst_op_3 = QListWidget()
        self.lst_op_3.setFixedWidth(w)
        self.lst_op_3.setFixedHeight(h)
        self.lst_op_3.setFont(self.font2)
        self.lst_op_3.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lst_op_3.itemClicked.connect(lambda: self.show_op_position(3))

        self.lst_op_3.addItem('ssa.v_gap')
        self.lst_op_3.addItem('ssa.v_ctr')
        self.lst_op_3.addItem('ssa.h_gap')
        self.lst_op_3.addItem('ssa.h_ctr')
        self.lst_op_3.addItem('filter1')
        self.lst_op_3.addItem('filter2')
        self.lst_op_3.addItem('filter3')
        self.lst_op_3.addItem('filter4')
        self.lb_op_3 = QLabel()
        self.lb_op_3.setFixedWidth(w)
        self.lb_op_3.setFixedHeight(h1)
        self.lb_op_3.setStyleSheet(bkg)
        self.lb_op_3.setFont(self.font2)
        vbox_3 = QVBoxLayout()
        vbox_3.addWidget(lb_3)
        vbox_3.addWidget(self.lst_op_3)
        vbox_3.addWidget(self.lb_op_3)
        vbox_3.addStretch()
        vbox_3.setAlignment(QtCore.Qt.AlignTop)

        # CM and TM
        lb_4 = QLabel()
        lb_4.setText('CM, TM')
        lb_4.setFont(self.font2)
        lb_4.setFixedWidth(w)
        self.lst_op_4 = QListWidget()
        self.lst_op_4.setFixedWidth(w)
        self.lst_op_4.setFixedHeight(h)
        self.lst_op_4.setFont(self.font2)
        self.lst_op_4.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lst_op_4.itemClicked.connect(lambda: self.show_op_position(4))

        self.lst_op_4.addItem('cm.x')
        self.lst_op_4.addItem('cm.yaw')
        self.lst_op_4.addItem('cm.y')
        self.lst_op_4.addItem('cm.p')
        self.lst_op_4.addItem('cm.r')
        self.lst_op_4.addItem('tm.x')
        self.lst_op_4.addItem('tm.yaw')
        self.lst_op_4.addItem('tm.y')
        self.lst_op_4.addItem('tm.p')
        self.lst_op_4.addItem('tm.r')
        self.lb_op_4 = QLabel()
        self.lb_op_4.setFixedWidth(w)
        self.lb_op_4.setFixedHeight(h1)
        self.lb_op_4.setStyleSheet(bkg)
        self.lb_op_4.setFont(self.font2)
        vbox_4 = QVBoxLayout()
        vbox_4.addWidget(lb_4)
        vbox_4.addWidget(self.lst_op_4)
        vbox_4.addWidget(self.lb_op_4)
        vbox_4.addStretch()
        vbox_4.setAlignment(QtCore.Qt.AlignTop)

        #dcm and pbsl
        lb_5 = QLabel()
        lb_5.setText('pbsl, dcm')
        lb_5.setFont(self.font2)
        lb_5.setFixedWidth(w)
        self.lst_op_5 = QListWidget()
        self.lst_op_5.setFixedWidth(w)
        self.lst_op_5.setFixedHeight(h)
        self.lst_op_5.setFont(self.font2)
        self.lst_op_5.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lst_op_5.itemClicked.connect(lambda: self.show_op_position(5))

        self.lst_op_5.addItem('pbsl.x_gap')
        self.lst_op_5.addItem('pbsl.x_ctr')
        self.lst_op_5.addItem('pbsl.y_gap')
        self.lst_op_5.addItem('pbsl.y_ctr')
        self.lst_op_5.addItem('dcm.eng')
        self.lst_op_5.addItem('dcm.th1')
        self.lst_op_5.addItem('dcm.th2')
        self.lst_op_5.addItem('dcm.dy2')
        self.lst_op_5.addItem('dcm.chi2')
        self.lb_op_5 = QLabel()
        self.lb_op_5.setFixedWidth(w)
        self.lb_op_5.setFixedHeight(h1)
        self.lb_op_5.setStyleSheet(bkg)
        self.lb_op_5.setFont(self.font2)
        vbox_5 = QVBoxLayout()
        vbox_5.addWidget(lb_5)
        vbox_5.addWidget(self.lst_op_5)
        vbox_5.addWidget(self.lb_op_5)
        vbox_5.addStretch()
        vbox_5.setAlignment(QtCore.Qt.AlignTop)

        # pzt
        lb_6 = QLabel()
        lb_6.setText('pzt')
        lb_6.setFont(self.font2)
        lb_6.setFixedWidth(w)
        self.lst_op_6 = QListWidget()
        self.lst_op_6.setFixedWidth(w)
        self.lst_op_6.setFixedHeight(h)
        self.lst_op_6.setFont(self.font2)
        self.lst_op_6.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lst_op_6.itemClicked.connect(lambda: self.show_op_position(6))

        self.lst_op_6.addItem('pzt_dcm_chi2.pos')
        self.lst_op_6.addItem('pzt_dcm_th2.pos')
        self.lst_op_6.addItem('pzt_tm_loadcell')
        self.lst_op_6.addItem('pzt_cm_loadcell')
        self.lb_op_6 = QLabel()
        self.lb_op_6.setFixedWidth(w)
        self.lb_op_6.setFixedHeight(h1)
        self.lb_op_6.setStyleSheet(bkg)
        self.lb_op_6.setFont(self.font2)

        vbox_6 = QVBoxLayout()
        vbox_6.addWidget(lb_6)
        vbox_6.addWidget(self.lst_op_6)
        vbox_6.addWidget(self.lb_op_6)
        vbox_6.addStretch()
        vbox_6.setAlignment(QtCore.Qt.AlignTop)

        # ic and camera
        lb_7 = QLabel()
        lb_7.setText('ic, camera')
        lb_7.setFont(self.font2)
        lb_7.setFixedWidth(w)
        self.lst_op_7 = QListWidget()
        self.lst_op_7.setFixedWidth(w)
        self.lst_op_7.setFixedHeight(h)
        self.lst_op_7.setFont(self.font2)
        self.lst_op_7.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lst_op_7.itemClicked.connect(lambda: self.show_op_position(7))

        self.lst_op_7.addItem('ic3')
        self.lst_op_7.addItem('ic4')
        self.lst_op_7.addItem('Andor')
        self.lst_op_7.addItem('detA1')
        self.lst_op_7.addItem('vlm')
        self.lst_op_7.addItem('MFS')
        self.lst_op_7.addItem('PMFS')
        self.lst_op_7.addItem('WPFS')
        self.lb_op_7 = QLabel()
        self.lb_op_7.setFixedWidth(w)
        self.lb_op_7.setFixedHeight(h1)
        self.lb_op_7.setStyleSheet(bkg)
        self.lb_op_7.setFont(self.font2)

        vbox_7 = QVBoxLayout()
        vbox_7.addWidget(lb_7)
        vbox_7.addWidget(self.lst_op_7)
        vbox_7.addWidget(self.lb_op_7)
        vbox_7.addStretch()
        vbox_7.setAlignment(QtCore.Qt.AlignTop)

        # get together
        hbox_1 = QHBoxLayout()
        hbox_1.addLayout(vbox_1)
        hbox_1.addLayout(vbox_2)
        hbox_1.addLayout(vbox_3)
        hbox_1.addLayout(vbox_4)
        hbox_1.addLayout(vbox_5)
        hbox_1.addLayout(vbox_6)
        hbox_1.addLayout(vbox_7)
        #hbox_1.addStretch()
        hbox_1.setAlignment(QtCore.Qt.AlignLeft)

        return hbox_1

    def layout_record_eng_calib(self):
        lb_empty = QLabel()
        lb_empty.setFixedHeight(10)

        lb_rec_eng_calib = QLabel()
        lb_rec_eng_calib.setFont(self.font1)
        lb_rec_eng_calib.setText('Record energy calibration position')

        self.pb_rec_eng_calib = QPushButton('record')
        self.pb_rec_eng_calib.setFont(self.font2)
        self.pb_rec_eng_calib.setFixedWidth(120)
        self.pb_rec_eng_calib.clicked.connect(self.record_eng_calib)

        self.pb_rm_eng_calib = QPushButton('remove')
        self.pb_rm_eng_calib.setFont(self.font2)
        self.pb_rm_eng_calib.setFixedWidth(120)
        self.pb_rm_eng_calib.clicked.connect(self.remove_eng_calib)

        self.pb_rm_all_eng_calib = QPushButton('remove all')
        self.pb_rm_all_eng_calib.setFont(self.font2)
        self.pb_rm_all_eng_calib.setFixedWidth(120)
        self.pb_rm_all_eng_calib.clicked.connect(self.remove_eng_calib_all)

        lb_rec_eng_id = QLabel()
        lb_rec_eng_id.setFont(self.font2)
        lb_rec_eng_id.setFixedWidth(70)
        lb_rec_eng_id.setText('Pos ID:')
        #lb_rec_eng_id.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.tx_rec_eng_id = QLineEdit('1')
        self.tx_rec_eng_id.setFont(self.font2)
        self.tx_rec_eng_id.setFixedWidth(40)

        hbox = QHBoxLayout()
        hbox.addWidget(lb_rec_eng_id)
        hbox.addWidget(self.tx_rec_eng_id)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        vbox_pb = QVBoxLayout()
        vbox_pb.addWidget(self.pb_rec_eng_calib)
        vbox_pb.addLayout(hbox)
        vbox_pb.addWidget(lb_empty)
        vbox_pb.addWidget(self.pb_rm_eng_calib)
        vbox_pb.addWidget(self.pb_rm_all_eng_calib)


        lb_rec_eng_recorded = QLabel()
        lb_rec_eng_recorded.setFont(self.font2)
        lb_rec_eng_recorded.setFixedWidth(160)
        lb_rec_eng_recorded.setText('Recorded')

        self.lst_eng_calib = QListWidget()
        self.lst_eng_calib.setFixedWidth(160)
        self.lst_eng_calib.setFixedHeight(160)
        self.lst_eng_calib.setFont(self.font2)
        self.lst_eng_calib.itemClicked.connect(self.display_calib_eng_detail)

        vbox_recorded = QVBoxLayout()
        vbox_recorded.addWidget(lb_rec_eng_recorded)
        vbox_recorded.addWidget(self.lst_eng_calib)
        vbox_recorded.setAlignment(QtCore.Qt.AlignTop)

        lb_rec_eng_detail = QLabel()
        lb_rec_eng_detail.setFont(self.font2)
        lb_rec_eng_detail.setFixedWidth(160)
        lb_rec_eng_detail.setText('Motor pos')

        self.tx_eng_calib = QPlainTextEdit()
        self.tx_eng_calib.setFixedWidth(200)
        self.tx_eng_calib.setFixedHeight(160)
        self.tx_eng_calib.setFont(self.font2)
        self.tx_eng_calib.setReadOnly(True)

        vbox_record_detail = QVBoxLayout()
        vbox_record_detail.addWidget(lb_rec_eng_detail)
        vbox_record_detail.addWidget(self.tx_eng_calib)
        vbox_record_detail.setAlignment(QtCore.Qt.AlignTop)

        lb_empty2 = QLabel()

        hbox2 = QHBoxLayout()
        hbox2.addLayout(vbox_pb)
        hbox2.addLayout(vbox_recorded)
        hbox2.addLayout(vbox_record_detail)
        hbox2.addStretch()
        hbox2.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_rec_eng_calib)
        vbox.addLayout(hbox2)
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignTop)

        hbox_all = QHBoxLayout()
        hbox_all.addLayout(vbox)
        hbox_all.addWidget(lb_empty2)
        hbox_all.addStretch()
        hbox_all.setAlignment(QtCore.Qt.AlignLeft)
        return hbox_all


    def record_eng_calib(self):
        global CALIBER
        try:
            eng_id = int(self.tx_rec_eng_id.text())
            record_calib_pos_new(eng_id)
            self.display_calib_eng_only()
        except Exception as err:
            print(err)


    def remove_eng_calib(self):
        item = self.lst_eng_calib.selectedItems()
        if len(item):
            eng_id = int(item[0].text().split('_')[0][3:])
            self.lst_eng_calib.takeItem(self.lst_eng_calib.row(item[0]))
            print(f'remove energy caliberation point {eng_id}')
            remove_caliber_pos(eng_id)
            self.display_calib_eng_only()

    def remove_eng_calib_all(self):
        n = self.lst_eng_calib.count()
        for i in range(n):
            item = self.lst_eng_calib.item(i)
            item_name = item.text()
            eng_id = int(item_name.split('_')[3:])
            remove_caliber_pos(eng_id)
        self.display_calib_eng_only()


    def get_caliber_eng(self):
        calib_eng_list = []
        calib_eng_id = []
        for k in CALIBER.keys():
            if 'XEng' in k:
                calib_eng_id.append(int(k.split('_')[1][3:]))
                calib_eng_list.append(CALIBER[k])
        return calib_eng_id, calib_eng_list


    def display_calib_eng_only(self):
        read_calib_file_new()
        self.lst_eng_calib.clear()
        calib_eng_id, calib_eng_list = self.get_caliber_eng()
        for i in range(len(calib_eng_id)):
            eng_id = calib_eng_id[i]
            calib_eng = calib_eng_list[i]
            txt = f'pos{eng_id}_{calib_eng:2.4f} keV'
            self.lst_eng_calib.addItem(txt)
        '''    
        for k in CALIBER.keys():
            if 'XEng' in k:
                eng_id = int(k.split('_')[1][3:])
                calib_eng = CALIBER[k]
                txt = f'pos{eng_id}_{calib_eng:2.4f} keV'
                self.lst_eng_calib.addItem(txt)
        '''
        # update label information
        self.lst_eng_calib.sortItems()
        eng_list_sort = np.sort(calib_eng_list)
        eng_lb = '(calib. at: '
        for eng in eng_list_sort:
            eng_lb += f'{eng:2.1f}, '
        eng_lb += 'keV)'
        self.lb_note.setText(eng_lb)


    def display_calib_eng_detail(self):
        item = self.lst_eng_calib.selectedItems()
        pos = item[0].text()
        eng_id = pos.split('_')[0]
        txt = ''
        keys = np.sort(list(CALIBER.keys()))[::-1]
        for k in keys:
            k0 = k.split('_')
            k1 = '_'.join(i for i in k0[:-1])
            k2 = k0[-1]
            if k2 == eng_id:
                txt += f'{k1:<10} = {CALIBER[k]:5.4f}\n'
        #print(f'pos:\n{txt}')
        self.tx_eng_calib.setPlainText(txt)





    def show_op_position(self, n):
        motor = motor_list(n)
        try:
            if n == 1:
                item = self.lst_op_1.selectedItems()
                mname = item[0].text()
                try:
                    val = motor[mname].position
                except:
                    val = motor[mname].get()
                self.lb_op_1.setText(f'{val:5.6f}')
            if n == 2:
                item = self.lst_op_2.selectedItems()
                mname = item[0].text()
                val = motor[mname].position
                self.lb_op_2.setText(f'{val:5.6f}')
            if n == 3:
                item = self.lst_op_3.selectedItems()
                mname = item[0].text()
                if 'filter' in mname:
                    val = motor[mname].get()
                    if val == 0:
                        val = 'Out'
                    else:
                        val = 'In'
                    self.lb_op_3.setText(val)
                else:
                    val = motor[mname].position
                    self.lb_op_3.setText(f'{val:5.6f}')
            if n == 4:
                item = self.lst_op_4.selectedItems()
                mname = item[0].text()
                val = motor[mname].position
                self.lb_op_4.setText(f'{val:5.6f}')
            if n == 5:
                item = self.lst_op_5.selectedItems()
                mname = item[0].text()
                val = motor[mname].position
                self.lb_op_5.setText(f'{val:5.6f}')
            if n == 6:
                item = self.lst_op_6.selectedItems()
                mname = item[0].text()
                val = motor[mname].value
                self.lb_op_6.setText(f'{val:5.6f}')
            if n == 7:
                item = self.lst_op_7.selectedItems()
                mname = item[0].text()
                if 'ic' in mname:
                    val = motor[mname].value
                    self.lb_op_7.setText(f'{val:5.6e}')
                else:
                    val = 'No value available'
                    self.lb_op_7.setText(val)
            QApplication.processEvents()         
        except Exception as err:
            print(err)


def merge_dict(dict1, dict2):
    res = {**dict1, **dict2}
    return res

def prepare_scan_list(fname_read, fname_write='scan_list_test.py'):
    #fname_read = '/nsls2/data/fxi-new/shared/config/bluesky/profile_collection/startup/41-scans.py'
    source = open(fname_read).read()
    fun = [f.name for f in ast.parse(source).body if isinstance(f, ast.FunctionDef)]
    fun_scan = [f for f in np.sort(fun) if 'scan' in f or 'xanes' in f] # funciton name with "scan"
    
    space4 = ' ' * 4
    file_lines = []
    fname_write_short = fname_write.split('/')[-1]
    file_lines.append(f'def fxi_load_{fname_write_short.split(".")[0]}():')
    file_lines.append(space4 + 'scan_list = {}')
    
    for i in range(len(fun_scan)):
        fun_name = fun_scan[i]
        fun_lines = convert_fun_dict(fun_name)
        for j in range(len(fun_lines)):
            file_lines.append(fun_lines[j])
        file_lines.append('\n')
    
    for i in range(len(fun_scan)):
        fun_name = fun_scan[i]
        file_lines.append(space4 + f'scan_list["txm_{fun_name}"] = txm_{fun_name}')

    file_lines.append(space4 + 'return scan_list')
    file_lines = convert_epics_to_string(file_lines)
    file_lines = convert_fpath_to_string(file_lines)
    with open(fname_write, 'w') as f:
        f.write(f'\n'.join(file_lines))


def convert_fun_dict(fun_name):
    #single_fun = inspect.getfullargspec(eval(fun_name))
    signature = inspect.signature(eval(fun_name))
    '''
    fun_arg = single_fun[0]
    fun_arg_value = single_fun[3]
    '''
    lines = []
    space4 = ' '*4
    
    lines.append(space4 + 'txm_' + fun_name + ' = {')

    for k, v in signature.parameters.items():
        if k == 'md' or k == 'note' or k == 'binning':
            continue
        if v.default is inspect.Parameter.empty:
            if 'detectors' in k or 'eng_list' in k or 'filter' in k:
                val = '[]'
            else:
                val = 'None'
        else:
            val = v.default
        l = f"'{k}': {str(val)}, "
        lines.append(space4 * 2 + l)     
    lines.append(space4 * 2 + "'introduction': ''' Description:\n '''")
    lines.append(space4 + '}')
    return lines


def convert_fpath_to_string(file_lines):
    lines_copy = file_lines.copy()
    idx = []
    for i, l in enumerate(file_lines):
        if '/' in l:
            idx.append(i)
    for i in idx:
        l = file_lines[i]
        arg_name = l.split(':')[0]
        arg_val = l[len(arg_name)+1:].strip().replace(',', '')
        lines_copy[i] = arg_name + ': ' + '"' + arg_val + '",'
    return lines_copy


def convert_epics_to_string(file_lines):
    lines_copy = file_lines.copy()
    idx = []
    for i, l in enumerate(file_lines):
        if 'Epics' in l:
            idx.append(i)

    for i in idx:
        l = file_lines[i]
        arg_name = l.split(':')[0]
        lsplit = l.split(',')
        for j, ll in enumerate(lsplit):
            if 'name' in ll:
                break
        arg_val = ll.split('=')[-1]
        lines_copy[i] = arg_name + ': ' + arg_val + ','  
    return lines_copy

def run_main():
    app = QApplication(sys.argv)
    txm = App()
    txm.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_main()
    '''
    t = threading.Thread(target=run_main)
    t.daemon = True
    t.start()
    
    app = QApplication(sys.argv)
    txm = App()
    txm.show()
    sys.exit(app.exec_())
    '''
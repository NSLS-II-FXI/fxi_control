import sys
import matplotlib.pyplot as plt
import numpy as np
import os
import threading
import time
import json
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSignal, pyqtSlot, QProcess, QTextCodec
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QRadioButton, QApplication, QWidget, QFrame,
                             QLineEdit, QPlainTextEdit, QWidget, QPushButton, QLabel, QCheckBox, QGroupBox,
                             QScrollBar, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QTextBrowser,
                             QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea,
                             QSlider, QComboBox, QButtonGroup, QMessageBox, QSizePolicy)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QColor
from qtconsole.rich_jupyter_widget import RichIPythonWidget, RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
#from IPython.lib import guisupport
from qtconsole.manager import QtKernelManager
#from IPython import get_ipython # already imported from bsui
#from scan_list import *
import threading
import bluesky.plan_stubs as bps
import ast
import numpy as np
from epics import caget, caput
from inspect import getmembers, isfunction

#from extract_scan_list import prepare_scan_list, convert_fun_dict
from scan_list_common import fxi_load_scan_list_common
from scan_list_other import fxi_load_scan_list_other
from scan_list_user import fxi_load_scan_list_user
from scan_list_pzt import fxi_load_scan_list_pzt

#get_ipython().run_line_magic("run", "-i /nsls2/data/fxi-new/shared/software/fxi_control/scan_list.py")

global txm, CALIBER, scan_list
scan_list = {}

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

class OutputWrapper(QObject):
    outputWritten = QtCore.pyqtSignal(object, object)
    def __init__(self, parent, stdout=True):
        super().__init__(parent)
        if stdout:
            self._stream = sys.stdout
            sys.stdout = self
        else:
            self._stream = sys.stderr
            sys.stderr = self
        self._stdout = stdout

    def write(self, text):
        self._stream.write(text)
        self.outputWritten.emit(text, self._stdout)

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def __del__(self):
        import sys
        try:
            if self._stdout:
                sys.stdout = self._stream
            else:
                sys.stderr = self._stream
        except AttributeError:
            pass

class Stream(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)
    def write(self, text):
        self.newText.emit(str(text))
    '''
    def flush(self):
        sys.stdout.flush()
    '''

class ConsoleWidget(RichIPythonWidget):
    def __init__(self, namespace={}, customBanner=None, *args, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)

        if customBanner is not None:
            self.banner = customBanner
     
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
        
        self.set_default_style('linux')
        #self.font = QtGui.QFont(self.font.family(), 16);
                
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

class Get_motor_reading(QThread):
    current_position = pyqtSignal(float)
    def __init__(self, motor):
        super().__init__()
        self.motor = motor
    def run(self):
        i = 0
        while True:
            if 'shutter' in self.motor.motor_name:
                status = self.motor.mot.status.value
                if 'Not' in status:
                    current_pos = 1 # shutter closed
                else:
                    current_pos = 0 # shutter open
            elif 'filter' in self.motor.motor_name:
                current_pos = self.motor.mot.value
            elif 'txm_zp_pix' in self.motor.motor_name:
                current_pos = DetU.z.position / zp.z.position - 1
            else:
                if hasattr(self.motor.mot, 'position'):
                    current_pos = self.motor.mot.position
                elif hasattr(self.motor.mot, 'pos.get'):
                    current_pos = self.motor.mot.pos.get()
                elif hasattr(self.motor.mot, 'value'):
                    current_pos = self.motor.mot.pos.get()
                elif hasattr(self.motor.mot, 'status.value'):
                    current_pos = self.motor.mot.status_value
                else:
                    continue
            self.current_position.emit(current_pos)
            i += 1
            time.sleep(0.2)
            
class Shutter():
    def __init__(self, obj):
        
        self.obj = obj
        self.font1 = QtGui.QFont('Arial', 12, QtGui.QFont.Bold)
        self.font2 = QtGui.QFont('Arial', 12, QtGui.QFont.Normal)
        self.motor_name = 'shutter'
        self.mot = eval(self.motor_name)
        self.init_motor_component()
        self.init_connect_function()

    def init_motor_component(self):
        self.button_pb_open_shutter = self.pb_open_shutter()
        self.button_pb_close_shutter = self.pb_close_shutter()
        self.label_lb_beam_current = self.lb_beam_current()
        self.label_lb_shutter_status = self.lb_shutter_status()

    def init_connect_function(self):
        self.button_pb_open_shutter.clicked.connect(self.fun_open_shutter)
        self.button_pb_close_shutter.clicked.connect(self.fun_close_shutter)


    def pb_open_shutter(self):
        self.obj.open_shutter = FixObj(QPushButton, self.font2, 'Open shutter', 120, 40).run()
        self.obj.open_shutter.setStyleSheet('color: rgb(50, 200, 50);')
        return self.obj.open_shutter

    def pb_close_shutter(self):
        self.obj.close_shutter = FixObj(QPushButton, self.font2, 'Close shutter', 120, 40).run()
        self.obj.close_shutter.setStyleSheet('color: rgb(200, 50, 50);')
        return self.obj.close_shutter

    def lb_beam_current(self):
        self.obj.lb_beam_current = FixObj(QLabel, self.font1, '', 120).run()
        self.obj.lb_beam_current.setStyleSheet('color: rgb(200, 50, 50);')
        return self.obj.lb_beam_current

    def lb_shutter_status(self):
        self.obj.lb_shutter_status = FixObj(QLabel, self.font1, '', 120).run()
        self.obj.lb_shutter_status.setStyleSheet('color: rgb(200, 50, 50);')
        return self.obj.lb_shutter_status

    def layout(self):
        lb_beam = FixObj(QLabel, self.font1, 'Beam current:', 120).run()
        lb_shutter = FixObj(QLabel, self.font1, 'Shutter status:', 120).run()

        hbox_beam = QHBoxLayout()
        hbox_beam.addWidget(lb_beam)
        hbox_beam.addWidget(self.label_lb_beam_current)
        hbox_beam.setAlignment(QtCore.Qt.AlignLeft)

        hbox_shutter = QHBoxLayout()
        hbox_shutter.addWidget(lb_shutter)
        hbox_shutter.addWidget(self.label_lb_shutter_status)
        hbox_shutter.setAlignment(QtCore.Qt.AlignLeft)

        vbox_shutter_click = QVBoxLayout()
        vbox_shutter_click.addWidget(self.button_pb_open_shutter)
        vbox_shutter_click.addWidget(self.button_pb_close_shutter)
        vbox_shutter_click.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_beam)
        vbox.addLayout(hbox_shutter)
        vbox.addLayout(vbox_shutter_click)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox

    def fun_open_shutter(self):
        try:
            self.button_pb_open_shutter.setDisabled(True)
            RE(_open_shutter())
        except Exception as err:
            print(err)
        finally:
            self.button_pb_open_shutter.setDisabled(False)

    def fun_close_shutter(self):
        try:
            self.button_pb_close_shutter.setDisabled(True)
            RE(_close_shutter())
        except Exception as err:
            print(err)
        finally:
            self.button_pb_close_shutter.setDisabled(False)

    def fun_update_beam_current(self):
        beam_value = beam_current.read()['beam_current']['value']
        self.label_lb_beam_current.setText(f'{beam_value:3.1f} mA')
    
    def fun_update_shutter_status(self, shutter_value):
        #shutter_value = shutter_status.read()['shutter_status']['value']
        if shutter_value == 1:
            sh_status = 'Closed' 
            stylesheet = 'color: rgb(200, 50, 50)' # display red
        else:
            sh_status = 'Open' 
            stylesheet = 'color: rgb(50, 200, 50)' # display green
        self.label_lb_shutter_status.setText(sh_status)
        self.label_lb_shutter_status.setStyleSheet(stylesheet)
        
    def fun_update_status(self, shutter_value):
        self.fun_update_beam_current()
        self.fun_update_shutter_status(shutter_value)

class TXM_ZP_mag():
    def __init__(self, obj):
        self.obj = obj
        self.motor_name = 'txm_zp_pix'
        self.font1 = QtGui.QFont('Arial', 12, QtGui.QFont.Bold)
        self.font2 = QtGui.QFont('Arial', 12, QtGui.QFont.Normal)
        self.init_motor_component()

    def init_motor_component(self):
        self.lb_sep1 = FixObj(QLabel, self.font2, '', 0, 10).run()
        self.lb_sep2 = FixObj(QLabel, self.font2, '', 0, 10).run()
        self.lb_current_mag = FixObj(QLabel, self.font2, 'TXM Mag:', 80).run()
        self.obj.lb_current_mag = FixObj(QLabel, self.font2, '', 80).run()
        self.lb_zp_mag = FixObj(QLabel, self.font2, 'ZP Mag:', 80).run()
        self.obj.lb_zp_mag = FixObj(QLabel, self.font2, '', 80).run()
        self.lb_pix_size = FixObj(QLabel, self.font2, 'Pixel:', 80).run()
        self.obj.lb_pix_size = FixObj(QLabel, self.font2, '', 80).run()

    def layout(self):
        hbox_zp_mag = QHBoxLayout()
        hbox_zp_mag.addWidget(self.lb_zp_mag)
        hbox_zp_mag.addWidget(self.obj.lb_zp_mag)
        hbox_zp_mag.setAlignment(QtCore.Qt.AlignTop)

        hbox_txm_mag = QHBoxLayout()
        hbox_txm_mag.addWidget(self.lb_current_mag)
        hbox_txm_mag.addWidget(self.obj.lb_current_mag)
        hbox_txm_mag.setAlignment(QtCore.Qt.AlignTop)
        
        hbox_txm_pix = QHBoxLayout()
        hbox_txm_pix.addWidget(self.lb_pix_size)
        hbox_txm_pix.addWidget(self.obj.lb_pix_size)
        hbox_txm_pix.setAlignment(QtCore.Qt.AlignTop)

        vbox_pix_mag = QVBoxLayout()
        vbox_pix_mag.addLayout(hbox_zp_mag)
        vbox_pix_mag.addWidget(self.lb_sep1)
        vbox_pix_mag.addLayout(hbox_txm_mag)
        vbox_pix_mag.addWidget(self.lb_sep2)
        vbox_pix_mag.addLayout(hbox_txm_pix)
        vbox_pix_mag.setAlignment(QtCore.Qt.AlignCenter)
        return vbox_pix_mag

    def fun_update_status(self, txm_mag):
        
        self.obj.lb_current_mag.setText(f'{txm_mag*GLOBAL_VLM_MAG:3.2f}')
        self.obj.lb_zp_mag.setText(f'{txm_mag:3.2f}')
        self.obj.lb_pix_size.setText(f'{6500./txm_mag/GLOBAL_VLM_MAG:2.2f} nm')
        #self.obj.lb_current_mag.setText(f'{GLOBAL_MAG:3.2f}')
        #self.obj.lb_zp_mag.setText(f'{GLOBAL_MAG/GLOBAL_VLM_MAG:3.2f}')
        #self.obj.lb_pix_size.setText(f'{6500./GLOBAL_MAG:2.2f} nm')


class Motor_base():
    def __init__(self, obj,  motor_name, motor_label='',unit='um'):
        super().__init__()
        self.obj = obj
        self.font1 = QtGui.QFont('Arial', 12, QtGui.QFont.Bold)
        self.font2 = QtGui.QFont('Arial', 12, QtGui.QFont.Normal)
        self.motor_name = motor_name
        self.motor_label = motor_label if len(motor_label) else motor_name
        self.unit = unit
        self.mot = eval(motor_name)
        self.init_motor_component()
        self.init_connect_function()        

    def init_motor_component(self):
        self.editor_setpos = self.tx_editor_setpos()        
        self.label_motor_pos = self.lb_label_motor_pos()
        self.button_step_plus = self.pb_button_step_plus()
        self.button_step_minus = self.pb_button_step_minus()
        self.editor_step_size = self.tx_editor_step_size()

    def init_connect_function(self): 
        self.editor_setpos.returnPressed.connect(self.fun_move_to_pos)
        self.button_step_plus.clicked.connect(lambda: self.fun_move_plus_minus('plus'))
        self.button_step_minus.clicked.connect(lambda: self.fun_move_plus_minus('minus'))   
   
    def tx_editor_setpos(self):
        self.obj.tx_setpos = FixObj(QLineEdit, self.font2, '0', 80).run()
        self.obj.tx_setpos.setValidator(QDoubleValidator())
        return self.obj.tx_setpos
    
    def lb_label_motor_pos(self):
        self.obj.lb_motor_pos = FixObj(QLabel, self.font2, '', 80).run()
        return self.obj.lb_motor_pos

    def pb_button_step_plus(self):
        self.obj.pb_motor_plus = FixObj(QPushButton, self.font2, '+', 40).run()
        return self.obj.pb_motor_plus
    
    def pb_button_step_minus(self):
        self.obj.pb_motor_minus = FixObj(QPushButton, self.font2, '-', 40).run()
        return self.obj.pb_motor_minus
        
    def tx_editor_step_size(self):
        self.obj.tx_step = FixObj(QLineEdit, self.font2, '', 60).run()
        self.obj.tx_step.setValidator(QDoubleValidator(decimals=3))  
        return self.obj.tx_step

    def lb_unit(self):
        lb_unit1 = FixObj(QLabel, self.font2, self.unit, 50).run()
        lb_unit2 = FixObj(QLabel, self.font2, self.unit, 50).run()
        lb_unit3 = FixObj(QLabel, self.font2, self.unit, 30).run()
        lb_unit4 = FixObj(QLabel, self.font2, self.unit, 30).run()
        return [lb_unit1, lb_unit2, lb_unit3, lb_unit4]

    def fun_check_pos_limit(self):
        try:
            limit = self.mot.limits
            l_l = float(limit[0])
            l_h = float(limit[1])
            flag = 0
            try:
                val = np.float(self.editor_setpos.text())
            except:
                val = np.float(self.label_motor_pos.text())
            if abs(l_l - l_h) < 0.01: # l_l == l_h means not limit:
                flag = 1
            else: 
                if val >= l_l and val <= l_h:
                    flag = 1
                else:
                    flag = 0
        except: # limit is not found for the motor
            try:
                val = np.float(self.editor_setpos.text())
            except:
                val = np.float(self.label_motor_pos.text())
            flag = 1
        return flag, val

    def fun_move_to_pos(self):
        flag, val = self.fun_check_pos_limit()
        if flag:
            try:
                self.editor_setpos.setDisabled(True)
                #RE(mv(self.mot, val))
                caput(self.mot.prefix, val)                
            except:
                msg = f'fails to move {self.motor_name}'
                print(msg)
                self.obj.tx_scan_msg.setPlainText(msg)
            finally:
                self.editor_setpos.setEnabled(True)
                try:
                    val_rb = self.mot.position
                except:
                    val_rb = self.mot.pos.get() # for pzt_dcm_th2, pzt_dcm_chi2
                self.label_motor_pos.setText(f'{val_rb:4.4f}')

    def fun_move_plus_minus(self, direction='plus'):
        try:
            ss = float(self.editor_step_size.text())
        except:
            ss = 0
            self.editor_step_size.setText('0')
        '''
        try:
            current_pos = float(self.editor_setpos.text())
        except:
            current_pos = self.mot.position
        '''
        current_pos = self.mot.position
        if direction == 'plus':
            self.editor_setpos.setText(f'{(current_pos + ss):4.3f}')
        elif direction == 'minus':
            self.editor_setpos.setText(f'{(current_pos - ss):4.3f}')
        else:
            self.editor_setpos.setText(f'{(current_pos):4.3f}')       
        self.fun_move_to_pos()    
    
    def fun_update_status(self, current_pos):
        self.label_motor_pos.setText(f'{current_pos:4.4f}')
    
class Motor_layout(Motor_base):
    def __init__(self, obj, motor_name, motor_label='', unit='um'):
        super().__init__(obj, motor_name, motor_label, unit)   
        self.button_reset_reading = self.pb_button_reset_reading()
        self.editor_reset_reading = self.tx_editor_reset_reading()
        self.init_motor_component_motor()
        self.init_connect_function_motor()
        self.init_pos_display_motor()
 
    def init_motor_component_motor(self):
        self.button_reset_reading = self.pb_button_reset_reading()
        self.editor_reset_reading = self.tx_editor_reset_reading()

    def init_connect_function_motor(self): 
        self.button_reset_reading.clicked.connect(self.fun_reset_reading)
     
    def init_pos_display_motor(self):
        current_pos = self.mot.position
        step_size = self.mot.step_size.get()
        self.label_motor_pos.setText(f'{current_pos:4.4f}')
        self.editor_setpos.setText(f'{current_pos:4.4f}')
        self.editor_reset_reading.setText((f'{current_pos:4.4f}'))
        self.editor_step_size.setText('0')

    def init_pos_display_sample(self):
        pass

    def pb_button_reset_reading(self):
        self.obj.pb_set_read = FixObj(QPushButton, self.font2, 'Reset to:', 110).run()
        return self.obj.pb_set_read

    def tx_editor_reset_reading(self):
        self.obj.tx_set_read = FixObj(QLineEdit, self.font2, '', 80).run()
        self.obj.tx_set_read.setValidator(QDoubleValidator()) 
        return self.obj.tx_set_read

    def fun_reset_reading(self):
        #mot = eval(self.motor_name)
        try:
            val = float(self.editor_reset_reading.text())
        except:
            val = self.mot.position
        RE(mv(self.mot.motor_calib, 1)) # change calibration to "SET"
        RE(mv(self.mot, val))
        RE(mv(self.mot.motor_calib, 0))
        self.init_pos_display_sample()
        #self.label_motor_pos.setText(f'{val:4.4f}')

    def layout(self):
        lb_empty = FixObj(QLabel, None, '', 10).run()
        
        lb_motor = FixObj(QLabel, self.font1, self.motor_label + ':', 75).run()
        lb_motor.setAlignment(QtCore.Qt.AlignVCenter)
        lb_unit = self.lb_unit()
        self.step_unit = lb_unit[2]
        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.label_motor_pos)
        hbox.addWidget(lb_unit[0])
        hbox.addWidget(self.editor_setpos)
        hbox.addWidget(lb_unit[1])

        hbox.addWidget(self.button_step_minus)
        hbox.addWidget(self.editor_step_size)
        hbox.addWidget(self.step_unit)
        hbox.addWidget(self.button_step_plus)
        hbox.addWidget(lb_empty)

        hbox.addWidget(self.button_reset_reading)
        hbox.addWidget(self.editor_reset_reading)
        #hbox.addWidget(lb_unit[3])
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

class PZT_th2_chi2(Motor_layout):
    def __init__(self, obj, motor_name, motor_label, unit='um'):
        super().__init__(obj, motor_name, motor_label, unit)
        #self.init_connect_function_pzt()
        self.init_pos_display_motor()
    '''
    def init_connect_function(self): 
        self.editor_setpos.returnPressed.connect(self.fun_move_to_pos)
        self.button_step_plus.clicked.connect(lambda: self.fun_move_plus_minus('plus'))
        self.button_step_minus.clicked.connect(lambda: self.fun_move_plus_minus('minus'))   
    '''

    def init_pos_display_motor(self): # overload function in super()
        current_pos = self.mot.pos.get()
        step_size = self.mot.step_size.get()
        self.label_motor_pos.setText(f'{current_pos:4.4f}')
        self.editor_setpos.setText(f'{current_pos:4.4f}')
        self.editor_step_size.setText(f'{step_size:4.4f}')

    def fun_move_plus_minus(self, direction='plus'):
        try:
            ss = float(self.editor_step_size.text())
        except:
            ss = 0
            self.editor_step_size.setText('0')
        current_pos = self.mot.get()[0]
        if direction == 'plus':
            self.editor_setpos.setText(f'{(current_pos + ss):4.3f}')
        elif direction == 'minus':
            self.editor_setpos.setText(f'{(current_pos - ss):4.3f}')
        else:
            self.editor_setpos.setText(f'{(current_pos):4.3f}')        
        self.fun_move_to_pos()  

    def fun_move_to_pos(self):
        try:
            val = np.float(self.editor_setpos.text())
        except:
            val = np.float(self.label_motor_pos.text())
        pv = self.mot.prefix + 'SET_POSITION.A'
        caput(pv, val)

    def layout(self):
        lb_empty = FixObj(QLabel, None, '', 10).run()
        lb_motor = FixObj(QLabel, self.font1, self.motor_label+':', 75).run()
        lb_motor.setAlignment(QtCore.Qt.AlignVCenter)
        lb_unit = self.lb_unit()

        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.label_motor_pos)
        hbox.addWidget(lb_unit[0])
        hbox.addWidget(self.editor_setpos)
        hbox.addWidget(lb_unit[1])

        hbox.addWidget(self.button_step_minus)
        hbox.addWidget(self.editor_step_size)
        hbox.addWidget(lb_unit[2])
        hbox.addWidget(self.button_step_plus)
        hbox.addWidget(lb_empty)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

class DCM_th2_chi2(Motor_layout):
    def __init__(self, obj, motor_name, motor_label, unit='deg'):
        super().__init__(obj, motor_name, motor_label, unit)
        # motor_name = dcm_th2 / dcm_chi2
        self.init_motor_component_dcm()
        self.init_connect_function_dcm()
        self.init_pos_display_motor_dcm()
        
    def init_motor_component_dcm(self):
        self.button_feedback_enable = self.pb_button_feedback_enable()
        self.editor_feedback_val = self.tx_editor_feedback_val()
        
    def init_connect_function_dcm(self):
        self.button_feedback_enable.clicked.connect(self.fun_enable_feedback)
        self.editor_feedback_val.returnPressed.connect(self.fun_change_feedback_val)

    def init_pos_display_motor_dcm(self):
        feedback_val = self.mot.feedback.get()
        feedback_status = self.mot.feedback_enable.get()
        self.editor_feedback_val.setText(f'{feedback_val:2.6f}')
        if feedback_status == 1:
            self.button_feedback_enable.setText('Feedback On')
            self.button_feedback_enable.setStyleSheet('color: rgb(200, 50, 50);')
        else:
            self.button_feedback_enable.setText('Feedback Off')
            self.button_feedback_enable.setStyleSheet('color: rgb(50, 50, 50);')
        
    def fun_enable_feedback(self): 
        # check feedback on motor: dcm_th2_/ dcm_chi2
        current_feedback_val = self.mot.feedback.get()
        current_feedback_status = self.mot.feedback_enable.get() # 1:on  0:off
        try:
            set_feedback_val = float(self.editor_feedback_val.text())
        except:
            set_feedback_val = current_feedback_val
        set_feedback_status = 1 - current_feedback_status
        RE(mv(self.mot.feedback, set_feedback_val))
        RE(mv(self.mot.feedback_enable, set_feedback_status))
        new_feedback_status = self.mot.feedback_enable.get()
        self.fun_update_feedback_status(new_feedback_status)
    
    def fun_update_feedback_status(self, new_feedback_status):
        #new_feedback_status = self.mot.feedback_enable.get()
        if new_feedback_status == 1:
            self.button_feedback_enable.setText('Feedback On')
            self.button_feedback_enable.setStyleSheet('color: rgb(200, 50, 50)')
        else:
            self.button_feedback_enable.setText('Feedback Off')
            self.button_feedback_enable.setStyleSheet('color: rgb(50, 50, 50)')

    def fun_update_status(self, current_pos):
        self.label_motor_pos.setText(f'{current_pos:4.4f}')
        new_feedback_status = self.mot.feedback_enable.get()
        self.fun_update_feedback_status(new_feedback_status)
 

    def fun_change_feedback_val(self):
        current_feedback_val = self.mot.feedback.get()
        current_feedback_status = self.mot.feedback_enable.get() # 1:on  0:off
        if current_feedback_status == 1: # feedback is on
            RE(mv(self.mot.feedback, set_feedback_val))

    def pb_button_feedback_enable(self):
        self.obj.pb_button_feedback_enable = FixObj(QPushButton, self.font2, 'Feedback On', 110).run()
        return self.obj.pb_button_feedback_enable

    def tx_editor_feedback_val(self):
        self.obj.tx_feedback_val = FixObj(QLineEdit, self.font2, '', 75).run()
        self.obj.tx_feedback_val.setValidator(QDoubleValidator()) 
        return self.obj.tx_feedback_val

    def fun_update_status(self, current_pos):
        self.label_motor_pos.setText(f'{current_pos:4.6f}')

    def layout(self):
        lb_empty = QLabel()
        lb_empty.setFixedWidth(10)
        lb_motor = FixObj(QLabel, self.font1, self.motor_label + ':', 75).run()
        lb_motor.setAlignment(QtCore.Qt.AlignVCenter)
        lb_unit = self.lb_unit()

        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.label_motor_pos)
        hbox.addWidget(lb_unit[0])
        hbox.addWidget(self.editor_setpos)
        hbox.addWidget(lb_unit[1])

        hbox.addWidget(self.button_step_minus)
        hbox.addWidget(self.editor_step_size)
        hbox.addWidget(lb_unit[2])
        hbox.addWidget(self.button_step_plus)
        hbox.addWidget(lb_empty)

        hbox.addWidget(self.button_feedback_enable)
        hbox.addWidget(self.editor_feedback_val)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

class Sample_motor_layout(Motor_layout):
    def __init__(self, obj, motor_name, motor_label='', unit='um'):
        super().__init__(obj, motor_name, motor_label, unit) 
        self.init_motor_component_sample()
        self.init_pos_display_sample()

    def init_motor_component_sample(self):
        self.label_lb_pos_limit = self.lb_pos_limit()

    def init_pos_display_sample(self):
        try:
            low_limit = self.mot.low_limit.get()
            high_limit = self.mot.high_limit.get()
            self.label_lb_pos_limit.setText(f'({low_limit:4.0f}, {high_limit:4.0f})')
        except:
            pass  
    
    def lb_pos_limit(self):
        self.obj.lb_limit = FixObj(QLabel, self.font2, '(-4000, 4000)', 120).run()
        return self.obj.lb_limit 

    def pb_button_reset_reading(self):
        self.obj.pb_set_read = FixObj(QPushButton, self.font2, 'Reset to:', 100).run()
        self.obj.pb_set_read.setVisible(False)
        return self.obj.pb_set_read

    def tx_editor_reset_reading(self):
        self.obj.tx_set_read = FixObj(QLineEdit, self.font2, '', 80).run()
        self.obj.tx_set_read.setValidator(QDoubleValidator()) 
        self.obj.tx_set_read.setVisible(False)
        return self.obj.tx_set_read


    def layout(self):
        lb_empty = FixObj(QLabel, None, '', 10).run()
        lb_motor = FixObj(QLabel, self.font1, self.motor_label + ':', 75).run()
        lb_unit = self.lb_unit()
        self.step_unit = lb_unit[2]

        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.label_motor_pos)
        hbox.addWidget(lb_unit[0])
        hbox.addWidget(self.editor_setpos)
        hbox.addWidget(lb_unit[1])
        hbox.addWidget(self.label_lb_pos_limit)
        hbox.addWidget(self.button_step_minus)
        hbox.addWidget(self.editor_step_size)
        hbox.addWidget(self.step_unit)
        hbox.addWidget(self.button_step_plus)
        hbox.addWidget(self.button_reset_reading)
        hbox.addWidget(self.editor_reset_reading)
        hbox.addWidget(lb_empty)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        return hbox

class XEng_motor_layout(Motor_layout):
    def __init__(self, obj, motor_name, motor_label='', unit='um'):
        super().__init__(obj, motor_name, motor_label, unit)   
        self.label_eng_calib = self.lb_eng_calib()

    def lb_eng_calib(self):
        self.obj.lb_eng_calib = FixObj(QLabel, self.font2, '(calib. energy)', 320).run()
        return self.obj.lb_eng_calib

    def layout(self):
        lb_empty = QLabel()
        lb_empty.setFixedWidth(10)
        self.cbox_dcm_only = QCheckBox('Moving DCM only')
        self.cbox_dcm_only.setFixedWidth(160)
        self.cbox_dcm_only.setFont(self.font2)
        self.cbox_dcm_only.setChecked(False)
        self.cbox_dcm_only.setVisible(False)
        lb_motor = FixObj(QLabel, self.font1, self.motor_label + ':', 75).run()
        lb_unit = self.lb_unit()

        hbox = QHBoxLayout()
        hbox.addWidget(lb_motor)
        hbox.addWidget(self.label_motor_pos)
        hbox.addWidget(lb_unit[0])
        hbox.addWidget(self.editor_setpos)
        hbox.addWidget(lb_unit[1])
        hbox.addWidget(self.label_eng_calib)
        hbox.addWidget(self.cbox_dcm_only)
        hbox.addWidget(lb_empty)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        
        return hbox

    def fun_move_to_pos(self):
        flag, val = self.fun_check_pos_limit()
        if flag:
            try:
                self.editor_setpos.setDisabled(True)
                if self.cbox_dcm_only.isChecked():
                    print('move dcm only\n')
                    RE(mv(XEng, val))
                else:
                    RE(move_zp_ccd(val))
            except:
                msg = f'fails to move {self.motor_name}'
                print(msg)
            finally:
                self.editor_setpos.setEnabled(True)
                val_rb = self.mot.position
                self.label_motor_pos.setText(f'{val_rb:4.4f}')

class Filter_layout():
    def __init__(self, obj, filter_name, filter_label):
        # filter_name = 'filter1, 2, 3, 4'
        self.obj = obj
        self.motor_name = filter_name
        self.motor_label = filter_label
        self.font1 = QtGui.QFont('Arial', 12, QtGui.QFont.Bold)
        self.font2 = QtGui.QFont('Arial', 12, QtGui.QFont.Normal)
        self.mot = eval(self.motor_name)
        self.init_component()
        self.init_connect_function()
        #self.fun_update_status()

    def init_component(self):
        self.button_filter_in = self.pb_button_filter_in()
        self.button_filter_out = self.pb_button_filter_out()
        self.label_filter = self.lb_label_filter()
        
    def init_connect_function(self):
        self.obj.pb_filter_in.clicked.connect(lambda: self.fun_click_filter('In'))
         
    def lb_label_filter(self):
        self.obj.lb_filter = FixObj(QLabel, self.font2, self.motor_label, 120, 40).run()
        return self.obj.lb_filter

    def pb_button_filter_in(self):
        self.obj.pb_filter_in = FixObj(QPushButton, self.font2, 'In', 40, 40).run()
        return self.obj.pb_filter_in

    def pb_button_filter_out(self):
        self.obj.pb_filter_out = FixObj(QPushButton, self.font2, 'Out', 40, 40).run()
        self.obj.pb_filter_out.clicked.connect(lambda: self.fun_click_filter('Out'))
        return self.obj.pb_filter_out

    def fun_click_filter(self, op):
        pv = self.mot.describe()[self.motor_name]['source'][3:]
        if op == 'In': # inserted
            caput(pv, 1)
            #RE(mv(self.mot, 1))
        else:
            caput(pv, 0)
            #RE(mv(self.mot, 0))
        current_status = self.mot.value
        self.fun_update_status(current_status) # excluded from global sync 

    def fun_update_status(self, current_status):
        #current_status = self.mot.value
        if current_status == 1: # inserted
            self.button_filter_in.setStyleSheet('color: rgb(200, 50, 50);')
            self.button_filter_out.setStyleSheet('color: rgb(50, 50, 50);')
        else:
            self.button_filter_in.setStyleSheet('color: rgb(50, 50, 50);')
            self.button_filter_out.setStyleSheet('color: rgb(200, 50, 50);')
        
    def layout(self):
        lb_empty = QLabel()
        hbox = QHBoxLayout()
        hbox.addWidget(self.label_filter)
        hbox.addWidget(self.button_filter_in)
        hbox.addWidget(self.button_filter_out)
        hbox.addWidget(lb_empty)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addStretch()
        return hbox

class FixObj():
    def __init__(self, def_widget, font=None, name='', width=0, height=0):
        super().__init__()
        self.w = width
        self.h = height
        self.font = font
        self.name = name
        self.obj = def_widget()
        if self.w > 0:
            self.obj.setFixedWidth(self.w)
        if self.h > 0:
            self.obj.setFixedHeight(self.h)
        if not (self.font is None):
            self.obj.setFont(self.font)
        if hasattr(self.obj, 'setText'):
            self.obj.setText(self.name)
    def run(self):
        return self.obj

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

        self._err_color = QtCore.Qt.red
        stdout = OutputWrapper(self, True)
        stdout.outputWritten.connect(self.handleOutput)
        stderr = OutputWrapper(self, False)
        stderr.outputWritten.connect(self.handleOutput) 

        self.initUI()
        self.global_sync()
        #self.beam_shutter_sync()
        self.display_calib_eng_only()
        self.enable_reset_reading()

    def handleOutput(self, text, stdout):
        color = self.terminal.textColor()
        self.terminal.moveCursor(QtGui.QTextCursor.End)
        #self.terminal.setTextColor(color if stdout else self._err_color)       
        stylesheet = "background-color: rgb(40, 40, 40)"#rgb(48, 10, 36)"
        self.terminal.setStyleSheet(stylesheet)
        c = QColor(51, 255, 51)
        self.terminal.setTextColor(c if stdout else self._err_color)
        self.terminal.insertPlainText(text)

    def global_sync(self):
        self.threads = []
        for motor in self.motor_display:
            reading_thread = Get_motor_reading(motor)
            reading_thread.current_position.connect(motor.fun_update_status)
            reading_thread.start()
            self.threads.append(reading_thread)
         
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.font1 = QtGui.QFont('Arial', 12, QtGui.QFont.Bold)
        self.font2 = QtGui.QFont('Arial', 12, QtGui.QFont.Normal)
        self.font3 = QtGui.QFont('Arial', 14, QtGui.QFont.Normal)
        self.fpath = os.getcwd()
        self.pos = {}
        self.sample_pos = {}
        self.scan_name = ''
        self.pos_num = 0
        self.txm_eng_list = {}
        self.txm_scan = {}
        self.txm_record_scan = {}
        self.motor_display = []
        self.msg_external_file = ''
        self.temporary_py_file = ''
        self.temporary_py_scan_list = {}
        self.custom_variable_dict = {}
        self.fn_calib_eng_file = "/nsls2/data/fxi-new/legacy/log/calib_new.csv"
        self.fpath_bluesky_startup = '/nsls2/data/fxi-new/shared/config/bluesky/profile_collection/startup'
        self.timestamp_cache_for_calib_eng_file = os.stat(self.fn_calib_eng_file)
        grid = QGridLayout()
  
        grid.addWidget(self.layout_motor(), 0, 1)
        #grid.addWidget(self.layout_instruction(), 1, 1)
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
                     '" check scan" -> "Run"')
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
        lb_empty = FixObj(QLabel, None, '', 30).run()
        
        lb_empty1 = FixObj(QLabel, None, '', 30).run()
        
        lb_empty2 = FixObj(QLabel, None, '', 10).run()
        
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

    def vbox_motor_xyz(self):
        self.mot_sample_x = Sample_motor_layout(self, 'zps.sx', 'Pos. x', 'um')
        self.mot_sample_y = Sample_motor_layout(self, 'zps.sy', 'Pos. y', 'um')
        self.mot_sample_z = Sample_motor_layout(self, 'zps.sz', 'Pos. z', 'um')
        self.mot_sample_r = Sample_motor_layout(self, 'zps.pi_r', 'Rotation', 'deg')
        self.mot_sample_e = XEng_motor_layout(self, 'XEng', 'XEng', 'keV')
        vbox = QVBoxLayout()
        vbox.addLayout(self.mot_sample_x.layout())
        vbox.addLayout(self.mot_sample_y.layout())
        vbox.addLayout(self.mot_sample_z.layout())
        vbox.addLayout(self.mot_sample_r.layout())
        vbox.addLayout(self.mot_sample_e.layout())
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignLeft)

        self.motor_display.append(self.mot_sample_x)
        self.motor_display.append(self.mot_sample_y)
        self.motor_display.append(self.mot_sample_z)
        self.motor_display.append(self.mot_sample_r)
        self.motor_display.append(self.mot_sample_e)
        return vbox

    def vbox_motor_pos(self):
        lb_title = FixObj(QLabel, self.font1, 'TXM motors', 120).run()

        self.pb_pos_sync = FixObj(QPushButton, self.font2, 'Update energy calib.', 350).run()
        self.pb_pos_sync.clicked.connect(self.pos_sync)

        self.pb_reset_rot_speed = FixObj(QPushButton, self.font2, 'Reset rotation speed to 30 deg/s', 350).run()
        self.pb_reset_rot_speed.clicked.connect(self.reset_r_speed)

        hbox = QHBoxLayout()
        hbox.addWidget(self.pb_pos_sync)
        hbox.addWidget(self.pb_reset_rot_speed)
        hbox.addStretch()
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        
        vbox_motor_pos = QVBoxLayout()
        vbox_motor_pos.addWidget(lb_title)

        vbox_motor_pos.addLayout(self.vbox_motor_xyz())
        vbox_motor_pos.addLayout(hbox)
        vbox_motor_pos.setAlignment(QtCore.Qt.AlignTop)
        return vbox_motor_pos
 
    def vbox_pos_select_for_scan(self):
        lb_pos = FixObj(QLabel, self.font1, 'Position used in scan', 200).run()
        lb_pos.setStyleSheet('color: rgb(0, 80, 255)')

        self.lst_scan_pos = FixObj(QListWidget, self.font2, '', 100, 120).run()

        self.pb_pos_rm_select = FixObj(QPushButton, self.font2, 'Remove', 90).run()
        self.pb_pos_rm_select.clicked.connect(self.pos_remove_select)

        self.pb_pos_rm_all_select = FixObj(QPushButton, self.font2, 'Rmv. all', 90).run()
        self.pb_pos_rm_all_select.clicked.connect(self.pos_remove_all_select)

        lb_note1 = FixObj(QLabel, self.font2, '1. if empty, use current pos.', 230, 30).run()

        lb_note2 = FixObj(QLabel, self.font2, '2. Bkg. is automatically added', 230, 30).run()

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
        sep = FixObj(QLabel, None, '', 170, 2).run()
        sep.setStyleSheet('background-color: rgb(0, 80, 255);')

        lb_pos = FixObj(QLabel, self.font1,'Position saved', 160).run() 

        lb_pos_x = FixObj(QLabel, self.font2, 'x:', 20).run()

        self.lb_pos_x = FixObj(QLabel, self.font2, '', 95).run()

        lb_pos_y = FixObj(QLabel, self.font2, 'y:', 20).run()

        self.lb_pos_y = FixObj(QLabel, self.font2, '', 95).run()

        lb_pos_z = FixObj(QLabel, self.font2, 'z:', 20).run()

        self.lb_pos_z = FixObj(QLabel, self.font2, '', 95).run()

        lb_pos_r = FixObj(QLabel, self.font2, 'r:', 20).run()
        
        self.lb_pos_r = FixObj(QLabel, self.font2, '', 95).run()

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

        self.lst_pos = FixObj(QListWidget, self.font2, '', 100, 180).run()
        self.lst_pos.itemClicked.connect(self.show_pos_clicked)
        self.lst_pos.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_pos_rec = FixObj(QPushButton, self.font2, 'Record', 80).run()
        self.pb_pos_rec.clicked.connect(self.pos_record)

        self.pb_pos_out = FixObj(QPushButton, self.font2, 'Bkg. pos', 80).run()
        self.pb_pos_out.clicked.connect(self.pos_record_bkg)

        self.pb_pos_save = FixObj(QPushButton, self.font2, 'Save pos.', 80).run()
        self.pb_pos_save.clicked.connect(self.pos_save)

        self.pb_pos_load_last = FixObj(QPushButton, self.font2, 'Load pos.', 80).run()
        self.pb_pos_load_last.clicked.connect(self.pos_load_last)

        self.pb_pos_rm = FixObj(QPushButton, self.font2, 'Remove', 80).run()

        self.pb_pos_rm_all = FixObj(QPushButton, self.font2, 'Rmv. all', 80).run()
        self.pb_pos_rm_all.clicked.connect(self.pos_remove_all)

        self.pb_pos_update = FixObj(QPushButton, self.font2, 'Update', 80).run()
        self.pb_pos_update.clicked.connect(self.pos_update)

        self.pb_pos_go = FixObj(QPushButton, self.font2, 'Go To', 80).run()
        self.pb_pos_go.clicked.connect(self.pos_go_to)

        self.pb_pos_select = FixObj(QPushButton, self.font2, 'select\nfor scan\n--->', 70, 135).run()
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

        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.pb_pos_save)
        hbox4.addWidget(self.pb_pos_load_last)
        hbox4.setAlignment(QtCore.Qt.AlignLeft)

        vbox_rec_go = QVBoxLayout()
        vbox_rec_go.addLayout(hbox1)
        vbox_rec_go.addLayout(hbox2)
        vbox_rec_go.addLayout(hbox3)
        vbox_rec_go.addWidget(sep)
        vbox_rec_go.addLayout(hbox4)
        vbox_rec_go.setAlignment(QtCore.Qt.AlignTop)

        hbox_pos_comb = QHBoxLayout()
        hbox_pos_comb.addLayout(vbox_rec_go)
        hbox_pos_comb.addWidget(self.pb_pos_select)
        hbox_pos_comb.setAlignment(QtCore.Qt.AlignLeft)

        vbox_pos_comb = QVBoxLayout()
        vbox_pos_comb.addLayout(hbox_pos_comb)
        vbox_pos_comb.addLayout(hbox_pos1)
        vbox_pos_comb.addLayout(hbox_pos2)
        vbox_pos_comb.setAlignment(QtCore.Qt.AlignTop)

        hbox = QHBoxLayout()
        hbox.addWidget(self.lst_pos)
        hbox.addLayout(vbox_pos_comb)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        vbox_lst = QVBoxLayout()
        vbox_lst.addWidget(lb_pos)
        vbox_lst.addLayout(hbox)
        vbox_lst.addStretch()
        vbox_lst.setAlignment(QtCore.Qt.AlignTop)
        return vbox_lst

    def vbox_beam_shutter(self):
        self.shutter = Shutter(self)
        self.motor_display.append(self.shutter)
        vbox = self.shutter.layout()
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
        tab3 = QWidget()

        lay1 = QVBoxLayout()
        lay1.addLayout(self.layout_pre_defined_scan())
        tab1.setLayout(lay1)

        lay2 = QVBoxLayout()
        #lay2.addLayout(self.hbox_optics_1())
        lay2.addLayout(self.vbox_advanced())
        tab2.setLayout(lay2)

        lay3 = QVBoxLayout()
        lay3.addLayout(self.vbox_other_func())
        tab3.setLayout(lay3)

        tabs.addTab(tab1, 'Pre-defined scan')
        tabs.addTab(tab2, 'Advanced')
        tabs.addTab(tab3, 'Other Func.')
        vbox = QVBoxLayout()
        vbox.addWidget(tabs)
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignTop)
        gpbox.setLayout(vbox)
        gpbox.setAlignment(QtCore.Qt.AlignTop)
        return gpbox

    def layout_pre_defined_scan(self):
        lb_empty = FixObj(QLabel).run()

        lb_space1 = FixObj(QLabel, None, '', 20).run()

        lb_space2 = FixObj(QLabel, None, '', 10).run()

        lb_space3 = FixObj(QLabel, None, '', 10).run()

        lb_space4 = FixObj(QLabel, None, '', 10).run()

        lb_space5 = FixObj(QLabel, None, '', 10).run()

        lb_space6 = FixObj(QLabel, None, '', 10).run()

        lb_v_space1 = FixObj(QLabel, None, '', 10).run()

        sep = FixObj(QLabel, None, '', 10, 180).run()
        #sep.setStyleSheet('background-color: rgb(0, 80, 255);')
        sep.setStyleSheet('background-color: rgb(0, 80, 255);')

        scan_cmd = self.hbox_scan_cmd()
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


        self.terminal = FixObj(QTextBrowser, self.font3, '', 0, 200).run()

        vbox_scan = QVBoxLayout()
        vbox_scan.addLayout(hbox_scan)
        vbox_scan.addWidget(lb_v_space1)
        vbox_scan.addLayout(scan_arg)
        vbox_scan.addLayout(scan_cmd)

        vbox_scan.addWidget(self.terminal)

        vbox_scan.addWidget(lb_empty)
        # vbox_scan.addLayout(custom_script)
        vbox_scan.setAlignment(QtCore.Qt.AlignTop)
        vbox_scan.addStretch()

        return vbox_scan

    def hbox_scan_cmd(self):
        lb_sep = FixObj(QLabel, self.font2, '', 0, 30).run()
        hbox = QHBoxLayout()
        hbox.addLayout(self.vbox_run_scan())
        hbox.addWidget(lb_sep)
        #hbox.addLayout(self.vbox_ipython())
        hbox.addLayout(self.vbox_global_var())
        hbox.addStretch()
        return hbox

    def vbox_ipython(self):
        lb_ipython_msg1 = FixObj(QLabel, self.font1, 'To initiate environment, run command:', 320).run()
        lb_ipython_msg2 = FixObj(QLabel, self.font1, 'Before first scan here, update scan-id:', 320).run()
        tx_ipython_msg1 = FixObj(QLineEdit, self.font2, '%run -i /nsls2/data/fxi-new/shared/software/fxi_control/load_base.py', 570).run()
        tx_ipython_msg2 = FixObj(QLineEdit, self.font2, 'RE.md["scan_id"] = db[-1].start["scan_id"]', 570).run()

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
    
        self.ip_widget = make_jupyter_widget_with_kernel()        
        self.ip_widget.setFixedWidth(1600)
        self.ip_widget.setFixedHeight(360)
        self.ip_widget.set_default_style('linux')
        self.ip_widget.font = QtGui.QFont(self.ip_widget.font.family(), 12);
        
        vbox2 = QVBoxLayout()
        vbox2.addLayout(hbox_ipython1)
        vbox2.addLayout(hbox_ipython2)
        vbox2.addWidget(self.ip_widget)
        vbox2.addStretch()
        return vbox2

    def vbox_run_scan(self):
        self.lb_scan_msg = FixObj(QLabel, None, "Scan command / Message:", 500, 30).run()
        self.tx_scan_msg = FixObj(QPlainTextEdit, self.font3, '', 800, 200).run()

        tx_empty = QLineEdit()
        tx_empty.setVisible(False)
        tx_empty.setEnabled(False)

        hbox_commd_msg = QHBoxLayout()
        hbox_commd_msg.addWidget(self.lb_scan_msg)
        hbox_commd_msg.addWidget(tx_empty)
        hbox_commd_msg.setAlignment(QtCore.Qt.AlignLeft)
        hbox_commd_msg.addStretch()

        vbox1 = QVBoxLayout()
        #vbox1.addLayout(hbox_commd_msg)
        vbox1.addLayout(self.hbox_scan_id())
        vbox1.addWidget(self.tx_scan_msg)
        vbox1.addLayout(self.hbox_run_sid())
        vbox1.addStretch()

        return vbox1

    def hbox_run_sid(self):
        lb_empty = QLabel()
        lb_empty.setFixedHeight(10)

        self.pb_run_scan = FixObj(QPushButton, self.font1, 'Run', 120, 40).run()
        self.pb_run_scan.setStyleSheet('color: rgb(200, 50, 50);')
        self.pb_run_scan.clicked.connect(self.run_scan)

        self.pb_pause_scan = FixObj(QPushButton, self.font1, 'Pause', 80, 40).run()
        self.pb_pause_scan.setStyleSheet('color: rgb(200, 200, 200)')
        self.pb_pause_scan.setEnabled(False)        
        self.pb_pause_scan.clicked.connect(self.run_pause)

        self.pb_resume_scan = FixObj(QPushButton, self.font1, 'Resume', 80, 40).run()
        self.pb_resume_scan.setStyleSheet('color: rgb(200, 200, 200);')
        self.pb_resume_scan.setEnabled(False)
        self.pb_resume_scan.clicked.connect(self.run_resume)

        self.pb_stop_scan = FixObj(QPushButton, self.font1, 'Stop', 80, 40).run()
        self.pb_stop_scan.setStyleSheet('color: rgb(200, 200, 200);')
        self.pb_stop_scan.setEnabled(False)
        self.pb_stop_scan.clicked.connect(self.run_stop)

        self.pb_abort_scan = FixObj(QPushButton, self.font1, 'Abort', 80, 40).run()
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

        lb_sid = FixObj(QLabel, self.font1,'Latest scan ID:', 120).run()
        lb_sid.setAlignment(QtCore.Qt.AlignLeft)
        lb_sid.setAlignment(QtCore.Qt.AlignVCenter)

        self.lb_current_sid = FixObj(QLabel, self.font1, '', 80).run()
        self.lb_current_sid.setAlignment(QtCore.Qt.AlignLeft)
        self.lb_current_sid.setAlignment(QtCore.Qt.AlignVCenter)
        self.lb_current_sid.setStyleSheet('color: rgb(200, 50, 50);')

        self.tx_sid = FixObj(QLineEdit, self.font2, '', 120).run()
        self.tx_sid.setValidator(QIntValidator())

        self.pb_sid = FixObj(QPushButton, self.font2, 'Reset scan ID to:', 160).run()
        self.pb_sid.clicked.connect(self.reset_sid)

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
        lb_title = FixObj(QLabel, self.font1, 'Scan type').run()

        #n = len(scan_list)

        self.lst_scan = FixObj(QListWidget, self.font2, '', 200, 160).run()
        self.lst_scan.setSelectionMode(QAbstractItemView.SingleSelection)
        self.load_scan_type_list(1) # load commonly used scans

        self.lst_scan.itemClicked.connect(self.show_scan_example)
        self.lst_scan.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_scan_list1 = FixObj(QPushButton, self.font2, 'Common', 100).run()
        self.pb_scan_list1.clicked.connect(lambda: self.load_scan_type_list(1))

        self.pb_scan_list2 = FixObj(QPushButton, self.font2, 'Other scan', 100).run()
        self.pb_scan_list2.clicked.connect(lambda: self.load_scan_type_list(2))

        self.pb_scan_list3 = FixObj(QPushButton, self.font2, 'User scan', 100).run()
        self.pb_scan_list3.clicked.connect(lambda: self.load_scan_type_list(3))

        self.pb_scan_list4 = FixObj(QPushButton, self.font2, 'Extract .py file ...', 135).run()
        self.pb_scan_list4.clicked.connect(lambda: self.update_scan_type_list(4))

        self.pb_scan_list5 = FixObj(QPushButton, self.font2, 'Temporary loaded', 135).run()
        self.pb_scan_list5.clicked.connect(lambda: self.load_scan_type_list(5))

        self.pb_scan_list1_update = FixObj(QPushButton, self.font2, 'U', 30).run()
        self.pb_scan_list1_update.clicked.connect(lambda: self.update_scan_type_list(1))

        self.pb_scan_list2_update = FixObj(QPushButton, self.font2, 'U', 30).run()
        self.pb_scan_list2_update.clicked.connect(lambda: self.update_scan_type_list(2))

        self.pb_scan_list3_update = FixObj(QPushButton, self.font2, 'U', 30).run()
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
        vbox_load_scan.addWidget(self.pb_scan_list4)
        vbox_load_scan.addWidget(self.pb_scan_list5)
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
        lb_title = FixObj(QLabel, self.font1, 'Energy list', 120).run()
        self.lst_eng_list = FixObj(QListWidget, self.font2, '', 160, 160).run()
        self.lst_eng_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lst_eng_list.clicked.connect(self.select_eng_list)

        lb_name = FixObj(QLabel, self.font2, 'Name:', 80).run()

        self.tx_eng_name = FixObj(QLineEdit, self.font2, '', 80).run()

        self.pb_load_eng_list = FixObj(QPushButton, self.font2, 'load (.txt)', 80).run()
        self.pb_load_eng_list.clicked.connect(self.load_eng_list)

        self.pb_select_eng_list = FixObj(QPushButton, self.font2, 'select', 80).run()
        self.pb_select_eng_list.clicked.connect(self.select_eng_list)
        self.pb_select_eng_list.setDisabled(True)

        self.pb_plot_eng_list = FixObj(QPushButton, self.font2, 'plot', 80).run()
        self.pb_plot_eng_list.clicked.connect(self.plot_eng_list)

        self.pb_save_eng_list = FixObj(QPushButton, self.font2, 'save', 80).run()
        self.pb_save_eng_list.clicked.connect(self.save_eng_list)

        self.pb_rm_eng_list = FixObj(QPushButton, self.font2, 'delete', 80).run()
        self.pb_rm_eng_list.clicked.connect(self.remove_eng_list)

        self.pb_rmall_eng_list = FixObj(QPushButton, self.font2, 'del. all', 80).run()
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
        lb_title = FixObj(QLabel, self.font1, 'Recorded scan').run()

        self.lst_record_scan = FixObj(QListWidget, self.font2, '', 160, 160).run()   
        self.lst_record_scan.itemClicked.connect(self.show_recorded_scan)
        self.lst_record_scan.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_record = FixObj(QPushButton, self.font2, 'record', 80).run()
        self.pb_record.setDisabled(True)
        self.pb_record.clicked.connect(self.record_scan)

        self.pb_record_remove = FixObj(QPushButton, self.font2, 'delete', 80).run()
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
        lb_title = FixObj(QLabel, self.font1,'Operators').run()
        self.rd_op_repeat_s = FixObj(QRadioButton, self.font2, 'Repeat', 90).run()
        # self.rd_op_repeat_s.setStyleSheet('color: rgb(0, 80, 255);')

        self.rd_op_repeat_s.setChecked(True)

        self.rd_op_repeat_e = FixObj(QRadioButton, self.font2, 'End Repeat', 90).run()
        # self.rd_op_repeat_e.setStyleSheet('color: rgb(0, 80, 255);')

        self.rd_op_sleep = FixObj(QRadioButton, self.font2, 'sleep (s)', 90).run()
        # self.rd_op_sleep.setStyleSheet('color: rgb(0, 80, 255);')

        self.rd_op_select_scan = FixObj(QRadioButton, self.font2, 'select scan', 110).run()
        # self.rd_op_select_scan.setStyleSheet('color: rgb(0, 80, 255);')

        self.operator_group = QButtonGroup()
        self.operator_group.setExclusive(True)
        self.operator_group.addButton(self.rd_op_repeat_s)
        self.operator_group.addButton(self.rd_op_repeat_e)
        self.operator_group.addButton(self.rd_op_sleep)
        self.operator_group.addButton(self.rd_op_select_scan)

        self.tx_op_repeat = FixObj(QLineEdit, self.font2, '1', 60).run()
        # self.tx_op_repeat.setStyleSheet('color: rgb(0, 80, 255);')
        self.tx_op_repeat.setValidator(QIntValidator())

        self.tx_op_sleep = FixObj(QLineEdit, self.font2, '', 60).run()
        self.tx_op_sleep.setValidator(QDoubleValidator())

        self.pb_op_insert = FixObj(QPushButton, self.font2, 'Insert', 140).run()
        # self.pb_op_insert.setStyleSheet('color: rgb(0, 80, 255);')
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
        lb_title = FixObj(QLabel, self.font1, 'Assembled scan').run()
        # lb_title.setStyleSheet('color: rgb(0, 80, 255);')

        self.lst_assembled_scan = FixObj(QListWidget, self.font2, '', 160, 160).run()
        self.lst_assembled_scan.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pb_assembled_scan_remove = FixObj(QPushButton, self.font2, 'delete', 80).run()
        self.pb_assembled_scan_remove.clicked.connect(self.remove_assemble_scan)

        self.pb_assembled_scan_remove_all = FixObj(QPushButton, self.font2, 'del. all', 80).run()
        self.pb_assembled_scan_remove_all.clicked.connect(self.remove_all_assemble_scan)

        self.pb_assembled_scan_up = FixObj(QPushButton, self.font2, 'mv up', 80).run()
        self.pb_assembled_scan_up.clicked.connect(self.assemble_scan_mv_up)

        self.pb_assembled_scan_down = FixObj(QPushButton, self.font2, 'mv down', 80).run()
        self.pb_assembled_scan_down.clicked.connect(self.assemble_scan_mv_down)

        self.pb_assembled = FixObj(QPushButton, self.font2, 'assemble', 165).run()
        self.pb_assembled.clicked.connect(self.assemble_scan_assemble)

        lb_name = FixObj(QLabel, self.font2, 'fun. name', 80).run()

        self.tx_fun_name = FixObj(QLineEdit, self.font2, '', 80).run()

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
        lb_empty = FixObj(QLabel, self.font2, '', 30).run()
        hbox = {}
        vbox = QVBoxLayout()
        for i in range(20):
            self.scan_lb[f'lb_{i}'] = FixObj(QLabel, self.font2, f'param {i}:', 160).run()
            self.scan_lb[f'lb_{i}'].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.scan_lb[f'lb_{i}'].setVisible(False)
            
            self.scan_tx[f'tx_{i}'] = FixObj(QLineEdit, self.font2, '', 120).run()
            self.scan_tx[f'tx_{i}'].setVisible(False)

        self.scan_lb['note'] = FixObj(QLabel, self.font1, 'Sample infor:', 160).run()
        self.scan_lb['note'].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.scan_lb['note'].setVisible(True)
        
        self.scan_tx['note'] = FixObj(QLineEdit, self.font2, '', 290).run()
        self.scan_tx['note'].setVisible(True)

        self.scan_lb['XEng'] = FixObj(QLabel, self.font1, 'X-ray Energy:', 120).run()
        self.scan_lb['XEng'].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        self.scan_tx['XEng'] = FixObj(QLineEdit, self.font2, '', 120).run()
        self.scan_tx['XEng'].setValidator(QDoubleValidator())

        self.pb_read_current_eng = FixObj(QPushButton, self.font2, 'use curr. XEng', 120).run()
        self.pb_read_current_eng.clicked.connect(self.use_current_eng)

        lb_pix = FixObj(QLabel, self.font1, 'Pixel size:', 80).run()
        self.lb_pixel_size = FixObj(QLabel, self.font2, '', 120).run()

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
        hbox['note'].addWidget(lb_empty)
        hbox['note'].addWidget(lb_pix)
        hbox['note'].addWidget(self.lb_pixel_size)
        
        hbox['note'].setAlignment(QtCore.Qt.AlignLeft)

        lb_empty = QLabel()
        lb_pos = FixObj(QLabel, self.font1, 'Sample / Bkg. Pos.:', 160).run()
        lb_pos.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.lb_sampel_pos_msg = FixObj(QLabel, self.font2, '  If empty, use current position').run()

        self.tx_pos = FixObj(QLineEdit, self.font2, '', 290).run()

        self.pb_choose_pos = FixObj(QPushButton, self.font2, 'add from list', 120).run()
        self.pb_choose_pos.clicked.connect(self.add_sample_pos)

        self.pb_clear_pos = FixObj(QPushButton, self.font2, 'clear positions',120).run()
        self.pb_clear_pos.clicked.connect(self.clear_scan_pos)

        self.pb_assemble_scan = FixObj(QPushButton, self.font1, 'check scan', 120).run()
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
            
            #self.display_calib_eng_only()
            msg += '\nupdate energy calibration finished.\n'
        except:
            msg += 'fails to connect database to retrieve scan_ID\n'
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
        msg += 'motor synchronization finshed.'    
        self.tx_scan_msg.setPlainText(msg)

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
        x = float(self.mot_sample_x.label_motor_pos.text())
        y = float(self.mot_sample_y.label_motor_pos.text())
        z = float(self.mot_sample_z.label_motor_pos.text())
        r = float(self.mot_sample_r.label_motor_pos.text())

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
            x = float(self.mot_sample_x.label_motor_pos.text())
            y = float(self.mot_sample_y.label_motor_pos.text())
            z = float(self.mot_sample_z.label_motor_pos.text())
            r = float(self.mot_sample_r.label_motor_pos.text())

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

            self.mot_sample_x.editor_setpos.setText(f'{x:4.3f}')
            self.mot_sample_y.editor_setpos.setText(f'{y:4.3f}')
            self.mot_sample_z.editor_setpos.setText(f'{z:4.3f}')
            self.mot_sample_r.editor_setpos.setText(f'{r:4.3f}')

            self.mot_sample_x.fun_move_to_pos()
            self.mot_sample_y.fun_move_to_pos()
            self.mot_sample_z.fun_move_to_pos()
            self.mot_sample_r.fun_move_to_pos()

    def pos_record_bkg(self):
        x = float(self.mot_sample_x.label_motor_pos.text())
        y = float(self.mot_sample_y.label_motor_pos.text())
        z = float(self.mot_sample_z.label_motor_pos.text())
        r = float(self.mot_sample_r.label_motor_pos.text())

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

    def pos_save(self):
        n = len(self.pos)
        keys = self.pos.keys()
        with open('/tmp/sample_pos.json', 'w') as f:
            json.dump(self.pos, f)
        print('Position has been saved to /tmp/sample_pos.json\n')

    def pos_load_last(self):
        self.pos = {}
        self.lst_pos.clear()
        self.lst_scan_pos.clear()
        with open('/tmp/sample_pos.json', 'r') as f:
            self.pos = json.load(f)
        print('Load sample position from /tmp/sample_pos.json\n')
        for k in self.pos.keys():
            self.lst_pos.addItem(k)
        self.lst_pos.sortItems()

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
        #print(scan_name[4:])
        self.tx_scan_msg.setPlainText(intro)

    def show_scan_example(self):
        item = self.lst_scan.selectedItems()
        self.scan_name = 'txm_' + item[0].text().replace(' ', '_')
        txm_scan = scan_list[self.scan_name]
        self.show_scan_example_sub(txm_scan)
        self.add_bkg_pos()
        self.select_eng_list()

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

    def check_scan(self, use_exist_pos=False):
        self.txm_scan = {}
        flag_multi_pos_scan = 0
        if not use_exist_pos:
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
                cmd_move_pos[key] = f'RE(mv(zps.sx, {x}, zps.sy, {y}, zps.sz, {z}, zps.pi_r, {r}))  #{key}\n'
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
        x = float(self.mot_sample_x.label_motor_pos.text())
        y = float(self.mot_sample_y.label_motor_pos.text())
        z = float(self.mot_sample_z.label_motor_pos.text())
        r = float(self.mot_sample_r.label_motor_pos.text())
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
        global txm
        options = QFileDialog.Option()
        file_type = 'txt files (*.txt)'
        fn, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", file_type, options=options)
        if fn:
            try:
                eng_list = np.array(np.loadtxt(fn))
            except:
                #eng_list = [eval(self.lb_motor_pos_e.text())]
                eng_list = [eval(self.mot_sample_e.label_motor_pos.text())]
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
        eng = self.mot_sample_e.label_motor_pos.text()
        #eng = self.lb_motor_pos_e.text()
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
                msg = '\n\nscan finished\n\n'
                print(msg)
                #self.tx_scan_msg.setPlainText(msg)
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
            try:
                sid = db[-1].start['scan_id']
                self.lb_current_sid.setText(str(sid))
            except Exception as err:
                msg += str(err) + '\n'
                print(msg)
            self.tx_scan_msg.setPlainText(msg)
            
            txt = self.terminal.toPlainText()
            lines = txt.split('\n')
            idx = 1
            for l in lines[::-1]:
                if 'generator' in l:
                    break
                idx += 1
            txt_short = ''
            for l in lines[-idx:]:
                txt_short += l+'\n'
            self.terminal.clear()
            self.terminal.insertPlainText(txt_short)
            self.terminal.moveCursor(QtGui.QTextCursor.End)
            with open('/tmp/scan_output.txt', 'w') as f:
                f.write(txt)

    def load_scan_type_list(self, scan_type=1, fpath_scan_list=''):
        global scan_list
        msg = ''
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
            
            if scan_type == 4:
                get_ipython().run_line_magic("run", f"-i {fpath_scan_list}")
                source = open(fpath_scan_list).read()
                fun_name = [f.name for f in ast.parse(source).body if isinstance(f, ast.FunctionDef)]
                tmp_scan_list = eval(fun_name[0] + '()')   
                msg = f'load custom scan in: {fpath_scan_list}'
                self.temporary_py_file = fpath_scan_list
                self.temporary_py_scan_list = tmp_scan_list
            if scan_type == 5:
                if len(self.temporary_py_file):
                    tmp_scan_list = self.temporary_py_scan_list
            scan_list = merge_dict(scan_list, tmp_scan_list)            
            self.lst_scan.clear()
            #QApplication.processEvents() 
            for k in tmp_scan_list.keys():
                name = ' '.join(t for t in k.split('_')[1:])
                self.lst_scan.addItem(name)
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

        if scan_type == 4: # open custom python files
            options = QFileDialog.Option()
            options |= QFileDialog.DontUseNativeDialog
            file_type = 'python files (*.py)'
            fn, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", file_type, options=options)
            if fn:
                fname_read = fn
                get_ipython().run_line_magic("run", f"-i {fname_read}")
                fname_write = 'custom_converted_scan_list.py'
                prepare_scan_list(fname_read, fname_write) 
                self.load_scan_type_list(4, fname_write)
      
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
        self.check_scan(use_exist_pos=True)

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
                    cmd += ' ' * (n_repeat * 4 + 8) + f'print(f"repeat #{t1}{rep_symbol[rep_id]}{t2}")\n\n'
                    n_repeat += 1
                    rep_id += 1
                elif 'End repeat' in item:
                    n_repeat -= 1
                    rep_id -= 1
                elif 'sleep' in item:
                    sleep_time = float(item[:-1].split('_')[-1])
                    #cmd += f'sleep for {sleep_time} sec ...\n'
                    cmd += ' ' * (n_repeat * 4 + 4) + f'print("sleep for {sleep_time} sec ...")\n\n'
                    cmd += ' ' * (n_repeat * 4 + 4) + f'yield from bps.sleep({sleep_time})\n\n'
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
        #cmd = 'RE.md["scan_id"] = db[-1].start["scan_id"]\n'
        cmd = ''
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
                            n_repeat * 4 + 4) + f'yield from mv(zps.sx, {x}, zps.sy, {y}, zps.sz, {z}, zps.pi_r, {r})  #{key}\n'

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

    def vbox_advanced(self):
        lb_empty = QLabel()
        lb_empty1 = QLabel()
        lb_empty2 = QLabel()
        lb_empty2.setFixedWidth(30)
        lb_empty3 = QLabel()
        lb_empty3.setFixedWidth(30)
        lb_empty4 = QLabel()
        lb_empty4.setFixedHeight(10)

        #hbox_optics = self.hbox_optics_1()
        hbox_record = self.layout_record_eng_calib()

        hbox = QHBoxLayout()
        hbox.addLayout(hbox_record)
        hbox.addWidget(lb_empty1)
        #hbox.addLayout(hbox_optics) 
        hbox.addWidget(lb_empty2)        
        hbox.addLayout(self.vbox_zp_ccd())  
        hbox.addWidget(lb_empty3)            
        hbox.addLayout(self.vbox_filter()) 
        hbox.addStretch()
        hbox.setAlignment(QtCore.Qt.AlignTop)
        
        self.chk_reset_reading = QCheckBox('Enable reading reset without moving motor (ADVANCED USER ONLY)')
        self.chk_reset_reading.stateChanged.connect(self.enable_reset_reading)
        self.chk_reset_reading.setChecked(False) 

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(lb_empty)
        vbox.addWidget(self.chk_reset_reading)
        vbox.addLayout(self.hbox_optics_adv())
        vbox.addWidget(lb_empty4)
        vbox.addStretch()

        return vbox

    def hbox_optics_adv(self):
        lb_empty = QLabel()
        lb_empty1 = QLabel()
        lb_empty1.setFixedWidth(30)
        hbox = QHBoxLayout()
        hbox.addLayout(self.vbox_optics_left())
        hbox.addWidget(lb_empty)
        hbox.addLayout(self.vbox_optics_right())
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addStretch()
        return hbox

    def vbox_optics_left(self):
        lb_sep1 = QLabel()
        lb_sep1.setFixedHeight(10)
        lb_sep1.setFixedWidth(100)

        lb_sep2 = QLabel()
        lb_sep2.setFixedHeight(10)
        lb_sep2.setFixedWidth(100)

        lb_sep3 = QLabel()
        lb_sep3.setFixedHeight(10)
        lb_sep3.setFixedWidth(100)

        vbox = QVBoxLayout()
        vbox.addLayout(self.vbox_motor_cond())
        vbox.addWidget(lb_sep1)
        vbox.addLayout(self.vbox_motor_aper())
        vbox.addWidget(lb_sep2)
        vbox.addLayout(self.vbox_motor_zp())
        vbox.addStretch()

        return vbox

    def vbox_optics_right(self):
        lb_empty = QLabel()
        lb_sep1 = QLabel()
        lb_sep1.setFixedHeight(10)
        lb_sep1.setFixedWidth(100)

        lb_sep2 = QLabel()
        lb_sep2.setFixedHeight(10)
        lb_sep2.setFixedWidth(100)

        lb_sep3 = QLabel()
        lb_sep3.setFixedHeight(10)
        lb_sep3.setFixedWidth(100)
        
        self.mot_txmX = Motor_layout(self, 'zps.pi_x', 'TXM X', 'mm')     
        self.motor_display.append(self.mot_txmX)
        
        vbox = QVBoxLayout()
        vbox.addLayout(self.mot_txmX.layout())
        vbox.addWidget(lb_sep1)

        vbox.addLayout(self.vbox_motor_detU())
        vbox.addWidget(lb_sep2)

        vbox.addLayout(self.vbox_motor_dcm_th2())
        vbox.addWidget(lb_sep3)
        vbox.addLayout(self.vbox_motor_dcm_chi2())
        vbox.addWidget(lb_empty)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()

        return vbox

    def vbox_zp_ccd(self):
        lb_empty = QLabel()
        lb_empty2 = QLabel()
        lb_empty2.setFixedHeight(10)
        lb_title = FixObj(QLabel, self.font1, 'Optical Parameter Calculation', 300).run()
        hbox = QHBoxLayout()
        hbox.addLayout(self.vbox_zone_plate_cal_1())
        hbox.addWidget(self.vbox_zone_plate_cal_2())
        hbox.addLayout(self.vbox_zone_plate_cal_3())
        hbox.addWidget(lb_empty)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addStretch()
        vbox = QVBoxLayout()
        vbox.addWidget(lb_title)
        vbox.addWidget(lb_empty2)
        vbox.addLayout(hbox)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        return vbox

    def vbox_zone_plate_cal_1(self):
        lb_zp_diameter = FixObj(QLabel, self.font2, 'ZP diameter:', 120).run()
        lb_zp_diameter_unit = FixObj(QLabel, self.font2, 'um', 40).run()
        self.tx_zp_diamter = FixObj(QLineEdit, self.font2, '244', 60 ).run()

        lb_zp_width = FixObj(QLabel, self.font2, 'Outer width:', 120).run()
        lb_zp_width_unit = FixObj(QLabel, self.font2, 'nm', 40).run()
        self.tx_zp_width = FixObj(QLineEdit, self.font2, '30', 60).run()

        lb_txm_mag = FixObj(QLabel, self.font2, 'ZP Mag:', 120).run()
        lb_txm_mag_unit = FixObj(QLabel, self.font2, 'x', 40).run()
        self.tx_txm_mag = FixObj(QLineEdit, self.font2, '32.5', 60).run()

        lb_vlm_mag = FixObj(QLabel, self.font2, 'Vis Lens Mag:', 120).run()
        lb_vlm_mag_unit = FixObj(QLabel, self.font2, 'x', 40).run()
        self.tx_vlm_mag = FixObj(QLineEdit, self.font2, '10', 60).run()

        lb_xray_eng = FixObj(QLabel, self.font2, 'X-ray energy:', 120).run()
        lb_xray_eng_unit = FixObj(QLabel, self.font2, 'keV', 40).run()
        self.tx_xray_eng = FixObj(QLineEdit, self.font2, '8.0', 60).run()
        
        self.pb_zp_cal = FixObj(QPushButton, self.font2, 'Calculate', 230).run()
        self.pb_zp_cal.clicked.connect(self.cal_zone_plate_param)
        
        hbox_dia = QHBoxLayout()
        hbox_dia.addWidget(lb_zp_diameter)
        hbox_dia.addWidget(self.tx_zp_diamter)
        hbox_dia.addWidget(lb_zp_diameter_unit)
        hbox_dia.setAlignment(QtCore.Qt.AlignLeft)

        hbox_w = QHBoxLayout()
        hbox_w.addWidget(lb_zp_width)
        hbox_w.addWidget(self.tx_zp_width)
        hbox_w.addWidget(lb_zp_width_unit)
        hbox_w.setAlignment(QtCore.Qt.AlignLeft)

        hbox_mag = QHBoxLayout()
        hbox_mag.addWidget(lb_txm_mag)
        hbox_mag.addWidget(self.tx_txm_mag)
        hbox_mag.addWidget(lb_txm_mag_unit)
        hbox_mag.setAlignment(QtCore.Qt.AlignLeft)
        
        hbox_vlm_mag = QHBoxLayout()
        hbox_vlm_mag.addWidget(lb_vlm_mag)
        hbox_vlm_mag.addWidget(self.tx_vlm_mag)
        hbox_vlm_mag.addWidget(lb_vlm_mag_unit)
        hbox_vlm_mag.setAlignment(QtCore.Qt.AlignLeft)

        hbox_eng = QHBoxLayout()
        hbox_eng.addWidget(lb_xray_eng)
        hbox_eng.addWidget(self.tx_xray_eng)
        hbox_eng.addWidget(lb_xray_eng_unit)
        hbox_eng.setAlignment(QtCore.Qt.AlignLeft)

        vbox_zp = QVBoxLayout()
        vbox_zp.addLayout(hbox_dia)
        vbox_zp.addLayout(hbox_w)
        vbox_zp.addLayout(hbox_mag)
        vbox_zp.addLayout(hbox_vlm_mag)
        vbox_zp.addLayout(hbox_eng)
        vbox_zp.addWidget(self.pb_zp_cal)
        vbox_zp.setAlignment(QtCore.Qt.AlignTop)

        return vbox_zp

    def vbox_zone_plate_cal_2(self):
        lb_zp_cal = FixObj(QLabel, self.font2, '--->', 60).run()
        lb_zp_cal.setAlignment(QtCore.Qt.AlignCenter)
        return lb_zp_cal

    def vbox_zone_plate_cal_3(self):
        lb_zp_wl = FixObj(QLabel, self.font2, 'Wavelength:', 120).run()
        lb_zp_wl_unit = FixObj(QLabel, self.font2, 'nm', 40).run()
        self.tx_zp_wl = FixObj(QLineEdit, self.font2, '', 80 ).run()

        lb_zp_fl = FixObj(QLabel, self.font2, 'Focal length:', 120).run()
        lb_zp_fl_unit = FixObj(QLabel, self.font2, 'mm', 40).run()
        self.tx_zp_fl = FixObj(QLineEdit, self.font2, '', 80).run()

        lb_zp_na = FixObj(QLabel, self.font2, 'NA:', 120).run()
        lb_zp_na_unit = FixObj(QLabel, self.font2, 'mrad', 40).run()
        self.tx_zp_na = FixObj(QLineEdit, self.font2, '', 80).run()

        lb_zp_dof= FixObj(QLabel, self.font2, 'DOF:', 120).run()
        lb_zp_dof_unit = FixObj(QLabel, self.font2, 'um', 40).run()
        self.tx_zp_dof = FixObj(QLineEdit, self.font2, '', 80).run()

        lb_zp_dis = FixObj(QLabel, self.font2, 'ZP position:', 120).run()
        stylesheet = 'color: rgb(0, 80, 255)'
        lb_zp_dis.setStyleSheet(stylesheet)
        lb_zp_dis_unit = FixObj(QLabel, self.font2, 'mm', 40).run()
        self.tx_zp_dis = FixObj(QLineEdit, self.font2, '', 80).run()

        lb_zp_ccd = FixObj(QLabel, self.font2, 'CCD posistion:', 120).run()
        stylesheet = 'color: rgb(0, 80, 255)'
        lb_zp_ccd.setStyleSheet(stylesheet)
        lb_zp_ccd_unit = FixObj(QLabel, self.font2, 'mm', 40).run()
        self.tx_zp_ccd = FixObj(QLineEdit, self.font2, '', 80).run()

        lb_pix = FixObj(QLabel, self.font1, 'Pix size:', 120).run()
        lb_pix_unit = FixObj(QLabel, self.font2, 'mm', 40).run()
        self.tx_pix = FixObj(QLineEdit, self.font2, '', 80).run()

        hbox_wl = QHBoxLayout()
        hbox_wl.addWidget(lb_zp_wl)
        hbox_wl.addWidget(self.tx_zp_wl)
        hbox_wl.addWidget(lb_zp_wl_unit)
        hbox_wl.setAlignment(QtCore.Qt.AlignLeft)

        hbox_fl = QHBoxLayout()
        hbox_fl.addWidget(lb_zp_fl)
        hbox_fl.addWidget(self.tx_zp_fl)
        hbox_fl.addWidget(lb_zp_fl_unit)
        hbox_fl.setAlignment(QtCore.Qt.AlignLeft)

        hbox_na = QHBoxLayout()
        hbox_na.addWidget(lb_zp_na)
        hbox_na.addWidget(self.tx_zp_na)
        hbox_na.addWidget(lb_zp_na_unit)
        hbox_na.setAlignment(QtCore.Qt.AlignLeft)

        hbox_dof = QHBoxLayout()
        hbox_dof.addWidget(lb_zp_dof)
        hbox_dof.addWidget(self.tx_zp_dof)
        hbox_dof.addWidget(lb_zp_dof_unit)
        hbox_dof.setAlignment(QtCore.Qt.AlignLeft)
        
        hbox_zp_dis = QHBoxLayout()
        hbox_zp_dis.addWidget(lb_zp_dis)
        hbox_zp_dis.addWidget(self.tx_zp_dis)
        hbox_zp_dis.addWidget(lb_zp_dis_unit)
        hbox_zp_dis.setAlignment(QtCore.Qt.AlignLeft)

        hbox_ccd_dis = QHBoxLayout()
        hbox_ccd_dis.addWidget(lb_zp_ccd)
        hbox_ccd_dis.addWidget(self.tx_zp_ccd)
        hbox_ccd_dis.addWidget(lb_zp_ccd_unit)
        hbox_ccd_dis.setAlignment(QtCore.Qt.AlignLeft)

        vbox_zp = QVBoxLayout()
        vbox_zp.addLayout(hbox_wl)
        vbox_zp.addLayout(hbox_fl)
        vbox_zp.addLayout(hbox_na)
        vbox_zp.addLayout(hbox_dof)
        vbox_zp.addLayout(hbox_zp_dis)
        vbox_zp.addLayout(hbox_ccd_dis)
        vbox_zp.setAlignment(QtCore.Qt.AlignTop)

        return vbox_zp
    
    def vbox_filter(self):
        lb_empty = QLabel()
        lb_title = FixObj(QLabel, self.font1, 'SSA Filters').run()

        lb_sep = QLabel()
        lb_sep.setFixedHeight(10)
        self.filt1 = Filter_layout(self, 'filter1', 'Filter 1 (1-Al)')
        self.filt2 = Filter_layout(self, 'filter2', 'Filter 2 (2-Al)')
        self.filt3 = Filter_layout(self, 'filter3', 'Filter 3 (3-Al)')
        self.filt4 = Filter_layout(self, 'filter4', 'Filter 4 (1-Cu)')
        
        self.motor_display.append(self.filt1)
        self.motor_display.append(self.filt2)
        self.motor_display.append(self.filt3)
        self.motor_display.append(self.filt4)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_title)
        vbox.addWidget(lb_sep)
        vbox.addLayout(self.filt1.layout())
        vbox.addLayout(self.filt2.layout())
        vbox.addLayout(self.filt3.layout())
        vbox.addLayout(self.filt4.layout())
        vbox.addWidget(lb_empty)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()

        return vbox

    def layout_record_eng_calib(self):
        lb_empty = QLabel()
        lb_empty.setFixedHeight(10)

        lb_empty2 = QLabel()
        lb_empty2.setFixedWidth(5)

        lb_empty3 = QLabel()
        lb_empty3.setFixedWidth(5)
        
        lb_empty4 = QLabel()
        lb_empty4.setFixedWidth(5)

        lb_sep1 = FixObj(QLabel, self.font2, '', 0, 10).run()
        lb_sep2 = FixObj(QLabel, self.font2, '', 0, 10).run()
        lb_sep3 = FixObj(QLabel, self.font2, '', 0, 10).run()

        lb_rec_eng_calib = FixObj(QLabel, self.font1, 'Record energy calibration position').run()

        self.pb_rec_eng_calib = FixObj(QPushButton, self.font2, 'record', 100).run()
        self.pb_rec_eng_calib.clicked.connect(self.record_eng_calib)

        self.pb_rm_eng_calib = FixObj(QPushButton, self.font2, 'remove', 100).run()
        self.pb_rm_eng_calib.clicked.connect(self.remove_eng_calib)

        self.pb_rm_all_eng_calib = FixObj(QPushButton, self.font2, 'remove all', 100).run()
        self.pb_rm_all_eng_calib.clicked.connect(self.remove_eng_calib_all)

        lb_rec_eng_id = FixObj(QLabel, self.font2, 'Pos ID:', 60).run()

        self.tx_rec_eng_id = FixObj(QLineEdit, self.font2, '1', 30).run()

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

        lb_rec_eng_recorded = FixObj(QLabel, self.font2, 'Recorded', 140).run()

        self.lst_eng_calib = FixObj(QListWidget, self.font2, '', 140, 160).run()
        self.lst_eng_calib.itemClicked.connect(self.display_calib_eng_detail)

        vbox_recorded = QVBoxLayout()
        vbox_recorded.addWidget(lb_rec_eng_recorded)
        vbox_recorded.addWidget(self.lst_eng_calib)
        vbox_recorded.setAlignment(QtCore.Qt.AlignTop)

        lb_rec_eng_detail = FixObj(QLabel, self.font2, 'Motor pos', 160).run()

        self.tx_eng_calib = FixObj(QPlainTextEdit, self.font2, '', 180, 160).run()
        self.tx_eng_calib.setReadOnly(True)

        vbox_record_detail = QVBoxLayout()
        vbox_record_detail.addWidget(lb_rec_eng_detail)
        vbox_record_detail.addWidget(self.tx_eng_calib)
        vbox_record_detail.setAlignment(QtCore.Qt.AlignTop)

        '''
        lb_zp_mag = FixObj(QLabel, self.font2, 'ZP Mag:', 80).run()
        self.lb_zp_mag = FixObj(QLabel, self.font2, '', 80).run()
        
        lb_current_mag = FixObj(QLabel, self.font2, 'TXM Mag:', 80).run()
        self.lb_current_mag = FixObj(QLabel, self.font2, '', 80).run()

        lb_pix_size = FixObj(QLabel, self.font2, 'Pixel:', 80).run()
        self.lb_pix_size = FixObj(QLabel, self.font2, '', 80).run()
        
        hbox_zp_mag = QHBoxLayout()
        hbox_zp_mag.addWidget(lb_zp_mag)
        hbox_zp_mag.addWidget(self.lb_zp_mag)
        hbox_zp_mag.setAlignment(QtCore.Qt.AlignTop)

        hbox_txm_mag = QHBoxLayout()
        hbox_txm_mag.addWidget(lb_current_mag)
        hbox_txm_mag.addWidget(self.lb_current_mag)
        hbox_txm_mag.setAlignment(QtCore.Qt.AlignTop)
        
        hbox_txm_pix = QHBoxLayout()
        hbox_txm_pix.addWidget(lb_pix_size)
        hbox_txm_pix.addWidget(self.lb_pix_size)
        hbox_txm_pix.setAlignment(QtCore.Qt.AlignTop)
        
        vbox_pix_mag = QVBoxLayout()
        vbox_pix_mag.addLayout(hbox_zp_mag)
        vbox_pix_mag.addWidget(lb_sep1)
        vbox_pix_mag.addLayout(hbox_txm_mag)
        vbox_pix_mag.addWidget(lb_sep1)
        vbox_pix_mag.addLayout(hbox_txm_pix)
        vbox_pix_mag.setAlignment(QtCore.Qt.AlignCenter)
        '''
        self.txm_zp_pix = TXM_ZP_mag(self)
        self.motor_display.append(self.txm_zp_pix)
        vbox_pix_mag = self.txm_zp_pix.layout()

        hbox2 = QHBoxLayout()
        hbox2.addLayout(vbox_pb)
        hbox2.addWidget(lb_empty2)
        hbox2.addLayout(vbox_recorded)
        hbox2.addWidget(lb_empty3)
        hbox2.addLayout(vbox_record_detail)
        hbox2.addWidget(lb_empty4)
        hbox2.addLayout(vbox_pix_mag)
        hbox2.addStretch()
        hbox2.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_rec_eng_calib)
        vbox.addWidget(lb_empty)
        vbox.addLayout(hbox2)
        #vbox.addWidget(lb_empty2)
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignTop)

        return vbox

    def vbox_motor_cond(self):
        self.mot_cond_x = Motor_layout(self, 'clens.x', 'Cond.x', 'um')
        self.mot_cond_y1 = Motor_layout(self, 'clens.y1', 'Cond.y1', 'um')
        self.mot_cond_y2 = Motor_layout(self, 'clens.y2', 'Cond.y2', 'um')
        self.mot_cond_z1 = Motor_layout(self, 'clens.z1', 'Cond.z1', 'um')
        self.mot_cond_z2 = Motor_layout(self, 'clens.z2', 'Cond.z2', 'um')
        self.mot_cond_pit = Motor_layout(self, 'clens.p', 'Cond.pit', 'um')

        vbox = QVBoxLayout()
        vbox.addLayout(self.mot_cond_x.layout())
        vbox.addLayout(self.mot_cond_y1.layout())
        vbox.addLayout(self.mot_cond_y2.layout())
        vbox.addLayout(self.mot_cond_z1.layout())
        vbox.addLayout(self.mot_cond_z2.layout())
        vbox.addLayout(self.mot_cond_pit.layout())
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignLeft)

        self.motor_display.append(self.mot_cond_x)
        self.motor_display.append(self.mot_cond_y1)
        self.motor_display.append(self.mot_cond_y2)
        self.motor_display.append(self.mot_cond_z1)
        self.motor_display.append(self.mot_cond_z2)
        self.motor_display.append(self.mot_cond_pit)

        return vbox
  
    def vbox_motor_aper(self):                
        self.mot_aper_x = Motor_layout(self, 'aper.x', 'Aper.x', 'um')
        self.mot_aper_y = Motor_layout(self, 'aper.y', 'Aper.y', 'um')
        self.mot_aper_z = Motor_layout(self, 'aper.z', 'Aper.z', 'mm')
        vbox = QVBoxLayout()
        vbox.addLayout(self.mot_aper_x.layout())
        vbox.addLayout(self.mot_aper_y.layout())
        vbox.addLayout(self.mot_aper_z.layout())
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignLeft)

        self.motor_display.append(self.mot_aper_x)
        self.motor_display.append(self.mot_aper_y)
        self.motor_display.append(self.mot_aper_z)
        return vbox

    def vbox_motor_zp(self):
        self.mot_zp_x = Motor_layout(self, 'zp.x', 'zp.x', 'um')
        self.mot_zp_y = Motor_layout(self, 'zp.y', 'zp.y', 'um')
        self.mot_zp_z = Motor_layout(self, 'zp.z', 'zp.z', 'mm')

        vbox = QVBoxLayout()
        vbox.addLayout(self.mot_zp_x.layout())
        vbox.addLayout(self.mot_zp_y.layout())
        vbox.addLayout(self.mot_zp_z.layout())
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignLeft)

        self.motor_display.append(self.mot_zp_x)
        self.motor_display.append(self.mot_zp_y)
        self.motor_display.append(self.mot_zp_z)
        return vbox

    def vbox_motor_detU(self):
        self.mot_detU_x = Motor_layout(self, 'DetU.x', 'DetU.x','mm')
        self.mot_detU_y = Motor_layout(self, 'DetU.y', 'DetU.y','mm')
        self.mot_detU_z = Motor_layout(self, 'DetU.z', 'DetU.z','mm')
        self.motor_display.append(self.mot_detU_x)
        self.motor_display.append(self.mot_detU_y)
        self.motor_display.append(self.mot_detU_z)

        vbox = QVBoxLayout()
        vbox.addLayout(self.mot_detU_x.layout())
        vbox.addLayout(self.mot_detU_y.layout())
        vbox.addLayout(self.mot_detU_z.layout())
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignLeft)
        return vbox

    def vbox_motor_dcm_th2(self):
        self.mot_dcm_th2 = DCM_th2_chi2(self, 'dcm_th2', 'dcm_th2', 'deg')
        self.mot_dcm_th2_pzt = PZT_th2_chi2(self, 'pzt_dcm_th2', 'pzt_th2', 'um')
        self.motor_display.append(self.mot_dcm_th2)
        self.motor_display.append(self.mot_dcm_th2_pzt)
        vbox = QVBoxLayout()
        vbox.addLayout(self.mot_dcm_th2.layout())
        vbox.addLayout(self.mot_dcm_th2_pzt.layout()) 
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignLeft)
        return vbox

    def vbox_motor_dcm_chi2(self):
        self.mot_dcm_chi2 = DCM_th2_chi2(self, 'dcm_chi2', 'dcm_chi2', 'deg')
        self.mot_dcm_chi2_pzt = PZT_th2_chi2(self, 'pzt_dcm_chi2', 'pzt_chi2', 'um')
        self.motor_display.append(self.mot_dcm_chi2)
        self.motor_display.append(self.mot_dcm_chi2_pzt)
        vbox = QVBoxLayout()
        vbox.addLayout(self.mot_dcm_chi2.layout())
        vbox.addLayout(self.mot_dcm_chi2_pzt.layout()) 
        vbox.addStretch()
        vbox.setAlignment(QtCore.Qt.AlignLeft)
        return vbox
    

    ################ Tab 3  ###################
    def vbox_other_func(self):
        lb_empty1 = QLabel()
        lb_empty2 = QLabel()
        hbox = QHBoxLayout()
        hbox.addLayout(self.vbox_load_external_py_file())
        #hbox.addLayout(self.vbox_global_var())        
        hbox.addWidget(lb_empty1)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addStretch()

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(self.vbox_ipython())
        vbox.addWidget(lb_empty2)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        return vbox

    def vbox_load_external_py_file(self):
        lb_empty = QLabel()
        lb_empty2 = QLabel()
        lb_external_file = FixObj(QLabel, self.font1, 'Load external .py file:', 180).run()
        self.pb_ext_file = FixObj(QPushButton, self.font2, 'Open and Load', 150).run()
        self.pb_ext_file.clicked.connect(self.fun_load_ext_py_file)
        self.tx_ext_file_msg = FixObj(QPlainTextEdit, self.font2, '', 600, 200).run()
        #self.tx_ext_file_msg.setFont(self.font2)
        #self.tx_ext_file_msg.setFixedHeight(200)
        #self.tx_ext_file_msg.setFixedWidth(600)

        hbox = QHBoxLayout()
        hbox.addWidget(lb_external_file)
        #hbox.addWidget(self.pb_ext_file)
        hbox.addWidget(lb_empty)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.tx_ext_file_msg)
        vbox.addWidget(self.pb_ext_file)
        vbox.addWidget(lb_empty2)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox

    def vbox_global_var(self):
        lb_empty = QLabel()
        lb_empty2 = QLabel()
        hbox = QHBoxLayout()
        hbox.addLayout(self.vbox_global_var_msg())
        hbox.addLayout(self.vbox_global_var_name_list())
        hbox.addLayout(self.vbox_global_var_value_editor())
        hbox.addWidget(lb_empty)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addStretch()

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)        
        vbox.addLayout(self.hbox_global_var_button()) 
        vbox.addWidget(lb_empty)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox

    def vbox_global_var_msg(self):
        lb_empty2 = QLabel()        
        lb_msg = FixObj(QLabel, self.font1, 'Python input', 120, 27).run()

        self.tx_var_file_msg = FixObj(QPlainTextEdit, self.font2, '', 250, 200).run()

        vbox = QVBoxLayout()
        vbox.addWidget(lb_msg)
        vbox.addWidget(self.tx_var_file_msg) 
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox

    def hbox_global_var_button(self): 
        lb_empty = QLabel()
        lb_sep = FixObj(QLabel, self.font2, '', 0, 10).run()
        self.lb_var_msg = FixObj(QLabel, self.font2, 'Msg: ', 400).run()
        self.pb_var_file = FixObj(QPushButton, self.font2, 'Execute', 80, 40).run()
        self.pb_var_file.clicked.connect(self.define_global_var)

        self.pb_var_save = FixObj(QPushButton, self.font2, 'Save', 80, 40).run()
        self.pb_var_save.clicked.connect(self.save_var_to_file)

        self.pb_var_load = FixObj(QPushButton, self.font2, 'Load', 80, 40).run()
        self.pb_var_load.clicked.connect(self.load_global_var_file)

        self.pb_var_clear = FixObj(QPushButton, self.font2, 'Clear', 80, 40).run()
        self.pb_var_clear.clicked.connect(self.clear_global_var)


        hbox_button = QHBoxLayout()
        hbox_button.addWidget(self.pb_var_file)
        hbox_button.addWidget(self.pb_var_save)        
        hbox_button.addWidget(self.pb_var_load)
        hbox_button.addWidget(self.pb_var_clear)    
        hbox_button.addWidget(lb_sep)
        hbox_button.addWidget(self.lb_var_msg)
        hbox_button.addWidget(lb_empty)
        hbox_button.setAlignment(QtCore.Qt.AlignLeft)
        return hbox_button

    def vbox_global_var_name_list(self):
        lb_var_list = FixObj(QLabel, self.font1, 'Var.', 70, 27).run()

        self.lst_saved_var = FixObj(QListWidget, self.font2, '', 200, 200).run()
        #self.lst_saved_var.setFixedHeight(200)
        #self.lst_saved_var.setFixedWidth(150)
        #self.lst_saved_var.setFont(self.font2)
        self.lst_saved_var.itemClicked.connect(self.show_varible_value)
        vbox = QVBoxLayout()
        vbox.addWidget(lb_var_list)
        vbox.addWidget(self.lst_saved_var)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox
    '''
    def vbox_global_var_value_list(self):
        lb_value_list = FixObj(QLabel, self.font1, 'Value', 70, 27).run()
        self.lst_saved_var_value = FixObj(QListWidget, self.font2, '', 250, 200).run()
        vbox = QVBoxLayout()
        vbox.addWidget(lb_value_list)
        vbox.addWidget(self.lst_saved_var_value)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox
    '''
    def vbox_global_var_value_editor(self):
        self.tx_saved_var_value = FixObj(QPlainTextEdit, self.font2, '', 350, 200).run()
        
        lb_value_list = FixObj(QLabel, self.font1, 'Value', 70, 27).run()
        vbox = QVBoxLayout()
        vbox.addWidget(lb_value_list)
        vbox.addWidget(self.tx_saved_var_value)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox

    '''
    def vbox_global_var_command_list(self):
        lb_var_list_comm = FixObj(QLabel, self.font1, 'Command history', 160, 27).run()
        self.lst_saved_var_comm = FixObj(QListWidget, self.font2, '', 220, 200).run()
        self.lst_saved_var_comm.setFixedHeight(200)
        self.lst_saved_var_comm.setFixedWidth(220)
        self.lst_saved_var_comm.setFont(self.font2)
        vbox = QVBoxLayout()
        vbox.addWidget(lb_var_list_comm)
        vbox.addWidget(self.lst_saved_var_comm)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox
    '''
    '''
    def vbox_global_var_value(self):
        lb_var_list_val = FixObj(QLabel, self.font1, 'Value', 120).run()
        self.lst_saved_var_val = FixObj(QListWidget, self.font3, '', 240, 200).run()
        vbox = QVBoxLayout()
        vbox.addWidget(lb_var_list_val)
        vbox.addWidget(self.lst_saved_var_val)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        vbox.addStretch()
        return vbox
    '''

    def save_var_to_file(self):
        options = QFileDialog.Option()
        options |= QFileDialog.DontUseNativeDialog
        fn,_ = QFileDialog.getSaveFileName(self, "Save to file", "")
        print(fn)
        if fn:
            fn_split = fn.split('/')
            fn_short = fn
            if len(fn_split) > 3:
                fn_short = '/'.join(t for t in fn_split[-3:])
            msg = ''
            try:
                if not fn.split('.')[-1] == 'py':
                    fn += '.py'
                    fn_short += '.py'
                with open(fn,'w') as f:
                    cmd = self.tx_var_file_msg.toPlainText()
                    f.write(cmd)
                msg = f'saved to .../{fn_short}'
                print(f'saved to {fn}')
            except Exception as err:
                msg = str(err)
                print(msg)
            finally:
                self.lb_var_msg.setText('Msg: ' + msg)
                   
    def define_global_var(self):
        cmd = self.tx_var_file_msg.toPlainText()
        msg = ''
        fn_save_tmp = '/tmp/tmp_global_variable.py'
        with open(fn_save_tmp, 'w') as f:
            f.write(cmd)
        self.update_variable_list(fn_save_tmp)

    def load_global_var_file(self):
        options = QFileDialog.Option()
        options |= QFileDialog.DontUseNativeDialog
        file_type = 'python files (*.py)'
        fn, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", file_type, options=options)
        if fn:
            fn_split = fn.split('/')
            fn_short = fn
            self.update_variable_list(fn)
            if len(fn_split) > 2:
                fn_short = '/'.join(t for t in fn_split[-2:])
            '''
            try:
                self.update_variable_list(fn)
                msg = f'File loaded: .../{fn_short}'
            except:
                msg = f'fails to load .../{fn_short}'
            finally: 
                print(msg)  
                self.lb_var_msg.setText('Msg: ' + msg)
            '''

    def clear_global_var(self):
        self.custom_variable_dict = {}
        self.lst_saved_var.clear()
        self.tx_saved_var_value.clear()

    def update_variable_list(self, fn_save_tmp):
        dict_variable = extract_variable(fn_save_tmp)
        dict_function = extract_function(fn_save_tmp, 'def')
        dict_class = extract_function(fn_save_tmp, 'class')

        self.custom_variable_dict = merge_dict(self.custom_variable_dict, dict_variable)
        self.custom_variable_dict = merge_dict(self.custom_variable_dict, dict_function)
        self.custom_variable_dict = merge_dict(self.custom_variable_dict, dict_class)

        keys = [k for k in self.custom_variable_dict.keys()]
        self.lst_saved_var.clear()
        for k in keys:
            self.lst_saved_var.addItem(k)

    def show_varible_value(self):
        item = self.lst_saved_var.selectedItems()
        key = item[0].text()
        command = self.custom_variable_dict[key]['command']
        value = self.custom_variable_dict[key]['value']
        key_type = self.custom_variable_dict[key]['type']
        cmd0 = ''.join(c for c in command)

        cmd = '\n'
        if key_type == 'variable':
            cmd0 = cmd0.lstrip()
            cmd0 = f'command:\n{key} = {cmd0}\n'
            cmd += f'value:\n{key} = {value}' 
        text = cmd0 + cmd
        self.tx_saved_var_value.setPlainText(text)

    def fun_load_ext_py_file(self):
        options = QFileDialog.Option()
        options |= QFileDialog.DontUseNativeDialog
        file_type = 'python files (*.py)'
        fn, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", file_type, options=options)
        if fn:
            fname_read = fn   
            try: 
                get_ipython().run_line_magic("run", f"-i {fn}")
                msg = f'Loaded successful: {fn}\n'     
            except:
                msg = f'FAILS TO LOAD FILE: {fn}\n'           
            self.msg_external_file += msg
            self.tx_ext_file_msg.setPlainText(self.msg_external_file)

    def enable_reset_reading(self):
        for mot in self.motor_display:
            if hasattr(mot, 'button_reset_reading'):
                if self.chk_reset_reading.isChecked():
                    if 'zps' in mot.motor_name and (not 'zps.pi_x' in mot.motor_name) : # zps.sx, y, z, pi_r
                        mot.button_step_minus.setVisible(False)
                        mot.editor_step_size.setVisible(False)
                        mot.button_step_plus.setVisible(False)
                        mot.step_unit.setVisible(False)
                        mot.button_reset_reading.setVisible(True)
                        mot.editor_reset_reading.setVisible(True)
                        
                    mot.button_reset_reading.setEnabled(True)
                    mot.editor_reset_reading.setEnabled(True)
                    # specially for XEng
                    self.mot_sample_e.label_eng_calib.setVisible(False)
                    self.mot_sample_e.cbox_dcm_only.setVisible(True)

                else:
                    mot.button_reset_reading.setEnabled(False)
                    mot.editor_reset_reading.setEnabled(False)
                    if 'zps' in mot.motor_name and (not 'zps.pi_x' in mot.motor_name): # zps.sx, y, z, pi_r
                        mot.button_reset_reading.setVisible(False)
                        mot.editor_reset_reading.setVisible(False)
                        mot.button_step_minus.setVisible(True)
                        mot.editor_step_size.setVisible(True)
                        mot.button_step_plus.setVisible(True)
                        mot.step_unit.setVisible(True)
                    # specially for XEng                   
                    self.mot_sample_e.cbox_dcm_only.setVisible(False)
                    self.mot_sample_e.cbox_dcm_only.setChecked(False)
                    self.mot_sample_e.label_eng_calib.setVisible(True)
                
    def record_eng_calib(self):
        global CALIBER
        try:
            eng_id = int(self.tx_rec_eng_id.text())
            record_calib_pos_new(eng_id)
            self.display_calib_eng_only()
        except Exception as err:
            print(err)

    def cal_zone_plate_param(self):
        h = 6.6261e-34
        c = 3e8
        ec = 1.602e-19
        try:
            eng = float(self.tx_xray_eng.text())
            zp_width = float(self.tx_zp_width.text())
            zp_dia = float(self.tx_zp_diamter.text())
            zp_mag = float(self.tx_txm_mag.text())
            vlm_mag = float(self.tx_vlm_mag.text())
            mag = zp_mag * vlm_mag

            wave_length = h * c / (ec * eng * 1000) * 1e9  # nm
            focal_length = zp_width * zp_dia / (wave_length) / 1000  # mm
            NA = wave_length / (2 * zp_width)
            DOF = wave_length / NA**2 / 1000  # um

            zp_pos = focal_length * (zp_mag + 1) / zp_mag
            ccd_pos = zp_pos * (zp_mag + 1)

            self.tx_zp_wl.setText(f'{wave_length:4.3f}')
            self.tx_zp_fl.setText(f'{focal_length:4.3f}')
            self.tx_zp_na.setText(f'{NA:4.3f}')
            self.tx_zp_dof.setText(f'{DOF:4.3f}')
            self.tx_zp_dis.setText(f'{zp_pos:4.4f}')
            self.tx_zp_ccd.setText(f'{ccd_pos:4.2f}')
        except Exception as err:
            print(err)
            print('something wrong, check inputs')

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
            
        # update label information
        self.lst_eng_calib.sortItems()
        eng_list_sort = np.sort(calib_eng_list)
        eng_lb = '(calib. at: '
        for eng in eng_list_sort:
            eng_lb += f'{eng:2.1f},  '
        eng_lb += 'keV)'
        #self.lb_note.setText(eng_lb)
        self.mot_sample_e.label_eng_calib.setText(eng_lb)

        
        '''
        self.lb_current_mag.setText(f'{GLOBAL_MAG:3.2f}')
        self.lb_zp_mag.setText(f'{GLOBAL_MAG/GLOBAL_VLM_MAG:3.2f}')
        self.lb_pix_size.setText(f'{6500./GLOBAL_MAG:2.2f} nm')
        self.lb_pixel_size.setText(f'{6500./GLOBAL_MAG:2.2f} nm')
        '''

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
                if 'ic' in mname:
                    val = motor[mname].value
                    self.lb_op_3.setText(f'{val:5.6e}')
                elif 'filter' in mname:
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
                try:
                    val = motor[mname].position
                except:
                    val = motor[mname].value
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

def RS(motor_name, val=0):
    global txm
    if motor_name == 'x' or motor_name == 1:
        motor = zps.sx
    elif motor_name == 'y' or motor_name == 2:
        motor = zps.sy
    elif motor_name == 'z' or motor_name == 3:
        motor = zps.sz
    elif motor_name == 'r' or motor_name == 4:
        motor = zps.pi_r
    else:
        print('un-recongnized motor name in: "x", "y", "z", "r"')
        return 0
    RE(mv(motor.motor_calib, 1))
    RE(mv(motor, val))
    RE(mv(motor.motor_calib, 0))
    txm.mot_sample_x.init_pos_display_sample()
    txm.mot_sample_y.init_pos_display_sample()
    txm.mot_sample_z.init_pos_display_sample()
    txm.mot_sample_r.init_pos_display_sample()


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
    func_name = f'fxi_load_{fname_write_short.split(".")[0]}'
    file_lines.append(f'def {func_name}():')
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
    file_lines = convert_initial_digit_to_string(file_lines)
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
        arg_val = ':'.join(t for t in l.split(':')[1:])
        arg_val = arg_val.strip().replace(',', '')
        #arg_val = l[len(arg_name)+1:].strip().replace(',', '')
        lines_copy[i] = arg_name + ': ' + '"' + arg_val + '",'
    return lines_copy

def convert_initial_digit_to_string(file_lines):
    lines_copy = file_lines.copy()
    idx = []
    for i, l in enumerate(file_lines):
        arg_name = l.split(':')[0]
        arg_val = ':'.join(t for t in l.split(':')[1:])
        arg_val = arg_val.strip().replace(',', '')
        try:
            tmp = eval(arg_val)
        except:
            try:
                if arg_val[0].isdigit():
                    lines_copy[i] = arg_name + ':' + '"' + arg_val + '",'
            except:
                pass
    return lines_copy

def convert_epics_to_string(file_lines):
    lines_copy = file_lines.copy()
    idx = []
    for i, l in enumerate(file_lines):
        if 'Epics' in l or 'prefix' in l:
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

def extract_variable(file_name):
    # get defined variable from .py file
    # exclude variable defined inside "function" and "class"
    msg = ''
    with open(file_name, 'r') as f:
       lines = f.readlines()
    arg_name = []
    arg_command = []
    arg_value = []    
    get_ipython().run_line_magic("run", f"-i {file_name}")
    for i, l in enumerate(lines):
        if len(l)-len(l.lstrip()) > 0: # there are leading spaces
            continue
        t = l.split('=')
        if len(t) == 2:
            try:
                #val = eval(t[1])
                arg_name.append(t[0])
                val = eval(arg_name[-1])                
                arg_command.append(t[1].replace('\n', ''))
                arg_value.append(val)
            except:
                msg = f'Syntax error found in line {i}'
                continue
    dict = {}
    n = len(arg_command)
    for i in range(n):
        tmp_dict = {}
        tmp_dict['command'] = arg_command[i].lstrip()
        tmp_dict['value'] = arg_value[i]
        tmp_dict['type'] = 'variable'
        dict[arg_name[i]] = tmp_dict
    return dict

def extract_function(fname, key='def'):
    with open(fname, 'r') as f:
        lines = f.readlines()        
    n = len(lines)
    n_fun = 0
    dict_fun = {}
    txt_fun_name = []
    line_fun = []    
    len_key = len(key)   
    find_fun = False 
    for i in range(n-1):        
        l = lines[i]
        l_next = lines[i+1]
        if l[:len_key+1] == key + ' ':
            find_fun = True
            txt_fun_name.append(l[len_key:].split('(')[0].lstrip())
        if find_fun:
            line_fun.append(l)
            if l_next[0] != ' ':                
                dict_fun[txt_fun_name[-1]] = line_fun
                line_fun = []
                n_fun = n_fun + 1
                find_fun = False
    if find_fun:
        if l_next[0] == ' ':
            line_fun.append(l_next)
        dict_fun[txt_fun_name[-1]] = line_fun
        n_fun += 1 

    dict = {}
    for k in dict_fun.keys():
        tmp_dict = {}
        tmp_dict['command'] = dict_fun[k]
        tmp_dict['value'] = ''
        tmp_dict['type'] = key
        dict[k] = tmp_dict
    return dict

def run_main():
    global txm
    app = QApplication(sys.argv)
    txm = App()
    txm.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_main()

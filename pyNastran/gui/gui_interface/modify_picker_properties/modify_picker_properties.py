"""
based on manage_actors.py
"""
from __future__ import print_function
from math import log10, ceil, floor
from six import iteritems

from pyNastran.gui.qt_version import qt_version
if qt_version == 4:
    from PyQt4 import QtCore, QtGui
    from PyQt4.QtGui import (
        QDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QDockWidget, QTableView, QWidget, QDoubleSpinBox,
        QApplication, QGridLayout, QHBoxLayout, QVBoxLayout,
    )
elif qt_version == 5:
    from PyQt5 import QtCore, QtGui
    from PyQt5.QtWidgets import (
        QDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QDockWidget, QTableView, QWidget, QDoubleSpinBox,
        QApplication, QGridLayout, QHBoxLayout, QVBoxLayout,
    )
elif qt_version == 'pyside':
    from PySide import QtCore, QtGui
    from PySide.QtGui import (
        QDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QDockWidget, QTableView, QWidget, QDoubleSpinBox,
        QApplication, QGridLayout, QHBoxLayout, QVBoxLayout,
    )
else:
    raise NotImplementedError('qt_version = %r' % qt_version)


class ModifyPickerPropertiesMenu(QDialog):

    def __init__(self, data, win_parent=None):
        self.win_parent = win_parent

        self._size = data['size'] * 100.
        self.out_data = data
        self.dim_max = data['dim_max']

        QDialog.__init__(self, win_parent)
        self.setWindowTitle('Modify Picker Properties')
        self.create_widgets()
        self.create_layout()
        self.set_connections()
        width = 260
        height = 130
        self.resize(width, height)
        #self.show()

    def create_widgets(self):
        # Size
        self.size = QLabel("Percent of Screen Size:")
        self.size_edit = QDoubleSpinBox(self)
        self.size_edit.setRange(0., 10.)

        log_dim = log10(self.dim_max)
        decimals = int(ceil(abs(log_dim)))

        decimals = max(3, decimals)
        self.size_edit.setDecimals(decimals)
        self.size_edit.setSingleStep(10. / 5000.)
        self.size_edit.setValue(self._size)

        # closing
        #self.apply_button = QPushButton("Apply")
        #self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Close")

    def create_layout(self):
        grid = QGridLayout()

        grid.addWidget(self.size, 1, 0)
        grid.addWidget(self.size_edit, 1, 1)

        ok_cancel_box = QHBoxLayout()
        #ok_cancel_box.addWidget(self.apply_button)
        #ok_cancel_box.addWidget(self.ok_button)
        ok_cancel_box.addWidget(self.cancel_button)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)

        vbox.addStretch()
        vbox.addLayout(ok_cancel_box)
        self.setLayout(vbox)
        self.layout()

    #def on_color(self):
        #pass

    def set_connections(self):
        self.size_edit.valueChanged.connect(self.on_size)
        if qt_version == 4:
            self.connect(self.size_edit, QtCore.SIGNAL('editingFinished()'), self.on_size)
            self.connect(self.size_edit, QtCore.SIGNAL('valueChanged()'), self.on_size)
            self.connect(self.size_edit, QtCore.SIGNAL('clicked()'), self.on_size)

            #self.connect(self.apply_button, QtCore.SIGNAL('clicked()'), self.on_apply)
            #self.connect(self.ok_button, QtCore.SIGNAL('clicked()'), self.on_ok)
            self.connect(self.cancel_button, QtCore.SIGNAL('clicked()'), self.on_cancel)
            self.connect(self, QtCore.SIGNAL('triggered()'), self.closeEvent)
        else:
            self.size_edit.editingFinished.connect(self.on_size)
            self.size_edit.valueChanged.connect(self.on_size)
            ## ??? clicked

            self.cancel_button.clicked.connect(self.on_cancel)
            #self.connect(self, QtCore.SIGNAL('triggered()'), self.closeEvent)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.out_data['close'] = True
        event.accept()

    def on_size(self):
        self._size = float(self.size_edit.text())
        self.on_apply(force=True)

    @staticmethod
    def check_float(cell):
        text = cell.text()
        value = float(text)
        return value, True

    def on_validate(self):
        size_value, flag0 = self.check_float(self.size_edit)

        if flag0:
            self._size = size_value
            #self.out_data['min'] = min(min_value, max_value)
            #self.out_data['max'] = max(min_value, max_value)
            self.out_data['clicked_ok'] = True
            return True
        return False

    def on_apply(self, force=False):
        passed = self.on_validate()
        if (passed or Force) and self.win_parent is not None:
            self.win_parent.element_picker_size = self._size / 100.
        return passed

    def on_ok(self):
        self.out_data['clicked_ok'] = True
        self.out_data['clicked_cancel'] = False
        self.out_data['close'] = True
        passed = self.on_apply()
        if passed:
            self.close()
            #self.destroy()

    def on_cancel(self):
        self.out_data['clicked_cancel'] = True
        self.out_data['close'] = True
        self.close()


def main():
    # kills the program when you hit Cntl+C from the command line
    # doesn't save the current state as presumably there's been an error
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


    import sys
    # Someone is launching this directly
    # Create the QApplication
    app = QApplication(sys.argv)
    #The Main window
    d = {
        'size' : 10.,
        'dim_max' : 502.
    }
    main_window = ModifyPickerPropertiesMenu(d)
    main_window.show()
    # Enter the main loop
    app.exec_()

if __name__ == "__main__":
    main()

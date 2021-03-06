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
        QDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QDockWidget, QTableView, QWidget,
        QApplication, QDoubleSpinBox, QGridLayout, QHBoxLayout, QVBoxLayout, QColorDialog)
elif qt_version == 5:
    from PyQt5 import QtCore, QtGui
    from PyQt5.QtWidgets import (
        QDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QDockWidget, QTableView, QWidget,
        QApplication, QDoubleSpinBox, QGridLayout, QHBoxLayout, QVBoxLayout, QColorDialog)
elif qt_version == 'pyside':
    from PySide import QtCore, QtGui
    from PySide.QtGui import (
        QDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QDockWidget, QTableView, QWidget,
        QApplication, QDoubleSpinBox, QGridLayout, QHBoxLayout, QVBoxLayout, QColorDialog)
else:
    raise NotImplementedError('qt_version = %r' % qt_version)


class ModifyLabelPropertiesMenu(QDialog):

    def __init__(self, data, win_parent=None):
        self.win_parent = win_parent
        float_color = data['color']
        assert len(float_color) == 3, float_color
        assert isinstance(float_color[0], float), float_color
        self.float_color = float_color
        self.int_color = [int(colori * 255) for colori in float_color]

        assert isinstance(self.float_color[0], float), self.float_color
        assert isinstance(self.int_color[0], int), self.int_color

        self._size = data['size']
        self.out_data = data
        self.dim_max = data['dim_max']

        QDialog.__init__(self, win_parent)
        self.setWindowTitle('Modify Label Properties')
        self.create_widgets()
        self.create_layout()
        self.set_connections()
        width = 260
        height = 130
        self.resize(width, height)
        #self.show()

    def create_widgets(self):
        # Min
        self.color = QLabel("Color:")
        self.color_edit = QPushButton()
        #self.color_edit.setFlat(True)

        qcolor = QtGui.QColor()
        qcolor.setRgb(*self.int_color)
        palette = QtGui.QPalette(self.color_edit.palette())
        palette.setColor(QtGui.QPalette.Background, QtGui.QColor('blue'))
        self.color_edit.setPalette(palette)

        self.color_edit.setStyleSheet("QPushButton {"
                                      "background-color: rgb(%s, %s, %s);" % tuple(self.int_color) +
                                      #"border:1px solid rgb(255, 170, 255); "
                                      "}")


        # Size
        self.size = QLabel("Size:")
        self.size_edit = QDoubleSpinBox(self)
        self.size_edit.setRange(0.0, self.dim_max)

        log_dim = log10(self.dim_max)
        decimals = int(ceil(abs(log_dim)))
        decimals = max(6, decimals)
        self.size_edit.setDecimals(decimals)
        #self.size_edit.setSingleStep(self.dim_max / 100.)
        self.size_edit.setSingleStep(self.dim_max / 1000.)
        self.size_edit.setValue(self._size)

        # closing
        #self.apply_button = QPushButton("Apply")
        #self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Close")

    def create_layout(self):
        grid = QGridLayout()

        grid.addWidget(self.color, 0, 0)
        grid.addWidget(self.color_edit, 0, 1)
        #grid.addWidget(self.min_button, 0, 2)

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

    def on_color(self):
        rgb_color_ints = self.int_color

        col = QColorDialog.getColor(QtGui.QColor(*rgb_color_ints), self,
                                    "Choose a label color")
        if col.isValid():
            float_color = col.getRgbF()[:3]  # floats
            self.int_color = [int(colori * 255) for colori in float_color]
            self.float_color = float_color

            assert isinstance(self.float_color[0], float), self.float_color
            assert isinstance(self.int_color[0], int), self.int_color

            self.color_edit.setStyleSheet("QPushButton {"
                                          "background-color: rgb(%s, %s, %s);" % tuple(self.int_color) +
                                          #"border:1px solid rgb(255, 170, 255); "
                                          "}")
        self.on_apply(force=True)

    #def on_color(self):
        #pass

    def set_connections(self):
        self.size_edit.valueChanged.connect(self.on_size)

        if qt_version == 4:
            self.connect(self.size_edit, QtCore.SIGNAL('editingFinished()'), self.on_size)
            self.connect(self.size_edit, QtCore.SIGNAL('valueChanged()'), self.on_size)
            self.connect(self.size_edit, QtCore.SIGNAL('clicked()'), self.on_size)
            self.connect(self.color_edit, QtCore.SIGNAL('clicked()'), self.on_color)

            #self.connect(self.apply_button, QtCore.SIGNAL('clicked()'), self.on_apply)
            #self.connect(self.ok_button, QtCore.SIGNAL('clicked()'), self.on_ok)
            self.connect(self.cancel_button, QtCore.SIGNAL('clicked()'), self.on_cancel)
            self.connect(self, QtCore.SIGNAL('triggered()'), self.closeEvent)
        else:
            self.size_edit.editingFinished.connect(self.on_size)
            self.size_edit.valueChanged.connect(self.on_size)
            #self.size_edit.clicked
            self.color_edit.clicked.connect(self.on_color)
            self.cancel_button.clicked.connect(self.on_cancel)
            # closeEvent

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.out_data['close'] = True
        event.accept()

    def on_size(self):
        self._size = float(self.size_edit.text())
        self.on_apply(force=True)
        #self.min_edit.setText(str(self._default_min))
        #self.min_edit.setStyleSheet("QLineEdit{background: white;}")

    @staticmethod
    def check_float(cell):
        text = cell.text()
        value = float(text)
        return value, True
        #try:
            #value = eval_float_from_string(text)
            #cell.setStyleSheet("QLineEdit{background: white;}")
            #return value, True
        #except ValueError:
            #cell.setStyleSheet("QLineEdit{background: red;}")
            #return None, False

    def on_validate(self):
        size_value, flag0 = self.check_float(self.size_edit)
        assert isinstance(self.float_color[0], float), self.float_color
        assert isinstance(self.int_color[0], int), self.int_color

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
            self.win_parent.set_labelsize_color(self._size, self.float_color)
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
        'color' : (1., 0., 0.), # red
        'size' : 10.,
        'dim_max' : 502.
    }
    main_window = ModifyLabelPropertiesMenu(d)
    main_window.show()
    # Enter the main loop
    app.exec_()

if __name__ == "__main__":
    main()

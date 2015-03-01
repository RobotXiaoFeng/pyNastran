# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals, print_function
from six import string_types, iteritems
from six.moves import range

# standard library
import sys
import os.path
import traceback
import inspect
#import webbrowser
#webbrowser.open("http://xkcd.com/353/")

from PyQt4 import QtCore, QtGui
print("Using PyQt4")
fmode = 1
#except ImportError:
    #try:
        #from PySide import QtCore, QtGui
        #print("Using PySide")
        #fmode = 2
    #except ImportError:
        #msg = 'Failed to import PySide or PyQt4'
        #raise ImportError(msg)
assert fmode in [1, 2]

# 3rd party
import vtk

# pyNastran
import pyNastran
from pyNastran.utils import print_bad_path
from pyNastran.gui.formats import (NastranIO, Cart3dIO, PanairIO, LaWGS_IO,
    STL_IO, TecplotIO, TetgenIO, Usm3dIO, Plot3d_io, ShabpIO,
    is_nastran, is_cart3d, is_panair, is_lawgs,
    is_shabp, is_stl, is_tecplot, is_tetgen, is_usm3d, is_plot3d)
from pyNastran.gui.arg_handling import get_inputs
from pyNastran.gui.gui_common import GuiCommon2

try:
    pkg_path = sys._MEIPASS #@UndefinedVariable
    script_path = os.path.join(pkg_path, 'scripts')
    icon_path = os.path.join(pkg_path, 'icons')
except:
    pkg_path = pyNastran.__path__[0]
    script_path = os.path.join(pkg_path, 'gui', 'scripts')
    icon_path = os.path.join(pkg_path, 'gui', 'icons')

#print('script_path = %s' % script_path)
#print('icon_path = %s' % icon_path)

# tcolorpick.png and tabout.png trefresh.png icons on LGPL license, see
# http://openiconlibrary.sourceforge.net/gallery2/?./Icons/actions/color-picker-grey.png
# http://openiconlibrary.sourceforge.net/gallery2/?./Icons/actions/help-hint.png
# http://openiconlibrary.sourceforge.net/gallery2/?./Icons/actions/view-refresh-8.png


# kills the program when you hit Cntl+C from the command line
# doesn't save the current state as presumably there's been an error
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(GuiCommon2, NastranIO, Cart3dIO, ShabpIO, PanairIO, LaWGS_IO, STL_IO, TetgenIO, Usm3dIO, Plot3d_io):

    def __init__(self, inputs):
        html_logging = True
        GuiCommon2.__init__(self, html_logging, inputs)

        NastranIO.__init__(self)
        Cart3dIO.__init__(self)
        PanairIO.__init__(self)
        ShabpIO.__init__(self)
        LaWGS_IO.__init__(self)
        STL_IO.__init__(self)
        TetgenIO.__init__(self)
        Usm3dIO.__init__(self)
        Plot3d_io.__init__(self)

        self.build_fmts(fmt_order=None)

        logo = os.path.join(icon_path, 'logo.png')
        self.set_logo(logo)
        self.set_script_path(script_path)
        self.set_icon_path(icon_path)

        self.setup_gui()
        self.setup_post(inputs)

    def build_fmts(self, fmt_order=None):
        fmt_order = [
            'nastran', 'cart3d', 'panair', 'shabp', 'usm3d',  # results
            'lawgs', 'tetgen', 'stl',  #'plot3d',  # no results
        ]
        fmts = []
        for fmt in fmt_order:
            if hasattr(self, 'get_%s_wildcard_geometry_results_functions' % fmt):
                func = 'get_%s_wildcard_geometry_results_functions' % fmt
                data = getattr(self, func)()
                msg = 'macro_name, geo_fmt, geo_func, res_fmt, res_func = data\n'
                msg += 'data = %s'
                assert len(data) == 5, msg % str(data)
                macro_name, geo_fmt, geo_func, res_fmt, res_func = data
                fmts.append((fmt, macro_name, geo_fmt, geo_func, res_fmt, res_func))
            #else:
                #func = 'get_%s_wildcard_geometry_results_functions' % fmt
                #raise RuntimeError(func)

        if len(fmts) == 0:
            RuntimeError('No formats...expected=%s' % fmt_order)
        self.fmts = fmts

        #fmts = [
            ## results
            #('nastran', 'Nastran', 'Nastran BDF (*.bdf; *.dat; *.nas)', self.load_nastran_geometry, 'Nastran OP2 (*.op2)', self.load_nastran_results),
            #('cart3d', 'Cart3d', 'Cart3d (*.tri; *.triq)', self.load_cart3d_geometry, 'Cart3d (*.triq)', self.load_cart3d_results),
            #('panair', 'Panair', 'Panair (*.inp)', self.load_panair_geometry, 'Panair (*.agps);;Panair (*.out)',  self.load_panair_results),
            #('shabp', 'S/HABP', 'Shabp (*.geo; *.mk5; *.inp)', self.load_shabp_geometry, 'Shabp (*.out)', self.load_shabp_results),
            #('usm3d', 'Usm3D', 'USM3D (*.cogsg; *.front)', self.load_usm3d_geometry, 'Usm3d (*.flo)', self.load_usm3d_results),

            ## no results
            #('lawgs', 'LaWGS', 'LaWGS (*.inp; *.wgs)', self.load_lawgs_geometry, None, None),
            #('tetgen', 'Tetgen', 'Tetgen (*.smesh)', self.load_tetgen_geometry, None, None),
            #('stl', 'STL', 'STereoLithography (*.STL)', self.load_stl_geometry, None, None),
            ##('plot3d', 'Plot3D', 'Plot3D (*.p3d; *.p3da)', self.load_plot3d_geometry, None, None),
        #]
        #self.fmts = fmts
        self.supported_formats = [fmt[0] for fmt in fmts]
        print('supported_formats = %s' % self.supported_formats)
        if len(fmts) == 0:
            raise RuntimeError('no modules were loaded...')

    def create_cell_picker(self):
        # cell picker
        self.cell_picker = vtk.vtkCellPicker()
        #self.point_picker = vtk.vtkPointPicker()
        #self.cell_picker.SetTolerance(0.0005)

    def mousePressEvent(self, ev):
        print('press x,y = (%s, %s)' % (ev.x(), ev.y()))
        if self.is_pick:
            #self.___saveX = ev.x()
            #self.___saveY = ev.y()
            pass
        else:
            self.iren.mousePressEvent(ev)

    def LeftButtonPressEvent(self, ev):
        asfd

    def mouseReleaseEvent(self, ev):
        print('release x,y = (%s, %s)' % (ev.x(), ev.y()))
        if self.is_pick:
            pass
        else:
            self.iren.mousePressEvent(ev)

    def init_cell_picker(self):
        self.is_pick = False
        self.vtk_interactor.SetPicker(self.cell_picker)
        #self.vtk_interactor.SetPicker(self.point_picker)

        def annotate_cell_picker(object, event):
            self.log_command("annotate_cell_picker()")
            picker = self.cell_picker
            if picker.GetCellId() < 0:
                #self.picker_textActor.VisibilityOff()
                pass
            else:
                world_position = picker.GetPickPosition()
                cell_id = picker.GetCellId()
                #ds = picker.GetDataSet()
                select_point = picker.GetSelectionPoint()
                self.log_command("annotate_picker()")
                self.log_info("world_position = %s" % str(world_position))
                self.log_info("cell_id = %s" % cell_id)
                #self.log_info("data_set = %s" % ds)
                self.log_info("selPt = %s" % str(select_point))

                #self.picker_textMapper.SetInput("(%.6f, %.6f, %.6f)"% pickPos)
                #self.picker_textActor.SetPosition(select_point[:2])
                #self.picker_textActor.VisibilityOn()

        def annotate_point_picker(object, event):
            self.log_command("annotate_point_picker()")
            picker = self.cell_picker
            if picker.GetPointId() < 0:
                #self.picker_textActor.VisibilityOff()
                pass
            else:
                world_position = picker.GetPickPosition()
                point_id = picker.GetPointId()
                #ds = picker.GetDataSet()
                select_point = picker.GetSelectionPoint()
                self.log_command("annotate_picker()")
                self.log_info("world_position = %s" % str(world_position))
                self.log_info("point_id = %s" % point_id)
                #self.log_info("data_set = %s" % ds)
                self.log_info("select_point = %s" % str(select_point))

                #self.picker_textMapper.SetInput("(%.6f, %.6f, %.6f)"% pickPos)
                #self.picker_textActor.SetPosition(select_point[:2])
                #self.picker_textActor.VisibilityOn()

        self.cell_picker.AddObserver("EndPickEvent", annotate_cell_picker)
        #self.point_picker.AddObserver("EndPickEvent", annotate_point_picker)

    def on_cell_picker(self):
        self.log_command("on_cell_picker()")
        picker = self.cell_picker
        world_position = picker.GetPickPosition()
        cell_id = picker.GetCellId()
        #ds = picker.GetDataSet()
        select_point = picker.GetSelectionPoint()  # get x,y pixel coordinate

        self.log_info("world_position = %s" % str(world_position))
        self.log_info("cell_id = %s" % cell_id)
        self.log_info("select_point = %s" % str(select_point))
        #self.log_info("data_set = %s" % ds)

    def about_dialog(self):
        """ Display about dialog """
        if fmode == 1:  # PyQt
            copyright = pyNastran.__pyqt_copyright__
        else:
            copyright = pyNastran.__copyright__

        about = [
            'pyNastran QT GUI',
            '',
            'pyNastran v%s' % pyNastran.__version__,
            copyright,
            pyNastran.__author__,
            '',
            '%s' % pyNastran.__website__,
            '',
            'Mouse',
            'Left Click - Rotate',
            'Middle Click - Pan/Recenter Rotation Point',
            'Shift + Left Click - Pan/Recenter Rotation Point',
            'Right Mouse / Wheel - Zoom',
            '',
            'Keyboard Controls',
            #'r   - reset camera view',
            #'X/x - snap to x axis',
            #'Y/y - snap to y axis',
            #'Z/z - snap to z axis',
            #'',
            #'h   - show/hide legend & info',
            'CTRL+I - take a screenshot (image)',
            'CTRL+L - cycle results',
            #'m/M    - scale up/scale down by 1.1 times',
            #'o/O    - rotate counter-clockwise/clockwise 5 degrees',
            's      - view model as a surface',
            'w      - view model as a wireframe',
            '',
            'Reload Model:  using the same filename reload the model',
        ]
        QtGui.QMessageBox.about(self, "About pyNastran GUI", "\n".join(about))

    def on_reload(self):
        """
        Runs the reload button.

        Reload allows you to edit the input model and "reload" the data without
        having to go to the pulldown menu.  For USM3D, we dynamically load the
        latest CFD results time step, which is really handy when you're running
        a job.
        """
        Title = self.Title
        if self.format == 'usm3d':
            self.step_results_usm3d()
        else:
            self.on_load_geometry(self.infile_name, self.format)

        if self.out_filename is None:
            msg = '%s - %s' % (self.format, self.infile_name)
        else:
            msg = '%s - %s - %s' % (self.format, self.infile_name, self.out_filename)
        self.set_window_title(msg)
        self.log_command('on_reload()')
        #self.cycleResults(Title)
        for i in range(10):  #  limit on number of cycles
            if self.Title != Title:
                self.cycleResults(Title)
            else:
                break

    def on_load_geometry(self, infile_name=None, geometry_format=None, plot=True):
        """
        Loads a baseline geometry

        :param infile_name: path to the filename (default=None -> popup)
        :param geometry_format: the geometry format for programmatic loading
        :param plot: Should the baseline geometry have results created and plotted/rendered?
                     If you're calling the on_load_results method immediately after, set it to False
                     (default=True)
        """
        wildcard = ''
        is_failed = False

        if geometry_format and geometry_format.lower() not in self.supported_formats:
            is_failed = True
            #if geometry_format in self.formats:
            msg = 'The import for the %r module failed.\n' % geometry_format
            #else:
                #msg = '%r is not a enabled format; enabled_formats=%s\n' % (geometry_format, self.supported_formats)
                #msg += str("formats = %s" % str(self.formats))
            self.log_error(msg)
            return is_failed

        if infile_name:
            geometry_format = geometry_format.lower()
            print("geometry_format = %r" % geometry_format)

            for fmt in self.fmts:
                fmt_name, _major_name, _geowild, _geofunc, _reswild, _resfunc = fmt
                if geometry_format == fmt_name:
                    load_function = _geofunc
                    if _reswild is None:
                        has_results = False
                    else:
                        has_results = True
                    break
            else:
                self.log_error('---invalid format=%r' % geometry_format)
                is_failed = True
                return is_failed
                raise NotImplementedError('on_load_geometry; infile_name=%r format=%r' % (infile_name, geometry_format))
            formats = [geometry_format]
            filter_index = 0
        else:
            formats = []
            load_functions = []
            has_results_list = []
            wildcard_list = []

            for fmt in self.fmts:
                fmt_name, _major_name, _geowild, _geofunc, _reswild, _resfunc = fmt
                formats.append(_major_name)
                wildcard_list.append(_geowild)
                load_functions.append(_geofunc)

                if _reswild is None:
                    has_results_list.append(False)
                else:
                    has_results_list.append(True)

            wildcard = ';;'.join(wildcard_list)

            # get the filter index and filename
            if infile_name is not None and geometry_format is not None:
                filter_index = formats.index(geometry_format)
            else:
                Title = 'Choose a Geometry File to Load'
                wildcard_index, infile_name = self._create_load_file_dialog(wildcard, Title)
                #print("infile_name = %r" % infile_name)
                #print("wildcard_index = %r" % wildcard_index)
                if not infile_name:
                    is_failed = True
                    return is_failed # user clicked cancel
                filter_index = wildcard_list.index(wildcard_index)

            geometry_format = formats[filter_index]
            load_function = load_functions[filter_index]
            has_results = has_results_list[filter_index]
            #return is_failed

        if load_function is not None:
            self.last_dir = os.path.split(infile_name)[0]

            self.grid.Reset()
            self.grid.Modified()
            self.grid2.Reset()
            self.grid2.Modified()
            #gridResult.Reset()
            #gridResult.Modified()

            if not os.path.exists(infile_name) and geometry_format:
                msg = 'input file=%r does not exist' % infile_name
                self.log_error(msg)
                self.log_error(print_bad_path(infile_name))
                return

            # clear out old data
            if self.modelType is not None:
                clear_name = 'clear_' + self.modelType
                try:
                    dy_method = getattr(self, clear_name)  # 'self.clear_nastran()'
                    dy_method()
                except:
                    print("method %r does not exist" % clear_name)
            self.log_info("reading %s file %r" % (geometry_format, infile_name))

            # inspect the load_geometry method to see what version it's using
            args, varargs, keywords, defaults = inspect.getargspec(load_function)
            try:
                if args[-1] != 'plot':
                    has_results = load_function(infile_name, self.last_dir, plot=plot)
                else:
                    name = load_function.__name__
                    self.log_error("'plot' needs to be added to %r"% name)
                    has_results = load_function(infile_name, self.last_dir)
            except Exception as e:
                msg = traceback.format_exc()
                self.log_error(msg)
                raise
                #return
            #self.vtk_panel.Update()
            self.rend.ResetCamera()

        # the model has been loaded, so we enable load_results
        if filter_index >= 0:
            self.format = formats[filter_index].lower()
            if has_results:
                enable = True
            else:
                enable = False
            #self.load_results.Enable(enable)
        else: # no file specified
            return
        #print("on_load_geometry(infile_name=%r, geometry_format=None)" % infile_name)
        self.infile_name = infile_name

        self.out_filename = None
        #if self.out_filename is not None:
            #msg = '%s - %s - %s' % (self.format, self.infile_name, self.out_filename)
        #else:
        msg = '%s - %s' % (self.format, self.infile_name)
        self.set_window_title(msg)
        self.log_command("on_load_geometry(infile_name=%r, geometry_format=%r)" % (infile_name, self.format))

    def on_load_results(self, out_filename=None):
        """
        Loads a results file.  Must have called on_load_geometry first.

        :param out_filename: the path to the results file
        """
        geometry_format = self.format
        if self.format is None:
            msg = 'on_load_results failed:  You need to load a file first...'
            self.log_error(msg)
            raise RuntimeError(msg)

        if out_filename in [None, False]:
            Title = 'Select a Results File for %s' % self.format
            wildcard = None
            load_function = None

            for fmt in self.fmts:
                fmt_name, _major_name, _geowild, _geofunc, _reswild, _resfunc = fmt
                if geometry_format == fmt_name:
                    wildcard = _reswild
                    load_function = _resfunc
                    break
            else:
                msg = 'format=%r is not supported' % geometry_format
                self.log_error(msg)
                raise RuntimeError(msg)

            if wildcard is None:
                msg = 'format=%r has no method to load results' % geometry_format
                self.log_error(msg)
                return
            wildcard_index, out_filename = self._create_load_file_dialog(wildcard, Title)
        else:

            for fmt in self.fmts:
                fmt_name, _major_name, _geowild, _geofunc, _reswild, _resfunc = fmt
                print('fmt_name=%r geometry_format=%r' % (fmt_name, geometry_format))
                if fmt_name == geometry_format:
                    load_function = _resfunc
                    break
            else:
                msg = 'format=%r is not supported.  Did you load a geometry model?' % geometry_format
                self.log_error(msg)
                raise RuntimeError(msg)

            if 0:
                if geometry_format == 'nastran':
                    load_function = self.load_nastran_results
                elif geometry_format == 'cart3d':
                    load_function = self.load_cart3d_results
                elif geometry_format == 'panair':
                    load_function = self.load_panair_results
                elif geometry_format == 'shabp':
                    load_function = self.load_shabp_results
                #elif geometry_format == 'lawgs':
                    #load_function = None
                #elif geometry_format == 'stl':
                    #load_function = None
                #elif geometry_format == 'tetgen':
                    #load_function = None
                elif geometry_format == 'usm3d':
                    load_function = self.load_usm3d_results
                #elif geometry_format == 'plot3d':
                    #load_function = None
                else:
                    msg = 'format=%r is not supported.  Did you load a geometry model?' % geometry_format
                    self.log_error(msg)
                    raise RuntimeError(msg)

        if out_filename == '':
            return
        if not os.path.exists(out_filename):
            msg = 'result file=%r does not exist' % out_filename
            self.log_error(msg)
            return
            #raise IOError(msg)
        self.last_dir = os.path.split(out_filename)[0]
        load_function(out_filename, self.last_dir)

        self.out_filename = out_filename
        msg = '%s - %s - %s' % (self.format, self.infile_name, out_filename)
        self.set_window_title(msg)
        print("on_load_results(%r)" % out_filename)
        self.out_filename = out_filename
        self.log_command("on_load_results(%r)" % out_filename)

    def closeEvent(self, event):
        """
        Handling saving state before application when application is
        being closed.
        """
        settings = QtCore.QSettings()
        settings.setValue("main_WindowGeometry", self.saveGeometry())
        settings.setValue("mainWindowState", self.saveState())
        settings.setValue("backgroundColor", self.background_col)
        QtGui.qApp.quit()


def main():
    app = QtGui.QApplication(sys.argv)
    QtGui.QApplication.setOrganizationName("pyNastran")
    QtGui.QApplication.setOrganizationDomain(pyNastran.__website__)
    QtGui.QApplication.setApplicationName("pyNastran")
    QtGui.QApplication.setApplicationVersion(pyNastran.__version__)

    inputs = get_inputs()
    window = MainWindow(inputs)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

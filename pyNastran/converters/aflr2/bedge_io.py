from __future__ import print_function
import os

import numpy as np
import vtk

from pyNastran.converters.aflr2.aflr2 import read_bedge
from pyNastran.gui.gui_objects.gui_result import GuiResult


class BEdge_IO(object):
    def __init__(self):
        pass

    def get_bedge_wildcard_geometry_results_functions(self):
        data = (
            'AFLR2 BEdge',
            'AFLR2 BEdge (*.bedge)', self.load_bedge_geometry,
            None, None)
        return data

    def load_bedge_geometry(self, bedge_filename, dirname, name='main', plot=True):
        #skip_reading = self.remove_old_openfoam_geometry(openfoam_filename)
        #if skip_reading:
        #    return

        self.modelType = 'bedge'

        model = read_bedge(bedge_filename)
        print('bedge_filename = %s' % bedge_filename)
        nnodes = model.nodes.shape[0]
        nbars = model.bars.shape[0]
        nelements = nbars

        nodes = model.nodes
        self.nElements = nelements
        self.nNodes = nnodes

        print("nNodes = %s" % self.nNodes)
        print("nElements = %s" % self.nElements)
        assert nelements > 0, nelements

        black = (0., 0., 0.)
        self.create_alternate_vtk_grid(
            'nodes', color=black, line_width=5, opacity=1., point_size=3,
            representation='point')
        self.alt_grids['nodes'].Allocate(nnodes, 1000)
        self.grid.Allocate(self.nElements, 1000)

        points = vtk.vtkPoints()
        points.SetNumberOfPoints(self.nNodes)

        mmax = np.amax(nodes, axis=0)
        mmin = np.amin(nodes, axis=0)
        dim_max = (mmax - mmin).max()
        self.log.info('max = %s' % mmax)
        self.log.info('min = %s' % mmin)
        #print('dim_max =', dim_max)
        #self.update_axes_length(dim_max)

        for inode, node in enumerate(nodes):
            points.InsertPoint(inode, node)

            elem = vtk.vtkVertex()
            elem.GetPointIds().SetId(0, inode)
            self.alt_grids['nodes'].InsertNextCell(elem.GetCellType(), elem.GetPointIds())

        bars = model.bars
        for eid, element in enumerate(bars):
            elem = vtk.vtkLine()
            n1, n2 = element
            try:
                elem.GetPointIds().SetId(0, n1)
                elem.GetPointIds().SetId(1, n2)
            except KeyError:
                print("nodeIDs =", element)
                print(str(element))
                continue
            self.grid.InsertNextCell(elem.GetCellType(), elem.GetPointIds())

        self.nElements = nelements
        self.alt_grids['nodes'].SetPoints(points)
        self.grid.SetPoints(points)
        self.grid.Modified()
        if hasattr(self.grid, 'Update'):
            self.grid.Update()
        #print("updated grid")

        # loadCart3dResults - regions/loads
        #self.TurnTextOn()
        self.scalarBar.VisibilityOn()
        self.scalarBar.Modified()

        self.iSubcaseNameMap = {1: ['AFLR BEDGE', '']}
        cases = {}
        ID = 1

        self._add_alt_actors(self.alt_grids)
        form, cases = self._fill_bedge_case(bedge_filename, cases, ID, nnodes, nelements, model)
        if plot:
            self._finish_results_io2(form, cases)

    def clear_bedge(self):
        pass

    def _fill_bedge_case(self, bedge_filename, cases, ID, nnodes, nelements, model):
        """
        creates the data for the sidebar 'form' and the result 'cases'
        """
        base, ext = os.path.splitext(bedge_filename)
        assert ext == '.bedge', bedge_filename

        tag_filename = base + '.tags'

        cases_new = []
        has_tag_data = False
        results_form = []

        geometry_form = [
            ('ElementID', 0, []),
            ('NodeID', 1, []),
            #('Region', 1, []),
            ('CurveID', 2, []),
            ('SubcurveID', 3, []),
            ('GridBC', 4, []),

            #('TurnAngle', 5, [])
            #('normSpacing', 6, []),
            #('BL_thick', 7, []),
        ]

        form = [
            ('Geometry', None, geometry_form),
        ]

        eids = np.arange(1, nelements + 1)
        nids = np.arange(1, nnodes + 1)


        eid_res = GuiResult(0, header='ElementID', title='ElementID',
                            location='centroid', scalar=eids)
        nid_res = GuiResult(0, header='NodeID', title='NodeID',
                            location='node', scalar=nids)
        curve_res = GuiResult(0, header='CurveID', title='CurveID',
                              location='centroid', scalar=model.curves)
        subcurve_res = GuiResult(0, header='SubcurveID', title='SubcurveID',
                                 location='centroid', scalar=model.subcurves)
        gridbc_res = GuiResult(0, header='GridBC', title='GridBC',
                               location='centroid', scalar=model.grid_bcs)

        icase = 0
        cases[icase] = (eid_res, (0, 'ElementID'))
        cases[icase + 1] = (nid_res, (0, 'NodeID'))
        cases[icase + 2] = (curve_res, (0, 'CurveID'))
        cases[icase + 3] = (subcurve_res, (0, 'SubcurveID'))
        cases[icase + 4] = (gridbc_res, (0, 'GridBC'))
        icase += 5


        #if 0:
            #surf_ids = element_props[:, 0]
            #recon_flags = element_props[:, 1]
            #grid_bcs = element_props[:, 2]

        if hasattr(model, 'turn_angle'):
            gf = ('TurnAngle', 5, [])
            geometry_form.append(gf)
            turnangle_res = GuiResult(0, header='TurnAngle', title='TurnAngle',
                                      location='centroid',
                                      scalar=np.degrees(np.abs(model.turn_angle)))
            cases[icase] = (turnangle_res, (0, 'TurnAngle'))
            icase += 1

        #norm_spacing = model.node_props[:, 0]
        #bl_thickness = model.node_props[:, 1]
        #cases[(ID, 1, 'normSpacing', 1, 'node', '%.3e')] = norm_spacing
        #cases[(ID, 2, 'BL_thick',    1, 'node', '%.3e')] = bl_thickness

        form = [
            ('Geometry', None, geometry_form),
        ]
        if has_tag_data:
            tag_form = []
            form.append(('Tag Data', None, tag_form),)

        results_form = []
        if len(results_form):
            form.append(('Results', None, results_form))
        return form, cases

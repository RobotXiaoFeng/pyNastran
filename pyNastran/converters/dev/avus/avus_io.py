from __future__ import print_function
from six import iteritems
from six.moves import range

import os
from numpy import arange, mean, amax, amin, array

import vtk
from vtk import vtkHexahedron, vtkQuad, vtkTriangle, vtkTetra

from pyNastran.converters.dev.avus.avus_grid import AvusGrid
from pyNastran.gui.gui_objects.gui_result import GuiResult


class AvusIO(object):
    def __init__(self):
        pass

    def get_avus_wildcard_geometry_results_functions(self):
        data = ('Avus',
                'Avus (*.grd)', self.load_avus_geometry,
                None, None)
        return data

    #def removeOldGeometry(self, filename):
        #self._remove_old_cart3d_geometry(filename)

    def load_avus_geometry(self, avus_filename, dirname, name='main', plot=True):
        #key = self.case_keys[self.icase]
        #case = self.result_cases[key]

        skip_reading = self._remove_old_cart3d_geometry(avus_filename)
        if skip_reading:
            return

        model = AvusGrid(log=self.log, debug=False)
        model.read_avus_grid(avus_filename)

        self.model_type = 'avus'
        #self.model_type = model.model_type
        self.nNodes = model.nnodes

        #self._make_tecplot_geometry(model, self.nNodes, quads_only=True) # cart3d
        is_surface = self._make_avus_geometry(model, quads_only=False)

        #self._create_cart3d_free_edegs(model, nodes, elements)


        # loadCart3dResults - regions/loads
        self. turn_text_on()
        self.scalarBar.VisibilityOn()
        self.scalarBar.Modified()

        loads = []
        assert loads is not None
        if 'Mach' in loads:
            avgMach = mean(loads['Mach'])
            note = ':  avg(Mach)=%g' % avgMach
        else:
            note = ''
        self.iSubcaseNameMap = {1: ['Avus%s' % note, '']}
        cases = {}
        ID = 1

        form, cases = self._fill_avus_case(cases, ID, model, is_surface)
        self._finish_results_io2(form, cases)

        if 0:
            # http://www.vtk.org/Wiki/VTK/Examples/Cxx/Filtering/AppendFilter
            points = vtkAppendFilter()
            #if VTK_MAJOR_VERSION <= 5:
                #appendFilter.AddInput(polydata)
                #appendFilter.AddInput(ug)
            #else:
            appendFilter.AddInputData(polydata)
            appendFilter.AddInputData()
            appendFilter.Update()

    def _make_avus_geometry(self, model, quads_only=False):
        nodes = model.nodes
        nnodes = self.nNodes

        points = vtk.vtkPoints()
        points.SetNumberOfPoints(nnodes)
        #self.gridResult.Allocate(self.nNodes, 1000)
        #vectorReselt.SetNumberOfComponents(3)
        #self.nid_map = {}
        #elem.SetNumberOfPoints(nNodes)

        #assert nodes is not None
        #nnodes = nodes.shape[0]

        mmax = amax(nodes, axis=0)
        mmin = amin(nodes, axis=0)
        dim_max = (mmax - mmin).max()
        self.create_global_axes(dim_max)
        for i in range(nnodes):
            points.InsertPoint(i, nodes[i, :])

        #elements = model.elements
        quads = model.quad_elements
        hexas = model.hexa_elements
        tets = model.tet_elements
        tris = model.tri_elements

        is_quads = len(quads)
        is_tris = len(tris)
        is_hexas = len(hexas)
        is_tets = len(tets)

        is_shells = is_quads + is_tris
        is_solids = is_tets + is_hexas
        if is_shells:
            is_surface = True
            if is_quads:
                elements = quads
                for iface, face in enumerate(quads):
                    elem = vtkQuad()
                    epoints = elem.GetPointIds()
                    epoints.SetId(0, face[0])
                    epoints.SetId(1, face[1])
                    epoints.SetId(2, face[2])
                    epoints.SetId(3, face[3])
                    self.grid.InsertNextCell(elem.GetCellType(), elem.GetPointIds())  #elem.GetCellType() = 5  # vtkTriangle
                    #break
            if is_tris:
                elements = tris
                for iface, face in enumerate(tris):
                    elem = vtkTriangle()
                    epoints = elem.GetPointIds()
                    epoints.SetId(0, face[0])
                    epoints.SetId(1, face[1])
                    epoints.SetId(2, face[2])
                    self.grid.InsertNextCell(5, elem.GetPointIds())  #elem.GetCellType() = 5  # vtkTriangle
                    #break

        elif is_solids:
            if is_tets:
                elements = tets
                is_surface = False
                self.nElements = model.nelements
                self.grid.Allocate(self.nElements, 1000)

                nelements = elements.shape[0]
                for eid in range(nelements):
                    elem = vtkTetra()
                    node_ids = elements[eid, :]
                    epoints = elem.GetPointIds()
                    epoints.SetId(0, node_ids[0])
                    epoints.SetId(1, node_ids[1])
                    epoints.SetId(2, node_ids[2])
                    epoints.SetId(3, node_ids[3])
                    self.grid.InsertNextCell(elem.GetCellType(), elem.GetPointIds())  #elem.GetCellType() = 5  # vtkTriangle


            if is_hexas:
                elements = hexas
                is_surface = True
                # is_surface = False
                is_volume = not is_surface

                if is_surface:
                    self.nElements = model.nelements
                    free_faces = array(model.get_free_faces(), dtype='int32')# + 1
                    nfaces = len(free_faces)
                    elements = free_faces
                    self.grid.Allocate(nfaces, 1000)

                    for face in free_faces:
                        elem = vtkQuad()
                        epoints = elem.GetPointIds()
                        epoints.SetId(0, face[0])
                        epoints.SetId(1, face[1])
                        epoints.SetId(2, face[2])
                        epoints.SetId(3, face[3])
                        self.grid.InsertNextCell(elem.GetCellType(), elem.GetPointIds())  #elem.GetCellType() = 5  # vtkTriangle

                elif is_volume:
                    self.nElements = model.nelements
                    self.grid.Allocate(self.nElements, 1000)

                    nelements = elements.shape[0]
                    for eid in range(nelements):
                        elem = vtkHexahedron()
                        node_ids = elements[eid, :]
                        epoints = elem.GetPointIds()
                        epoints.SetId(0, node_ids[0])
                        epoints.SetId(1, node_ids[1])
                        epoints.SetId(2, node_ids[2])
                        epoints.SetId(3, node_ids[3])
                        epoints.SetId(4, node_ids[4])
                        epoints.SetId(5, node_ids[5])
                        epoints.SetId(6, node_ids[6])
                        epoints.SetId(7, node_ids[7])
                        self.grid.InsertNextCell(elem.GetCellType(), elem.GetPointIds())  #elem.GetCellType() = 5  # vtkTriangle
        else:
            raise NotImplementedError()

        self.grid.SetPoints(points)
        #self.grid.GetPointData().SetScalars(self.gridResult)
        #print(dir(self.grid) #.SetNumberOfComponents(0))
        #self.grid.GetCellData().SetNumberOfTuples(1);
        #self.grid.GetCellData().SetScalars(self.gridResult)
        self.grid.Modified()
        if hasattr(self.grid, 'Update'):
            self.grid.Update()
        return is_surface

    def clear_avus(self):
        pass

    #def load_tecplot_results(self, cart3d_filename, dirname):
        #model = Cart3D(log=self.log, debug=False)
        #self.load_cart3d_geometry(cart3d_filename, dirname)

    def _fill_avus_case(self, cases, ID, model, is_surface):
        #'x', 'y', 'z',
        #result_names = ['rho', 'U', 'V', 'W', 'p']
        result_names = []
        # result_names = model.variables[3:]
        #nelements = elements.shape[0]
        nelements = model.nelements
        nnodes = model.nnodes
        #nnodes = nodes.shape[0]


        cases_new = []
        new = False

        #is_results = False
        is_results = True
        results_form = []

        if is_surface:
            element_id = 'FaceID'
        else:
            element_id = 'ElementID'

        geometry_form = [
            ('NodeID', 0, []),
            (element_id, 1, []),
            #('Region', 2, []),
        ]

        eids = arange(1, nelements + 1)
        nids = arange(1, nnodes + 1)

        eid_res = GuiResult(ID, header=element_id, title=element_id,
                            location='centroid', scalar=eids)
        nid_res = GuiResult(ID, header='NodeID', title='NodeID',
                            location='node', scalar=nids)
        icase = 0
        cases[icase] = (eid_res, (itime, element_id))
        cases[icase + 1] = (nid_res, (itime, 'NodeID'))

        #cases[(ID, 2, 'Region', 1, 'centroid', '%i')] = regions

        return geometry_form, cases

        results = model.results
        if is_results and len(results):
            i = 2
            for iresult, result_name in enumerate(result_names):
                if results.shape[1] == 1:
                    nodal_data = results
                    assert len(result_names) == 1, result_names
                else:
                    nodal_data = results[:, iresult]

                if new:
                    cases_new[i] = (result, i, result_name, 1, 'node', '%.3f', '')
                else:
                    cases[(ID, i, result_name, 1, 'node', '%.3f', '')] = nodal_data
                results_form.append((result_name, i, []))
                i += 1
        form = [
            ('Geometry', None, geometry_form),
        ]
        if len(results_form):
            form.append(('Results', None, results_form))
        return form, cases

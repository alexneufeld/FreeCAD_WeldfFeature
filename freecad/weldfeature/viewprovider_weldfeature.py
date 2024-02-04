import os
import math
import FreeCAD
import FreeCADGui
from PySide import QtGui
from freecad.weldfeature import ICONPATH
import pivy.coin as coin
from .gui_utils import get_complementary_shade
from .task_weldfeature import WeldFeatureTaskPanel


class ViewProviderWeldFeature:
    def __init__(self, vobj):
        vobj.addProperty(
            "App::PropertyColor",
            "ShapeColor",
            "ObjectStyle",
            "Object shape color",
        )
        vobj.addProperty(
            "App::PropertyColor",
            "AlternatingColor",
            "ObjectStyle",
            "Object shape alternating color",
        )
        vobj.addProperty(
            "App::PropertyBool",
            "DrawWithAlternatingColors",
            "ObjectStyle",
            "Whether to draw with alternating colors",
        )
        # default to alternating colored weld
        vobj.DrawWithAlternatingColors = True
        vobj.addProperty(
            "App::PropertyBool",
            "AutoSetAlternatingColor",
            "ObjectStyle",
            "Auto-set the alternating color",
        )
        vobj.AutoSetAlternatingColor = True
        vobj.addProperty(
            "App::PropertyEnumeration",
            "EndCapStyle",
            "ObjectStyle",
            "Geometry to include at the ends of weld beads",
        )
        vobj.EndCapStyle = ["Flat", "Rounded", "Pointed"]

        vobj.Proxy = self
        pass

    def attach(self, vobj):
        self._init_scene_graph(vobj)
        vobj.addDisplayMode(self.default_display_group, "Shaded")
        vobj.addDisplayMode(self.wireframe_display_group, "Wireframe")

    def updateData(self, fp, prop):
        weld_position_properties = [
            "Base",
            "PropagateSelection",
            "IntermittentWeld",
            "IntermittentWeldPitch",
            "IntermittentWeldLength",
            "IntermittentWeldOffset",
        ]
        if prop in weld_position_properties:
            # recompute the entire weld bead shape
            self._setup_weld_bead(fp)
        if prop == "WeldSize":
            # disallow really small weld sizes
            new_size = float(fp.WeldSize.getValueAs("mm"))
            self.sphere.radius.setValue(0.99 * new_size)
            self.intermediate_cyl.radius.setValue(new_size)
            self._setup_weld_bead(fp)
        return

    def getDisplayModes(self, obj):
        """
        Return a list of display modes.
        """
        return ["Shaded", "Wireframe"]

    def getDefaultDisplayMode(self):
        return "Shaded"

    def onChanged(self, vp, prop):
        if prop == "EndCapStyle":
            self._adjust_endcaps(vp.Object)
        if prop == "AutoSetAlternatingColor":
            if vp.AutoSetAlternatingColor:
                rgb = vp.ShapeColor[:3]
                alternate_color = (*get_complementary_shade(rgb), 1.0)
                vp.setPropertyStatus("AlternatingColor", "Hidden")
                vp.setPropertyStatus("AlternatingColor", "-ReadOnly")
                vp.AlternatingColor = alternate_color
                vp.setPropertyStatus("AlternatingColor", "ReadOnly")
            else:
                vp.setPropertyStatus("AlternatingColor", "-ReadOnly")
                vp.setPropertyStatus("AlternatingColor", "-Hidden")
        if prop == "DrawWithAlternatingColors":
            if vp.DrawWithAlternatingColors:
                vp.setPropertyStatus("AutoSetAlternatingColor", "-Hidden")
                if vp.AutoSetAlternatingColor:
                    vp.setPropertyStatus("AlternatingColor", "Hidden")
                else:
                    vp.setPropertyStatus("AlternatingColor", "-Hidden")
            else:
                vp.setPropertyStatus("AlternatingColor", "Hidden")
                vp.setPropertyStatus("AutoSetAlternatingColor", "Hidden")
        if prop == "ShapeColor":
            if vp.AutoSetAlternatingColor:
                vp.setPropertyStatus("AlternatingColor", "Hidden")
                rgb = vp.ShapeColor[:3]
                alternate_color = (*get_complementary_shade(rgb), 1.0)
                vp.setPropertyStatus("AlternatingColor", "-ReadOnly")
                vp.AlternatingColor = alternate_color
                vp.setPropertyStatus("AlternatingColor", "ReadOnly")
        if prop in ["ShapeColor", "AlternatingColor", "DrawWithAlternatingColors"]:
            self._set_geom_colors(vp)

    def getIcon(self):
        return os.path.join(ICONPATH, "WeldFeature.svg")

    def setEdit(self, vobj, mode=0):
        taskpanel = WeldFeatureTaskPanel(vobj.Object, False)
        FreeCADGui.Control.showDialog(taskpanel)
        return True

    def unsetEdit(self, vobj, mode=0):
        FreeCADGui.Control.closeDialog()
        return False

    def doubleClicked(self, vobj):
        self.setEdit(vobj)
        return True

    def setupContextMenu(self, vobj, menu):
        action = menu.addAction(
            QtGui.QIcon(os.path.join(ICONPATH, "WeldFeature.svg")), "Edit Weld"
        )
        action.triggered.connect(lambda: self.setEdit(vobj))
        return False

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def _init_scene_graph(self, vobj):
        # create the inventor scene objects
        self.default_display_group = coin.SoSeparator()
        self.wireframe_display_group = coin.SoSeparator()

        self.start_and_end_caps = coin.SoSeparator()
        self.intermediate_spheres = coin.SoSeparator()
        self.main_intermediate_cylinders = coin.SoSeparator()
        self.alt_intermediate_cylinders = coin.SoSeparator()

        self.main_material = coin.SoMaterial()
        self.start_and_end_caps.addChild(self.main_material)
        self.intermediate_spheres.addChild(self.main_material)
        self.main_intermediate_cylinders.addChild(self.main_material)

        self.alt_material = coin.SoMaterial()
        self.alt_intermediate_cylinders.addChild(self.alt_material)

        self.sphere = coin.SoSphere()
        self.intermediate_cyl = coin.SoCylinder()
        # default to 1mm sizes
        self.sphere.radius.setValue(0.99)
        self.intermediate_cyl.radius.setValue(1.0)
        self.intermediate_cyl.height.setValue(1.0)
        self.intermediate_cyl.parts.setValue(coin.SoCylinder.SIDES)

        self.copies_of_spheres = coin.SoMultipleCopy()
        self.copies_of_spheres.addChild(self.sphere)

        self.copies_of_cyls = coin.SoMultipleCopy()
        self.alt_copies_of_cyls = coin.SoMultipleCopy()
        self.copies_of_endcaps = coin.SoMultipleCopy()
        self.copies_of_endcaps.addChild(coin.SoCube())
        self.copies_of_cyls.addChild(self.intermediate_cyl)
        self.alt_copies_of_cyls.addChild(self.intermediate_cyl)
        self.start_and_end_caps.addChild(self.copies_of_endcaps)

        self.main_intermediate_cylinders.addChild(self.copies_of_cyls)
        self.alt_intermediate_cylinders.addChild(self.alt_copies_of_cyls)
        self.intermediate_spheres.addChild(self.copies_of_spheres)

        self.default_display_group.addChild(self.start_and_end_caps)
        self.default_display_group.addChild(self.intermediate_spheres)
        self.default_display_group.addChild(self.main_intermediate_cylinders)
        self.default_display_group.addChild(self.alt_intermediate_cylinders)

    def _set_geom_colors(self, vobj):
        self.main_material.diffuseColor = vobj.ShapeColor[:3]
        if vobj.DrawWithAlternatingColors:
            self.alt_material.diffuseColor = vobj.AlternatingColor[:3]
        else:
            self.alt_material.diffuseColor = vobj.ShapeColor[:3]

    def _adjust_endcaps(self, fp):
        vertex_list = fp.Proxy._vertex_list
        if not vertex_list:
            return
        self.copies_of_endcaps.removeAllChildren()
        cap_size = float(fp.WeldSize.getValueAs("mm"))
        match fp.ViewObject.EndCapStyle:
            case "Flat":
                cap_shape = coin.SoCylinder()
                cap_shape.radius.setValue(cap_size)
                cap_shape.height.setValue(0.0)
                cap_shape.parts.setValue(coin.SoCylinder.TOP)
            case "Rounded":
                cap_shape = coin.SoSphere()
                cap_shape.radius.setValue(cap_size)
            case "Pointed":
                cone = coin.SoCone()
                cone.bottomRadius.setValue(cap_size)
                cone.height.setValue(cap_size)
                cone.parts.setValue(coin.SoCone.SIDES)
                translate = coin.SoTranslation()
                translate.translation.setValue(coin.SbVec3f(0.0, 0.5 * cap_size, 0.0))
                cap_shape = coin.SoSeparator()
                cap_shape.addChild(translate)
                cap_shape.addChild(cone)

        self.copies_of_endcaps.addChild(cap_shape)
        cap_matrix_list = []
        for sublist in vertex_list:
            startcap_base = sublist[0]
            endcap_base = sublist[-1]
            startcap_dir = (startcap_base - sublist[1]).normalize()
            endcap_dir = (endcap_base - sublist[-2]).normalize()
            primitive_axis = FreeCAD.Vector(0.0, 1.0, 0.0)

            startcap_rot_axis = coin.SbVec3f(*primitive_axis.cross(startcap_dir))
            endcap_rot_axis = coin.SbVec3f(*primitive_axis.cross(endcap_dir))
            startcap_rot_angle = math.acos(primitive_axis.dot(startcap_dir))
            endcap_rot_angle = math.acos(primitive_axis.dot(endcap_dir))

            startcap_mat = coin.SbMatrix()
            startcap_mat.setTransform(
                coin.SbVec3f(*startcap_base),  # translation
                coin.SbRotation(startcap_rot_axis, startcap_rot_angle),  # rotation
                coin.SbVec3f(1.0, 1.0, 1.0),  # scale
            )
            endcap_mat = coin.SbMatrix()
            endcap_mat.setTransform(
                coin.SbVec3f(*endcap_base),  # translation
                coin.SbRotation(endcap_rot_axis, endcap_rot_angle),  # rotation
                coin.SbVec3f(1.0, 1.0, 1.0),  # scale
            )
            cap_matrix_list.extend([startcap_mat, endcap_mat])

        endcap_matrices = coin.SoMFMatrix()
        endcap_matrices.setNum(len(cap_matrix_list))
        for i, mat in enumerate(cap_matrix_list):
            endcap_matrices.set1Value(i, mat)
        self.copies_of_endcaps.matrix = endcap_matrices

    def _setup_weld_bead(self, fp):
        superlist_of_vertices = fp.Proxy._vertex_list
        if not superlist_of_vertices:
            return
        sph_mat_list = []
        main_cyl_mat_list = []
        alt_cyl_mat_list = []
        for vertices in superlist_of_vertices:
            for i, vert in enumerate(vertices):
                if (i != 0) and (i != len(vertices) - 1):
                    # don't show the sphere when the next, current, and last points
                    # are nearly colinear
                    x = (vert - vertices[i - 1]).getAngle(
                        vertices[i + 1] - vert
                    ) / math.pi
                    if x > 1e-3:
                        mat = coin.SbMatrix()
                        mat.setTranslate(coin.SbVec3f(*vert))
                        sph_mat_list.append(mat)
                if i != len(vertices) - 1:
                    v2next = vertices[i] - vertices[i + 1]
                    # cylinders are created concentric to the Y-Axis
                    cyl_axis = FreeCAD.Vector(0.0, 1.0, 0.0)
                    cyl_rotation_axis = coin.SbVec3f(*cyl_axis.cross(v2next))
                    cyl_rotation_angle = math.acos(
                        cyl_axis.dot(v2next) / (cyl_axis.Length * v2next.Length)
                    )
                    mat2 = coin.SbMatrix()
                    mat2.setTransform(
                        coin.SbVec3f(*(vert - 0.5 * v2next)),  # translation
                        coin.SbRotation(
                            cyl_rotation_axis, cyl_rotation_angle
                        ),  # rotation
                        coin.SbVec3f(1.0, v2next.Length, 1.0),  # scale
                    )
                    if not i % 2:
                        main_cyl_mat_list.append(mat2)
                    else:
                        alt_cyl_mat_list.append(mat2)

        spheres_matrices = coin.SoMFMatrix()
        spheres_matrices.setNum(len(sph_mat_list))
        for i, mat in enumerate(sph_mat_list):
            spheres_matrices.set1Value(i, mat)
        self.copies_of_spheres.matrix = spheres_matrices

        cyls_main_matrices = coin.SoMFMatrix()
        cyls_main_matrices.setNum(len(main_cyl_mat_list))
        for i, mat in enumerate(main_cyl_mat_list):
            cyls_main_matrices.set1Value(i, mat)
        self.copies_of_cyls.matrix = cyls_main_matrices

        cyls_alt_matrices = coin.SoMFMatrix()
        cyls_alt_matrices.setNum(len(alt_cyl_mat_list))
        for i, mat in enumerate(alt_cyl_mat_list):
            cyls_alt_matrices.set1Value(i, mat)
        self.alt_copies_of_cyls.matrix = cyls_alt_matrices
        # also need to change the endcaps
        self._adjust_endcaps(fp)

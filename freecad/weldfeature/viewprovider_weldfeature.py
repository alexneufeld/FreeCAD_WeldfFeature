import os
import math
import FreeCAD
from freecad.weldfeature import ICONPATH
import pivy.coin as coin


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
        if prop == "Base":
            print("updatedata of viewprovide object")
            # recompute the entire weld bead shape
            self._setup_weld_bead(fp)
        if prop == "WeldSize":
            # disallow really small weld sizes
            new_size = float(fp.WeldSize.getValueAs("mm"))
            self.sphere.radius.setValue(0.99 * new_size)
            self.intermediate_cyl.radius.setValue(new_size)
            self._setup_weld_bead(fp)
        if prop == "IntermittentWeld":
            pass  # TODO
        if prop == "NumberOfWelds":
            pass  # TODO
        if prop == "WeldSpacing":
            pass  # TODO
        if prop == "WeldLength":
            pass  # TODO
        return

    def getDisplayModes(self, obj):
        """
        Return a list of display modes.
        """
        return ["Shaded", "Wireframe"]

    def getDefaultDisplayMode(self):
        return "Shaded"

    def onChanged(self, vp, prop):
        FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")
        if prop in ["ShapeColor", "AlternatingColor", "DrawWithAlternatingColors"]:
            self._set_geom_colors(vp)
        if prop == "EndCapStyle":
            self._adjust_endcaps(vp.Object)

    def getIcon(self):
        return os.path.join(ICONPATH, "WeldFeature.svg")

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
        endcap_matrices = coin.SoMFMatrix()
        endcap_matrices.setNum(2)  # change this if supporting multiple segments
        startcap_base = vertex_list[0]
        endcap_base = vertex_list[-1]
        startcap_dir = (startcap_base - vertex_list[1]).normalize()
        endcap_dir = (endcap_base - vertex_list[-2]).normalize()
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
        endcap_matrices.set1Value(0, startcap_mat)
        endcap_matrices.set1Value(1, endcap_mat)
        self.copies_of_endcaps.matrix = endcap_matrices

    def _setup_weld_bead(self, fp):
        vertices = fp.Proxy._vertex_list
        if not vertices:
            return
        number_of_main_cyls = len(vertices) // 2
        number_of_alt_cyls = len(vertices) - number_of_main_cyls - 1
        cyls_main_matrices = coin.SoMFMatrix()
        cyls_alt_matrices = coin.SoMFMatrix()
        cyls_main_matrices.setNum(number_of_main_cyls)
        cyls_alt_matrices.setNum(number_of_alt_cyls)
        sph_ctr = 0
        main_ctr = 0
        alt_ctr = 0
        sph_mat_list = []
        for i, vert in enumerate(vertices):
            if (i != 0) and (i != len(vertices) - 1):
                # don't show the sphere when the next, current, and last points
                # are nearly colinear
                x = (vert - vertices[i - 1]).getAngle(vertices[i + 1] - vert) / math.pi
                if x > 1e-3:
                    mat = coin.SbMatrix()
                    mat.setTranslate(coin.SbVec3f(*vert))
                    sph_mat_list.append(mat)
                    sph_ctr += 1
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
                    coin.SbRotation(cyl_rotation_axis, cyl_rotation_angle),  # rotation
                    coin.SbVec3f(1.0, v2next.Length, 1.0),  # scale
                )
                if not i % 2:
                    cyls_main_matrices.set1Value(main_ctr, mat2)
                    main_ctr += 1
                else:
                    cyls_alt_matrices.set1Value(alt_ctr, mat2)
                    alt_ctr += 1

        spheres_matrices = coin.SoMFMatrix()
        spheres_matrices.setNum(sph_ctr)
        for i, mat in enumerate(sph_mat_list):
            spheres_matrices.set1Value(i, mat)
        self.copies_of_spheres.matrix = spheres_matrices

        self.copies_of_cyls.matrix = cyls_main_matrices
        self.alt_copies_of_cyls.matrix = cyls_alt_matrices
        # also need to change the endcaps
        self._adjust_endcaps(fp)

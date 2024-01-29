import os
import math
import FreeCAD
from freecad.fcweld import ICONPATH
import pivy.coin as coin
from .geom_utils import discretize_list_of_edges


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
            "Geometry to include at the ends of weld beads"
        )
        vobj.EndCapStyle = [
            "Flat",
            "Rounded",
            "Pointed"
        ]
        # create the inventor scene objects
        self.default_display_group = coin.SoSeparator()
        self.wireframe_display_group = coin.SoSeparator()

        self.start_and_end_caps = coin.SoSeparator()
        self.intermediate_spheres = coin.SoSeparator()
        self.main_intermediate_cylinders = coin.SoSeparator()
        self.alt_intermediate_cylinders = coin.SoSeparator()

        self.main_material = coin.SoMaterial()
        self.main_material.diffuseColor = vobj.ShapeColor[:3]
        self.start_and_end_caps.addChild(self.main_material)
        self.intermediate_spheres.addChild(self.main_material)
        self.main_intermediate_cylinders.addChild(self.main_material)

        self.alt_material = coin.SoMaterial()
        self.alt_material.diffuseColor = vobj.AlternatingColor[:3]
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
        self.copies_of_cyls.addChild(self.intermediate_cyl)
        self.alt_copies_of_cyls.addChild(self.intermediate_cyl)

        self.main_intermediate_cylinders.addChild(self.copies_of_cyls)
        self.alt_intermediate_cylinders.addChild(self.alt_copies_of_cyls)
        self.intermediate_spheres.addChild(self.copies_of_spheres)

        self.default_display_group.addChild(self.start_and_end_caps)
        self.default_display_group.addChild(self.intermediate_spheres)
        self.default_display_group.addChild(self.main_intermediate_cylinders)
        self.default_display_group.addChild(self.alt_intermediate_cylinders)

        # initialize an empty list of vertexes to run the weld bead thru
        self._vertex_list = []

        vobj.Proxy = self
        pass

    def attach(self, vobj):
        vobj.addDisplayMode(self.default_display_group, "Shaded")
        vobj.addDisplayMode(self.wireframe_display_group, "Wireframe")

    def updateData(self, fp, prop):
        # if not self.is_attached:
        #     self.attach(fp.ViewObject)
        #     self.is_attached = True
        if prop == "Base":
            # recompute the entire weld bead shape
            self._recompute_vertices(fp)
            self._setup_weld_bead(f)
        if prop == "WeldSize":
            new_size = float(fp.WeldSize.getValueAs('mm'))
            self.sphere.radius.setValue(0.99 * new_size)
            self.intermediate_cyl.radius.setValue(new_size)
            self._recompute_vertices(fp)
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

    def getDisplayModes(self,obj):
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
            self._adjust_endcaps()

    def getIcon(self):
        return os.path.join(ICONPATH, "WeldFeature.svg")

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def _set_geom_colors(self, vobj):
        self.main_material.diffuseColor = vobj.ShapeColor[:3]
        if vobj.DrawWithAlternatingColors:
            self.alt_material.diffuseColor = vobj.AlternatingColor[:3]
        else:
            self.alt_material.diffuseColor = vobj.ShapeColor[:3]

    def _adjust_endcaps(self):
        if not self._vertex_list:
            return
        startcap_base = self._vertex_list[0]
        endcap_base = self._vertex_list[-1]

    def _recompute_vertices(self, fp):
        """Call this as little as possible to save compute time"""
        geom_selection = fp.Base
        if not geom_selection:
            self._vertex_list = []
            return
        base_object, subelement_names = geom_selection
        list_of_edges = [base_object.getSubObject(name) for name in subelement_names]
        bead_size = float(fp.WeldSize.getValueAs('mm'))
        vertices = discretize_list_of_edges(list_of_edges, bead_size)
        self._vertex_list = vertices

    def _setup_weld_bead(self):
        vertices = self._vertex_list
        if not vertices:
            return
        number_of_spheres = len(vertices)
        spheres_matrices = coin.SoMFMatrix()
        spheres_matrices.setNum(number_of_spheres)

        number_of_cyls = number_of_spheres - 1

        number_of_main_cyls = number_of_spheres // 2
        number_of_alt_cyls = number_of_spheres - number_of_main_cyls - 1
        cyls_main_matrices = coin.SoMFMatrix()
        cyls_alt_matrices = coin.SoMFMatrix()
        cyls_main_matrices.setNum(number_of_main_cyls)
        cyls_alt_matrices.setNum(number_of_alt_cyls)
        main_ctr = 0
        alt_ctr = 0
        for i, vert in enumerate(vertices):
            mat = coin.SbMatrix()
            mat.setTranslate(coin.SbVec3f(*vert))
            spheres_matrices.set1Value(i, mat)

            if (i != len(vertices)-1):
                v2next = (vertices[i] - vertices[i+1])
                # cylinders are created concentric to the Y-Axis
                cyl_axis = FreeCAD.Vector(0.0, 1.0, 0.0)
                cyl_rotation_axis = coin.SbVec3f(*cyl_axis.cross(v2next))
                cyl_rotation_angle = math.acos(
                    cyl_axis.dot(v2next) /
                    (cyl_axis.Length * v2next.Length)
                    )
                mat2 = coin.SbMatrix()
                mat2.setTransform(
                    coin.SbVec3f(*(vert -0.5 * v2next)),  # translation
                    coin.SbRotation(cyl_rotation_axis, cyl_rotation_angle),  # rotation
                    coin.SbVec3f(1.0, v2next.Length, 1.0)  # scale
                )
                if not i % 2:
                    cyls_main_matrices.set1Value(main_ctr, mat2)
                    main_ctr += 1
                else:
                    cyls_alt_matrices.set1Value(alt_ctr, mat2)
                    alt_ctr += 1
        self.copies_of_spheres.matrix = spheres_matrices
        self.copies_of_cyls.matrix = cyls_main_matrices
        self.alt_copies_of_cyls.matrix = cyls_alt_matrices

    def setup_weld_bead(self, fp):
        geom_selection = fp.Base
        bead_size = float(fp.WeldSize.getValueAs('mm'))

        self.spheres.removeAllChildren()
        self.odd_colored_cylinderes.removeAllChildren()
        self.even_colored_cylinderes.removeAllChildren()

        light = coin.SoDirectionalLight()
        mat1 = coin.SoMaterial()
        mat1.diffuseColor = fp.ViewObject.ShapeColor[:3]

        mat2 = coin.SoMaterial()
        mat2.diffuseColor = fp.ViewObject.AlternatingColor[:3]

        # self.spheres.addChild(mat1)

        if not geom_selection:
            return
        base_object, subelement_names = geom_selection
        list_of_edges = [base_object.getSubObject(name) for name in subelement_names]
        vertices = discretize_list_of_edges(list_of_edges, bead_size)
        for i, vert in enumerate(vertices):
            if (i != 0 and) (i != len(vertices)-1)
            # add a sphere
            sphere_translate = coin.SoTranslation()
            sphere_translate.translation.setValue(coin.SbVec3f(*vert))
            sphere = coin.SoSphere()
            sphere.radius.setValue(bead_size*0.99)
            sep = coin.SoSeparator()
            # sep.addChild(light)
            sep.addChild(mat1)
            sep.addChild(sphere_translate)
            sep.addChild(sphere)
            self.spheres.addChild(sep)

            if (i != len(vertices)-1):
                v2next = (vertices[i] - vertices[i+1])
                cyl = coin.SoCylinder()
                cyl.radius.setValue(bead_size)
                cyl.height.setValue(v2next.Length)
                cyl.parts.setValue(coin.SoCylinder.SIDES)

                cyl_transform = coin.SoTransform()
                cyl_transform.translation.setValue(*(vert -0.5 * v2next))
                cyl_axis = FreeCAD.Vector(0.0, 1.0, 0.0)
                cyl_transform.rotation.setValue(
                    coin.SbVec3f(*cyl_axis.cross(v2next)),
                    math.acos(cyl_axis.dot(v2next) / (cyl_axis.Length * v2next.Length))
                )

                sep = coin.SoSeparator()
                # sep.addChild(light)
                if i % 2:
                    sep.addChild(mat1)
                else:
                    sep.addChild(mat2)
                sep.addChild(cyl_transform)
                sep.addChild(cyl)

                if i % 2:
                    self.odd_colored_cylinderes.addChild(sep)
                else:
                    self.even_colored_cylinderes.addChild(sep)



import os
import math
import FreeCAD
from freecad.fcweld import ICONPATH
import pivy.coin as coin
from .geom_utils import discretize_list_of_edges


class ViewProviderWeldFeature:

    is_attached = False

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
        vobj.Proxy = self
        pass

    def attach(self, vobj):
        # setup the default shaded display mode
        self.default_display_group = coin.SoSeparator()
        #
        # self.material = coin.SoMaterial()
        # self.default_display_group.addChild(coin.SoDirectionalLight())
        # self.material.diffuseColor = (1.0, 0.0, 0.0)   # Red
        # self.default_display_group.addChild(self.material)

        self.spheres = coin.SoSeparator()
        self.odd_colored_cylinderes = coin.SoSeparator()
        self.even_colored_cylinderes = coin.SoSeparator()

        self.default_display_group.addChild(self.spheres)
        self.default_display_group.addChild(self.odd_colored_cylinderes)
        self.default_display_group.addChild(self.even_colored_cylinderes)

        # setup the wireframe display mode
        self.wireframe_display_group = coin.SoSeparator()

        vobj.addDisplayMode(self.default_display_group, "Shaded")
        vobj.addDisplayMode(self.wireframe_display_group, "Wireframe")

    def updateData(self, fp, prop):
        """
        If a property of the handled feature has changed we have the chance to handle this here
        """
        if not self.is_attached:
            self.attach(fp.ViewObject)
            self.is_attached = True
        if prop == "Base" or prop == "WeldSize":
            pass
        self.setup_weld_bead(fp)
        return

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

    def getDisplayModes(self,obj):
        """
        Return a list of display modes.
        """
        return ["Shaded", "Wireframe"]

    def getDefaultDisplayMode(self):
        """
        Return the name of the default display mode. It must be defined in getDisplayModes.
        """
        return "Shaded"

    def setDisplayMode(self,mode):
        """
        Map the display mode defined in attach with those defined in getDisplayModes.
        Since they have the same names nothing needs to be done.
        This method is optional.
        """
        return mode

    def onChanged(self, vp, prop):
        """
        Print the name of the property that has changed
        """

        FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")
        self.setup_weld_bead(vp.Object)

    def getIcon(self):
        return os.path.join(ICONPATH, "WeldFeature.svg")

    def __getstate__(self):
        """
        Called during document saving.
        """
        return None

    def __setstate__(self,state):
        """
        Called during document restore.
        """
        return None

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
        # set some basic properties of the default display mode
        # self.shape_hints = coin.SoShapeHints()
        # # vertexOrdering == CLOCKWISE or COUNTERCLOCKWISE, shapeType == SOLID:
        # # causes primitives to be backface culled and rendered with one-sided lighting.
        # self.shape_hints.vertexOrdering = coin.SoShapeHints.COUNTERCLOCKWISE
        # self.shape_hints.shapeType = coin.SoShapeHints.SOLID
        # self.shape_hints.creaseAngle = 0.0 # math.pi*1.1
        # self.default_display_group.addChild(self.shape_hints)
        #
        # self.material = coin.SoMaterial()
        # self.default_display_group.addChild(coin.SoDirectionalLight())
        # self.material.diffuseColor = (1.0, 0.0, 0.0)   # Red
        # self.default_display_group.addChild(self.material)

        # setup shaders
        shaderpath = os.path.dirname(os.path.abspath(__file__))
        self.shader_program = coin.SoShaderProgram()

        self.vertex_shader = coin.SoVertexShader()
        self.vertex_shader.sourceProgram.setValue(os.path.join(shaderpath, 'weldbead_vertex_shader.glsl'))

        self.fragment_shader = coin.SoFragmentShader()
        self.fragment_shader.sourceProgram.setValue(os.path.join(shaderpath, 'weldbead_fragment_shader.glsl'))

        self.shader_program.shaderObject.set1Value(0, self.vertex_shader)
        self.shader_program.shaderObject.set1Value(1, self.fragment_shader)
        self.default_display_group.addChild(self.shader_program)

        self.extrusion = coin.SoVRMLExtrusion()
        self.default_display_group.addChild(self.extrusion)
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
        if prop == "Base":
            self.create_extrusion(fp.Base, float(fp.WeldSize.getValueAs('mm')))
        if prop == "WeldSize":
            # rescale the weld bead
            beadsize = float(fp.WeldSize.getValueAs('mm'))
            self.extrusion.scale.setNum(1)
            self.extrusion.scale.set1Value(0, coin.SbVec2f(beadsize, beadsize))
        return

    def setup_weld_bead(self, geom_selection, bead_size):
        if not geom_selection:
            return
        base_object, subelement_names = geom_selection
        list_of_edges = [base_object.getSubObject(name) for name in subelement_names]
        print(list_of_edges)
        vertices = discretize_list_of_edges(list_of_edges)
        print(vertices)
        array = coin.SoMultipleCopy()
        scale = coin.SoScale()
        scale.scaleFactor.setValue(bead_size, bead_size, bead_size)
        array.addChild(scale)
        array.addChild(coin.SoSphere())
        matrices = coin.SoMFMatrix()
        matrices.setNum(len(vertices))
        for i, vec in enumerate(vertices):
            matrix = coin.SbMatrix()
            matrix.setTranslate(coin.SbVec3f(*vec))
            matrices.set1Value(i, matrix)
        array.matrix = matrices
        self.default_display_group.replaceChild(0, array)

    def create_extrusion(self, geom_selection, beadsize):
        if not geom_selection:
            # if no geometry is set as a base object, don't render anythin
            self.extrusion.crossSection.setNum(0)
            self.extrusion.spine.setNum(0)
            return
        base_object, subelement_names = geom_selection
        list_of_edges = [base_object.getSubObject(name) for name in subelement_names]
        vertices = discretize_list_of_edges(list_of_edges)

        # create the profile as closed circle
        fn = 30
        self.extrusion.crossSection.setNum(fn + 1)
        for i in range(fn):
            theta = 2*math.pi * i / fn
            x  = math.cos(theta)
            # invert theta here to avoid flipped normals
            z  = math.sin(-1*theta)
            if abs(x) < 1e-5:
                x = 0
            if abs(z) < 1e-5:
                z = 0
            if i == 0:
                x = 1.0
                z = 0.0
            self.extrusion.crossSection.set1Value(i, coin.SbVec2f(x, z))
        self.extrusion.crossSection.set1Value(fn, coin.SbVec2f(1.0 , 0.0))
        # set the scale of teh weld bead.
        # If only a single value is specified for the scale parameters,
        # it will be used at all points of the sweep path
        self.extrusion.scale.setNum(1)
        self.extrusion.scale.set1Value(0, coin.SbVec2f(beadsize, beadsize))
        # define the sweep path
        self.extrusion.spine.setNum(len(vertices))
        for i, vec in enumerate(vertices):
            self.extrusion.spine.set1Value(i, coin.SbVec3f(*vec))

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

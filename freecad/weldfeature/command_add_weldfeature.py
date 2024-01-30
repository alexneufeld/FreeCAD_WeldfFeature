import os
import FreeCAD
import FreeCADGui
from freecad.weldfeature import ICONPATH
from .weldfeature import WeldFeature
from .viewprovider_weldfeature import ViewProviderWeldFeature
from .gui_utils import parse_and_clean_selection
from .gui_utils import set_default_values
from .gui_utils import get_best_default_object_colors

class AddWeldFeatureCommand:

    DEFAULT_OBJECT_VALUES = {
        "WeldSize": FreeCAD.Units.Quantity("4 mm"),
        "IntermittentWeld": False,
        "NumberOfIntermittentWelds": 2,
        "IntermittentWeldSpacing": FreeCAD.Units.Quantity("50 mm"),
        "IntermittentWeldLength": "15 mm",
        "FieldWeld": False,
        "AlternatingWeld": False,
        "AllAround": False,
    }

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "WeldFeature.svg"),
            "Menutext": "AddWeldFeatureCommand",
            "tooltip": "Add a weld bead to the assembly"
        }

    def Activated(self):

        doc = FreeCAD.ActiveDocument
        selection = parse_and_clean_selection()
        if len(selection) != 1:
            FreeCAD.Console.PrintUserError(
                "Select geometry from a single object.\n"
            )
            return
        obj = doc.addObject("App::FeaturePython", "WeldBead")
        WeldFeature(obj)
        set_default_values(obj, self.DEFAULT_OBJECT_VALUES)
        ViewProviderWeldFeature(obj.ViewObject)
        # assign the selected reference geometry
        obj.Base = selection[0]
        # place the weld object in the tree view so that it is in the same geofeature
        # group as the referenced geometry.
        group = obj.Base[0].getParentGeoFeatureGroup()
        if group:  # getParentGeoFeatureGroup returns None for ungrouped objects
            group.addObject(obj)
        # assign nice object colors
        base_color, alternate_color = get_best_default_object_colors(obj.Base[0])
        obj.ViewObject.ShapeColor = base_color
        obj.ViewObject.AlternatingColor = alternate_color

    def IsActive(self):
        return FreeCADGui.ActiveDocument is not None

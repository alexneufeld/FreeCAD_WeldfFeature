import os
import FreeCAD
import FreeCADGui
from freecad.weldfeature import ICONPATH
from .weldfeature import WeldFeature
from .viewprovider_weldfeature import ViewProviderWeldFeature
from .gui_utils import parse_and_clean_selection
from .gui_utils import set_default_values
from .gui_utils import get_best_default_object_colors
from .task_weldfeature import WeldFeatureTaskPanel


class AddWeldFeatureCommand:
    DEFAULT_OBJECT_VALUES = {
        "PropagateSelection": False,
        "WeldSize": FreeCAD.Units.Quantity("4 mm"),
        "IntermittentWeld": False,
        "IntermittentWeldPitch": FreeCAD.Units.Quantity("50 mm"),
        "IntermittentWeldLength": "15 mm",
        "FieldWeld": False,
        "AlternatingWeld": False,
        "AllAround": False,
    }

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "WeldFeature.svg"),
            "Menutext": "AddWeldFeatureCommand",
            "tooltip": "Add a weld bead to the assembly",
        }

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        selection = parse_and_clean_selection()
        if not selection:
            # create nothing if no usable selections were returned
            return
        obj = doc.addObject("App::FeaturePython", "WeldBead")
        WeldFeature(obj)
        set_default_values(obj, self.DEFAULT_OBJECT_VALUES)
        ViewProviderWeldFeature(obj.ViewObject)
        # assign the selected reference geometry
        obj.Base = selection
        # place the weld object in the tree view so that it is in the same geofeature
        # group as the referenced geometry. Note that issues may occur if multiple
        # base objects in different geofeature groups are selected...
        group = obj.Base[0][0].getParentGeoFeatureGroup()
        if group:  # getParentGeoFeatureGroup returns None for ungrouped objects
            group.addObject(obj)
        # assign nice object colors, based on the first selected object
        base_color, alternate_color = get_best_default_object_colors(obj.Base[0][0])
        obj.ViewObject.ShapeColor = base_color
        obj.ViewObject.AlternatingColor = alternate_color
        # show the objects task panel
        taskpanel = WeldFeatureTaskPanel(obj, True)
        FreeCADGui.Control.showDialog(taskpanel)

    def IsActive(self):
        return FreeCADGui.ActiveDocument is not None

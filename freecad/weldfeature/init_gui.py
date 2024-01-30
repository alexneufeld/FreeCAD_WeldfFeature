import os
import FreeCADGui
from TranslateUtils import translate
from freecad.fcweld import ICONPATH, TRANSLATIONSPATH


class WeldWorkbench(FreeCADGui.Workbench):
    """
    class which gets initiated at startup of the gui
    """
    MenuText = translate("Weld Bead", "Weld Bead")
    ToolTip = translate("Weld Bead", "Add weld beads to an assembly")
    Icon = os.path.join(ICONPATH, "WeldFeature.svg")
    toolbox = []

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        This function is called at the first activation of the workbench.
        here is the place to import all the commands
        """
        # Add translations path
        FreeCADGui.addLanguagePath(TRANSLATIONSPATH)
        FreeCADGui.updateLocale()
        from freecad.fcweld.command_add_weldfeature import AddWeldFeatureCommand
        FreeCADGui.addCommand("Weld_AddWeldFeature", AddWeldFeatureCommand())
        self.appendMenu(
            "WeldFeature",
            [
                "Weld_AddWeldFeature",
            ],
        )
        self.appendToolbar(
            "WeldFeature",
            [
                "Weld_AddWeldFeature",
            ],
        )

    def Activated(self):
        '''
        code which should be computed when a user switch to this workbench
        '''

        pass

    def Deactivated(self):
        '''
        code which should be computed when this workbench is deactivated
        '''
        pass


FreeCADGui.addWorkbench(WeldWorkbench())

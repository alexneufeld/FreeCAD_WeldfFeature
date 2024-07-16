import os
# import __main__
import FreeCADGui
from freecad.weldfeature.command_add_weldfeature import AddWeldFeatureCommand

#
# def toolbar_manipulation(name):
#     import FreeCAD
#
#     FreeCAD.Console.PrintLog(f"workbench name: {name}\n")
#     if name == "AssemblyWorkbench":
#         from freecad.weldfeature import ICONPATH
#         import os
#         import FreeCADGui
#
#         mw = FreeCADGui.getMainWindow()
#         from PySide import QtWidgets, QtGui
#
#         my_tool_button = QtWidgets.QToolButton()
#         my_tool_button.setIcon(QtGui.QIcon(os.path.join(ICONPATH, "WeldFeature.svg")))
#         my_tool_button.clicked.connect(lambda: FreeCADGui.runCommand("WeldFeature_Add"))
#         my_tool_bar = QtWidgets.QToolBar("Assembly Features")
#         my_tool_bar.addWidget(my_tool_button)
#         mw.addToolBar(my_tool_bar)
#
#
# # The following 2 lines are important because InitGui.py files are passed to the exec() function...
# # ...and the runMacro wouldn't be visible outside. So explicitly add it to __main__
# __main__.toolbar_manipulation = toolbar_manipulation
#
# # Connect the function that runs the macro to the appropriate signal
# FreeCADGui.getMainWindow().workbenchActivated.connect(toolbar_manipulation)

# Add the GUI command
FreeCADGui.addCommand("WeldFeature_Add", AddWeldFeatureCommand())


# This shouldn't need an entire workbench
class WeldWorkbench(FreeCADGui.Workbench):
    from freecad.weldfeature import ICONPATH, TRANSLATIONSPATH
    from freecad.weldfeature.TranslateUtils import translate

    MenuText = translate("Weld Bead", "Weld Bead")
    ToolTip = translate("Weld Bead", "Add weld beads to an assembly")
    Icon = os.path.join(ICONPATH, "WeldFeature.svg")
    toolbox = []

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        from freecad.weldfeature import TRANSLATIONSPATH

        FreeCADGui.addLanguagePath(TRANSLATIONSPATH)
        FreeCADGui.updateLocale()
        self.appendMenu(
            "WeldFeature",
            [
                "WeldFeature_Add",
            ],
        )
        self.appendToolbar(
            "WeldFeature",
            [
                "WeldFeature_Add",
            ],
        )

    def Activated(self):
        pass

    def Deactivated(self):
        pass


FreeCADGui.addWorkbench(WeldWorkbench())

import __main__
import FreeCADGui
from freecad.weldfeature.command_add_weldfeature import AddWeldFeatureCommand


def toolbar_manipulation(name):
    import FreeCAD

    FreeCAD.Console.PrintLog(f"workbench name: {name}\n")
    if name == "AssemblyWorkbench":
        from freecad.weldfeature import ICONPATH
        import os
        import FreeCADGui

        mw = FreeCADGui.getMainWindow()
        from PySide import QtWidgets, QtGui

        my_tool_button = QtWidgets.QToolButton()
        my_tool_button.setIcon(QtGui.QIcon(os.path.join(ICONPATH, "WeldFeature.svg")))
        my_tool_button.clicked.connect(lambda: FreeCADGui.runCommand("WeldFeature_Add"))
        my_tool_bar = QtWidgets.QToolBar("Assembly Features")
        my_tool_bar.addWidget(my_tool_button)
        mw.addToolBar(my_tool_bar)


# The following 2 lines are important because InitGui.py files are passed to the exec() function...
# ...and the runMacro wouldn't be visible outside. So explicitly add it to __main__
__main__.toolbar_manipulation = toolbar_manipulation

# Connect the function that runs the macro to the appropriate signal
FreeCADGui.getMainWindow().workbenchActivated.connect(toolbar_manipulation)

# Add the GUI command
FreeCADGui.addCommand("WeldFeature_Add", AddWeldFeatureCommand())

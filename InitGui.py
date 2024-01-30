import FreeCADGui
import __main__


def run_on_startup(name):
    # Do not run when NoneWorkbench is activated because UI isn't yet completely initialized
    import FreeCAD
    FreeCAD.Console.PrintLog(f"workbench name: {name}\n")
    if name == "AssemblyWorkbench":
        # Run macro only once by disconnecting the signal at first call
        from freecad.weldfeature import ICONPATH
        import os
        import FreeCADGui
        mw = FreeCADGui.getMainWindow()
        # mw.workbenchActivated.disconnect(run_on_startup)
        from freecad.weldfeature.command_add_weldfeature import AddWeldFeatureCommand
        FreeCADGui.addCommand("WeldFeature_Add", AddWeldFeatureCommand())
        # find the assembly toolbar
        from PySide import QtWidgets, QtGui
        toolbars = [x for x in mw.children() if isinstance(x, QtWidgets.QToolBar)]
        assembly_toolbar = [x for x in toolbars if x.objectName() == "Assembly Joints"][0]
        # assembly_toolbar = [x for x in toolbars if x.objectName() == "Assembly"][0]
        # create a toolbutton
        my_tool_button = QtWidgets.QToolButton()
        my_tool_button.setIcon(QtGui.QIcon(os.path.join(ICONPATH, "WeldFeature.svg")))
        my_tool_button.clicked.connect(lambda: FreeCADGui.runCommand("WeldFeature_Add"))
        my_tool_bar = QtWidgets.QToolBar("Assembly Features")
        # assembly_toolbar.addWidget(my_tool_button)
        my_tool_bar.addWidget(my_tool_button)
        mw.addToolBar(my_tool_bar)
        # mw.insertToolBar(assembly_toolbar, my_tool_bar)
        # print(f"{assembly_toolbar.children()=}")
        # manip = Manipulator()
        # FreeCADGui.addWorkbenchManipulator(manip)
        # wb = FreeCADGui.activeWorkbench()
        # wb.reloadActive()
        print("did the thing")


# The following 2 lines are important because InitGui.py files are passed to the exec() function...
# ...and the runMacro wouldn't be visible outside. So explicitly add it to __main__
__main__.run_on_startup = run_on_startup

# Connect the function that runs the macro to the appropriate signal
FreeCADGui.getMainWindow().workbenchActivated.connect(run_on_startup)
print("finished executing the welding init gui file")


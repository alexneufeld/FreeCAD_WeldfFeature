import os
import FreeCAD
import FreeCADGui
from PySide import QtCore
from PySide import QtGui
from PySide import QtWidgets
from freecad.weldfeature import ICONPATH


def get_unit_for_comboboxes(doc: FreeCAD.Document) -> str:
    """Translate a FreeCAD document's unit system into a good length unit to
    use in UI combo-boxes"""
    # only very recent versions of FreeCAD have a per-document unit system
    if hasattr(doc, "UnitSystem"):
        unit_system_description = doc.UnitSystem
    else:
        list_of_schemas = FreeCAD.Units.listSchemas()
        unit_system_description = list_of_schemas[FreeCAD.Units.getSchema()]
    schema_to_useful_length_unit = {
        "Standard (mm, kg, s, degree)": "mm",
        "MKS (m, kg, s, degree)": "mm",
        "US customary (in, lb)": "mm",
        "Imperial decimal (in, lb)": "in",
        "Building Euro (cm, m², m³)": "cm",
        "Building US (ft-in, sqft, cft)": "in",
        "Metric small parts & CNC(mm, mm/min)": "mm",
        "Imperial for Civil Eng (ft, ft/sec)": "ft",
        "FEM (mm, N, s)": "mm",
        "Meter decimal (m, m², m³)": "m",
    }
    return schema_to_useful_length_unit[unit_system_description]


class selectionFilter(QtCore.QObject):
    ALLOWED_TYPES = ("Edge", "Face")

    selection = QtCore.Signal(str)

    def __init__(self):
        super().__init__()

    def addSelection(self, doc, obj, sub, pnt):
        print(f"{doc=}, {obj=}, {sub=}, {pnt=}")
        if sub.rstrip("0123456789") in self.ALLOWED_TYPES:
            print("allowed")
            self.selection.emit(sub)


class WeldFeatureTaskPanel:
    def __init__(self, feature, isNewFeature):
        self.feature = feature
        self.isNewFeature = isNewFeature
        self.doc = FreeCAD.ActiveDocument
        self.guidoc = FreeCADGui.ActiveDocument
        uiPath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "TaskWeldFeatureParameters.ui"
        )
        loader = FreeCADGui.UiLoader()
        self.form = loader.load(uiPath)
        self.setupUI()
        self.doc.openTransaction("Edit WeldFeature")
        # set up selection behaviour changes
        FreeCADGui.Selection.clearSelection()
        self.selectionObserver = selectionFilter()
        FreeCADGui.Selection.addObserver(self.selectionObserver)
        self.selectionObserver.selection.connect(self.addReference)

    def setupUI(self):
        # set window title and icon
        self.form.setWindowTitle("Weld Parameters")
        self.form.setWindowIcon(QtGui.QIcon(os.path.join(ICONPATH, "WeldFeature.svg")))

        # initialize UI fields to feature parameter values
        lu = get_unit_for_comboboxes(self.doc)

        self.form.weldSize.setProperty("unit", lu)
        self.form.weldSize.setProperty(
            "rawValue", float(self.feature.WeldSize.getValueAs(lu))
        )
        self.form.intermittentWeldLength.setProperty("unit", lu)
        self.form.intermittentWeldLength.setProperty(
            "rawValue", float(self.feature.IntermittentWeldLength.getValueAs(lu))
        )
        self.form.intermittentWeldPitch.setProperty("unit", lu)
        self.form.intermittentWeldPitch.setProperty(
            "rawValue", float(self.feature.IntermittentWeldPitch.getValueAs(lu))
        )
        self.form.intermittentWeldOffset.setProperty("unit", lu)
        self.form.intermittentWeldOffset.setProperty(
            "rawValue", float(self.feature.IntermittentWeldOffset.getValueAs(lu))
        )

        # populate list of geometry references
        for selitem in self.feature.Base:
            for subel in selitem[1]:
                self.form.listWidgetReferences.addItem(f"{selitem[0].Name}.{subel}")

        # delete list items via a context menu
        deleteAction = QtWidgets.QAction("Remove", self.form)
        deleteAction.setShortcuts(QtGui.QKeySequence.Delete)
        deleteAction.triggered.connect(self.removeReference)
        # note that the list widgets action policy must be 'ActionsContextMenu'
        # this can be done in QtDesigner
        self.form.listWidgetReferences.addAction(deleteAction)

        self.form.checkBoxPropagateSelection.setChecked(self.feature.PropagateSelection)
        self.form.checkBoxIntermittentWeld.setChecked(self.feature.IntermittentWeld)
        self.form.checkBoxAllAround.setChecked(self.feature.AllAround)
        self.form.checkBoxAlternatingWeld.setChecked(self.feature.AlternatingWeld)
        self.form.checkBoxFieldWeld.setChecked(self.feature.FieldWeld)

        # connect expression bindings
        FreeCADGui.ExpressionBinding(self.form.weldSize).bind(self.feature, "WeldSize")
        FreeCADGui.ExpressionBinding(self.form.intermittentWeldLength).bind(
            self.feature, "IntermittentWeldLength"
        )
        FreeCADGui.ExpressionBinding(self.form.intermittentWeldPitch).bind(
            self.feature, "IntermittentWeldPitch"
        )
        FreeCADGui.ExpressionBinding(self.form.intermittentWeldOffset).bind(
            self.feature, "IntermittentWeldOffset"
        )

        # connect signals and slots
        self.form.checkBoxPropagateSelection.toggled.connect(
            self.changeCheckBoxPropagateSelection
        )
        self.form.checkBoxIntermittentWeld.toggled.connect(
            self.changeCheckBoxIntermittentWeld
        )
        self.form.checkBoxAllAround.toggled.connect(self.changeCheckBoxAllAround)
        self.form.checkBoxAlternatingWeld.toggled.connect(
            self.changeCheckBoxAlternatingWeld
        )
        self.form.checkBoxFieldWeld.toggled.connect(self.changeCheckBoxFieldWeld)

        self.form.weldSize.valueChanged.connect(self.changeWeldSize)
        self.form.intermittentWeldLength.valueChanged.connect(
            self.changeIntermittentWeldLength
        )
        self.form.intermittentWeldPitch.valueChanged.connect(
            self.changeIntermittentWeldPitch
        )
        self.form.intermittentWeldOffset.valueChanged.connect(
            self.changeIntermittentWeldOffset
        )

        self.updateUI()

    def changeCheckBoxPropagateSelection(self, checked):
        self.feature.PropagateSelection = checked
        self.updateUI()

    def changeCheckBoxIntermittentWeld(self, checked):
        self.feature.IntermittentWeld = checked
        self.updateUI()

    def changeCheckBoxAllAround(self, checked):
        self.feature.AllAround = checked
        self.updateUI()

    def changeCheckBoxAlternatingWeld(self, checked):
        self.feature.AlternatingWeld = checked
        self.updateUI()

    def changeCheckBoxFieldWeld(self, checked):
        self.feature.FieldWeld = checked
        self.updateUI()

    def changeWeldSize(self, val):
        self.feature.WeldSize = val
        self.updateUI()

    def changeIntermittentWeldLength(self, val):
        self.feature.IntermittentWeldLength = val
        self.updateUI()

    def changeIntermittentWeldPitch(self, val):
        self.feature.IntermittentWeldPitch = val
        self.updateUI()

    def changeIntermittentWeldOffset(self, val):
        self.feature.IntermittentWeldOffset = val
        self.updateUI()

    def updateUI(self):
        # enable/disable UI fields based on object state
        self.form.intermittentWeldLength.setEnabled(self.feature.IntermittentWeld)
        self.form.intermittentWeldPitch.setEnabled(self.feature.IntermittentWeld)
        self.form.intermittentWeldOffset.setEnabled(self.feature.IntermittentWeld)

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)

    def accept(self):
        self.doc.commitTransaction()
        self.guidoc.resetEdit()
        FreeCADGui.Control.closeDialog()
        self.doc.recompute()
        FreeCADGui.Selection.removeObserver(self.selectionObserver)

    def reject(self):
        self.doc.abortTransaction()
        FreeCADGui.Control.closeDialog()
        # delete the object if it was just created
        if self.isNewFeature:
            self.doc.removeObject(self.feature.Name)
        self.doc.recompute()
        FreeCADGui.Selection.removeObserver(self.selectionObserver)

    def focusUiStart(self):
        start_widget = self.form.weldSize
        start_widget.setFocus()
        start_widget.selectAll()

    def removeReference(self):
        print("removing reference")
        # deletedRef = self.form.listWidgetReferences.takeItem(
        #     self.form.listWidgetReferences.currentIndex().row()
        # ).text()
        # newList = list(self.feature.baseObject[1])
        # print(deletedRef)
        # print(newList)
        # newList.remove(deletedRef)
        # self.feature.baseObject = (self.feature.baseObject[0], newList)
        self.updateUI()

    def addReference(self, text):
        print(f"adding reference: {text}")
        # if text not in self.feature.baseObject[1]:
        #     newList = list(self.feature.baseObject[1])
        #     newList.append(text)
        #     self.feature.baseObject = (self.feature.baseObject[0], newList)
        #     self.form.listWidgetReferences.addItem(text)
        #     self.updateUI()

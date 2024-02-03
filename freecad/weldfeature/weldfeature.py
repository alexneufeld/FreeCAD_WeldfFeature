from itertools import starmap
import FreeCAD
import Part
from .geom_utils import discretize_list_of_edges
from .geom_utils import discretize_intermittent
from .tangent_edges import expand_selection_to_geometry


class WeldFeature:
    def __init__(self, obj):
        obj.Proxy = self
        # add_property(type, name, section, description)
        # supported properties
        obj.addProperty(
            "App::PropertyXLinkSubList",
            "Base",
            "Base",
            "Reference geometry for the weld bead. "
            "Multiple faces or edges may be selected",
        )
        obj.addProperty(
            "App::PropertyBool",
            "PropagateSelection",
            "Base",
            "Whether to weld along any edges tangent to selected edges",
        )
        obj.addProperty(
            "App::PropertyLength", "WeldSize", "Weld", "Size of the weld bead"
        )
        # set this immediately to avoid ever recomputing with a non-usable value
        obj.WeldSize = FreeCAD.Units.Quantity("4.0 mm")
        # properties for intermittent welds
        obj.addProperty(
            "App::PropertyBool",
            "IntermittentWeld",
            "Weld",
            "Whether to model an intermittent or continuous weld",
        )
        obj.addProperty(
            "App::PropertyLength",
            "IntermittentWeldPitch",
            "Weld",
            "Pitch of intermittent welds",
        )
        obj.addProperty(
            "App::PropertyLength",
            "IntermittentWeldLength",
            "Weld",
            "Length of individual welds in an intermittent weld",
        )
        obj.addProperty(
            "App::PropertyLength",
            "IntermittentWeldOffset",
            "Weld",
            "Offset of the start of the intermittent weld pattern "
            "from the start of selected edges",
        )
        # Informational properties - There have no effect on the generated geometry,
        # but they can be used to track metadata that could be linked to drawings.
        obj.addProperty(
            "App::PropertyBool",
            "FieldWeld",
            "WeldInformation",
            "Whether this weld should be completed in the field",
        )
        obj.addProperty(
            "App::PropertyBool",
            "AlternatingWeld",
            "WeldInformation",
            "Whether this weld alternates on either side of the selected shape",
        )
        obj.addProperty(
            "App::PropertyBool",
            "AllAround",
            "WeldInformation",
            "Whether this weld wrap all the way around the selected shape",
        )
        obj.addProperty(
            "App::PropertyLength",
            "WeldLength",
            "WeldInformation",
            "Computed Length of weld material in this weld object",
        )
        obj.setPropertyStatus("WeldLength", "ReadOnly")

        self._vertex_list = []

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop: str):
        non_informational_properties = [
            "Base",
            "PropagateSelection",
            "WeldSize",
            "IntermittentWeld",
            "IntermittentWeldPitch",
            "IntermittentWeldLength",
            "IntermittentWeldOffset",
        ]
        if prop in non_informational_properties:
            self._recompute_vertices(obj)
        if prop == "IntermittentWeld":
            # when not using an intermittent weld,
            # hide visibility of associated properties
            dependant_properties = [
                "IntermittentWeldPitch",
                "IntermittentWeldLength",
                "IntermittentWeldOffset",
            ]
            for property_name in dependant_properties:
                # prepend a '-' (E.G.: "-Hidden") to clear the status bit
                obj.setPropertyStatus(
                    property_name, "-" * int(obj.IntermittentWeld) + "Hidden"
                )

    def dumps(self):
        return {
            "_vertex_list": [
                [tuple(x) for x in sublist] for sublist in self._vertex_list
            ],
            "_weld_length": self._weld_length,
        }

    def loads(self, state: dict):
        self._vertex_list = [
            [FreeCAD.Vector(x) for x in sublist]
            for sublist in state.get("_vertex_list", [])
        ]
        self._weld_length = state.get("_weld_length", 0.0)
        return None

    def _recompute_vertices(self, obj):
        """Call this as little as possible to save compute time"""
        bead_size = float(obj.WeldSize.getValueAs("mm"))
        if bead_size < 1e-1:
            FreeCAD.Console.PrintUserError(
                "Weld sizes of less than 0.1mm are not supported\n"
            )
            return
        # this should be a list of tuples, something like:
        # [(<obj001>, ['Edge1', 'Edge2']), (<obj002>, ['Edge1', 'Edge3'])]
        geom_selection = obj.Base

        if not geom_selection:
            self._vertex_list = []
            return
        unsorted_edges = expand_selection_to_geometry(
            geom_selection, obj.PropagateSelection
        )
        # when restoring documents, all edges may briefly be null for some reason
        amount_of_null_shapes = len(
            [x for x in [edge.isNull() for edge in unsorted_edges] if x]
        )
        if amount_of_null_shapes == len(unsorted_edges):
            return
        sorted_edges = Part.sortEdges(unsorted_edges)

        lists_of_vertexes = []

        # TODO: this will cause errors with objects in differing geofeature groups
        if obj.IntermittentWeld:
            for edge_group in sorted_edges:
                lists_of_vertexes.extend(
                    discretize_intermittent(
                        edge_group,
                        bead_size,
                        float(obj.IntermittentWeldLength.getValueAs("mm")),
                        float(obj.IntermittentWeldPitch.getValueAs("mm")),
                        float(obj.IntermittentWeldOffset.getValueAs("mm")),
                    )
                )
        else:
            for edge_group in sorted_edges:
                lists_of_vertexes.append(
                    discretize_list_of_edges(edge_group, bead_size)
                )
        # the final vertex list is a nested list, where each sublist is a smooth
        # discretization of multiple connected edges
        self._vertex_list = lists_of_vertexes
        self._update_weld_length(obj)

    def _update_weld_length(self, obj):
        """based on self._vertex_list (a list of lists of FreeCAD.Vector), this
        function calculates the total path length of weld using the simple
        cumulative-distance-between-points method.
        This has some numerical inaccuracy vs. the edge length of the originally
        selected edges. However, this discrepancy is minimal for reasonable weld
        bead sizes, and this method works seamlessly with intermittent welds
        """
        running_total = 0.0
        for sublist in self._vertex_list:
            running_total += sum(
                starmap(lambda x, y: x.distanceToPoint(y), zip(sublist, sublist[1:]))
                # zip automatically stops before running off the end of the list-^
            )
        self._weld_length = running_total
        # we must toggle the ReadOnly propertybit in order to set the value at all
        obj.setPropertyStatus("WeldLength", "-ReadOnly")
        obj.WeldLength = self._weld_length
        obj.setPropertyStatus("WeldLength", "ReadOnly")

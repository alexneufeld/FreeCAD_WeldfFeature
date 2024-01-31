import FreeCAD
import Part
from .geom_utils import discretize_list_of_edges


class WeldFeature:
    def __init__(self, obj):
        obj.Proxy = self
        # add_property(type, name, section, description)
        # supported properties
        # TODO: when we decide to support multiple object selections in one WeldFeature, change this property type to App::PropertyXLinkSubList
        obj.addProperty(
            "App::PropertyXLinkSubList",
            "Base",
            "Base",
            "Reference geometry for the weld bead. "
            "Multiple faces, edges, and points may be selected.",
        )
        obj.addProperty(
            "App::PropertyLength", "WeldSize", "Weld", "Size of the weld bead."
        )

        obj.addProperty(
            "App::PropertyBool",
            "IntermittentWeld",
            "Weld",
            "Whether to model an intermittent or continous weld",
        )
        obj.addProperty(
            "App::PropertyEnumeration",
            "IntermittentWeldSpecification",
            "Weld",
            "Method of specification for intermittent welds",
        )
        obj.IntermittentWeldSpecification = [
            "Length-Pitch",
            "Length-Number",
            # "Pitch-Number",  # This would leave the weld length ambigous?
        ]
        obj.addProperty(
            "App::PropertyInteger",
            "NumberOfIntermittentWelds",
            "Weld",
            "Number of welds in an intermittent weld",
        )
        obj.addProperty(
            "App::PropertyLength",
            "IntermittentWeldSpacing",
            "Weld",
            "Spacing (pitch) of intermittent welds",
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
            "Offest of the start of the intermittent weld pattern "
            "from the start of selected edges",
        )

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

        self._vertex_list = []

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop: str):
        if prop == "Base":
            self._recompute_vertices(obj)
        if prop == "WeldSize":
            self._recompute_vertices(obj)
        if prop == "IntermittentWeld":
            # when not using an intermittent weld,
            # hide visibility of associated properties
            dependant_properties = [
                "NumberOfIntermittentWelds",
                "IntermittentWeldSpacing",
                "IntermittentWeldLength",
                "IntermittentWeldOffset",
                "IntermittentWeldSpecification",
            ]
            for property_name in dependant_properties:
                # can also use "-Hidden" to clear the status bit
                obj.setPropertyStatus(
                    property_name, "-" * int(obj.IntermittentWeld) + "Hidden"
                )
        if prop == "IntermittentWeldSpecification":
            pass
        if prop == "NumberOfIntermittentWelds":
            pass
        if prop == "IntermittentWeldSpacing":
            pass
        if prop == "IntermittentWeldLength":
            pass
        if prop == "IntermittentWeldOffset":
            pass
        if prop == "FieldWeld":
            pass
        if prop == "AlternatingWeld":
            pass
        if prop == "AllAround":
            pass
        if prop == "WeldLength":
            pass

    def dumps(self):
        return {
            "_vertex_list": [
                [tuple(x) for x in sublist] for sublist in self._vertex_list
            ]
        }

    def loads(self, state: dict):
        self._vertex_list = [
            [FreeCAD.Vector(x) for x in sublist]
            for sublist in state.get("_vertex_list", [])
        ]
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
        unsorted_edges = []
        for subselection in geom_selection:
            base_object, subelement_names = subselection
            # flatten the list of selected document objects.
            # We'll then re-sort them into groups of connected edges,
            # ignoring which document objects those edges originally belonged to.
            unsorted_edges.extend(
                [base_object.getSubObject(name) for name in subelement_names]
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
        for edge_group in sorted_edges:
            lists_of_vertexes.append(discretize_list_of_edges(edge_group, bead_size))
        # the final vertex list is a nested list, where each sublist is a smooth
        # discretization of multiple connected edges
        self._vertex_list = lists_of_vertexes

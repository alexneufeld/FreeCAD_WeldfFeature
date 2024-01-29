class WeldFeature:
    def __init__(self, obj):
        obj.Proxy = self
        # add_property(type, name, section, description)
        # supported properties
        # TODO: when we decide to support multiple object selections in one WeldFeature, change this property type to App::PropertyXLinkSubList
        obj.addProperty(
            "App::PropertyXLinkSub",
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
            "Method of specification for intermittent welds"
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
            "Whether this weld should be completed in the field"
        )
        obj.addProperty(
            "App::PropertyBool",
            "AlternatingWeld",
            "WeldInformation",
            "Whether this weld alternates on either side of the selected shape"
        )
        obj.addProperty(
            "App::PropertyBool",
            "AllAround",
            "WeldInformation",
            "Whether this weld wrap all the way around the selected shape"
        )
        obj.addProperty(
            "App::PropertyLength",
            "WeldLength",
            "WeldInformation",
            "Computed Length of weld material in this weld object"
        )

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop):
        if prop == "WeldSize":
            pass
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

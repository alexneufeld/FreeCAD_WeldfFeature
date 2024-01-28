
class WeldFeature():
    def __init__(self, obj):
        obj.Proxy = self
        # add_property(type, name, section, description)
        # supported properties
        __possible_properties = ['App::PropertyBool', 'App::PropertyBoolList', 'App::PropertyFloat', 'App::PropertyFloatList', 'App::PropertyFloatConstraint', 'App::PropertyPrecision', 'App::PropertyQuantity', 'App::PropertyQuantityConstraint', 'App::PropertyInteger', 'App::PropertyIntegerConstraint', 'App::PropertyPercent', 'App::PropertyEnumeration', 'App::PropertyIntegerList', 'App::PropertyIntegerSet', 'App::PropertyMap', 'App::PropertyString', 'App::PropertyPersistentObject', 'App::PropertyUUID', 'App::PropertyFont', 'App::PropertyStringList', 'App::PropertyLink', 'App::PropertyLinkChild', 'App::PropertyLinkGlobal', 'App::PropertyLinkHidden', 'App::PropertyLinkSub', 'App::PropertyLinkSubChild', 'App::PropertyLinkSubGlobal', 'App::PropertyLinkSubHidden', 'App::PropertyLinkList', 'App::PropertyLinkListChild', 'App::PropertyLinkListGlobal', 'App::PropertyLinkListHidden', 'App::PropertyLinkSubList', 'App::PropertyLinkSubListChild', 'App::PropertyLinkSubListGlobal', 'App::PropertyLinkSubListHidden', 'App::PropertyXLink', 'App::PropertyXLinkSub', 'App::PropertyXLinkSubList', 'App::PropertyXLinkList', 'App::PropertyMatrix', 'App::PropertyVector', 'App::PropertyVectorDistance', 'App::PropertyPosition', 'App::PropertyDirection', 'App::PropertyVectorList', 'App::PropertyPlacement', 'App::PropertyPlacementList', 'App::PropertyPlacementLink', 'App::PropertyRotation', 'App::PropertyColor', 'App::PropertyColorList', 'App::PropertyMaterial', 'App::PropertyMaterialList', 'App::PropertyPath', 'App::PropertyFile', 'App::PropertyFileIncluded', 'App::PropertyPythonObject', 'App::PropertyExpressionEngine', 'App::PropertyAcceleration', 'App::PropertyAmountOfSubstance', 'App::PropertyAngle', 'App::PropertyArea', 'App::PropertyCompressiveStrength', 'App::PropertyCurrentDensity', 'App::PropertyDensity', 'App::PropertyDissipationRate', 'App::PropertyDistance', 'App::PropertyDynamicViscosity', 'App::PropertyElectricalCapacitance', 'App::PropertyElectricalConductance', 'App::PropertyElectricalConductivity', 'App::PropertyElectricalInductance', 'App::PropertyElectricalResistance', 'App::PropertyElectricCharge', 'App::PropertyElectricCurrent', 'App::PropertyElectricPotential', 'App::PropertyFrequency', 'App::PropertyForce', 'App::PropertyHeatFlux', 'App::PropertyInverseArea', 'App::PropertyInverseLength', 'App::PropertyInverseVolume', 'App::PropertyKinematicViscosity', 'App::PropertyLength', 'App::PropertyLuminousIntensity', 'App::PropertyMagneticFieldStrength', 'App::PropertyMagneticFlux', 'App::PropertyMagneticFluxDensity', 'App::PropertyMagnetization', 'App::PropertyMass', 'App::PropertyPressure', 'App::PropertyPower', 'App::PropertyShearModulus', 'App::PropertySpecificEnergy', 'App::PropertySpecificHeat', 'App::PropertySpeed', 'App::PropertyStiffness', 'App::PropertyStress', 'App::PropertyTemperature', 'App::PropertyThermalConductivity', 'App::PropertyThermalExpansionCoefficient', 'App::PropertyThermalTransferCoefficient', 'App::PropertyTime', 'App::PropertyUltimateTensileStrength', 'App::PropertyVacuumPermittivity', 'App::PropertyVelocity', 'App::PropertyVolume', 'App::PropertyVolumeFlowRate', 'App::PropertyVolumetricThermalExpansionCoefficient', 'App::PropertyWork', 'App::PropertyYieldStrength', 'App::PropertyYoungsModulus']

        # TODO: when we decide to support multiple object selections in one WeldFeature, change this property type to App::PropertyXLinkSubList
        obj.addProperty("App::PropertyXLinkSub", "Base", "Base", "Reference geometry for the weld bead. Multiple faces, edges, and points may be selected.")
        obj.addProperty("App::PropertyLength", "WeldSize", "Weld", "Size of the weld bead.")

        obj.addProperty("App::PropertyBool", "IntermittentWeld", "Weld", "Whether to model an intermittent or continous weld")
        # obj.addProperty("App::PropertyEnum", "IntermittentSpecification", "Weld", "Method of specification for intermittent welds")
        # enum_values = [
        #     "Length-Pitch",
        #     "Length-Number",
        #     "Pitch-Number"
        # ]
        obj.addProperty("App::PropertyInteger", "NumberOfWelds", "Weld", "Number of welds in an intermittent weld")
        obj.addProperty("App::PropertyLength", "WeldSpacing", "Weld", "Spacing (pitch) of intermittent welds")
        obj.addProperty("App::PropertyLength", "WeldLength", "Weld", "Length of individual welds in an intermittent weld")


        obj.addProperty("App::PropertyBool", "FieldWeld", "WeldInformation", "")
        obj.addProperty("App::PropertyBool", "AlternatingWeld", "WeldInformation", "")
        obj.addProperty("App::PropertyBool", "AllAround", "WeldInformation", "")


    def execute(self, obj):
        pass

    def onChanged(self, obj, prop):
        if prop == "IntermittentWeld":
            # when not using an intermittent weld, hide visibility of associated properties
            dependant_properties = [
                "NumberOfWelds",
                "WeldSpacing",
                "WeldLength"
            ]
            for property_name in dependant_properties:
                # can also use "-Hidden" to clear the status bit
                # other property status bit that are possible:
                # [
                #     'CopyOnChange',
                #     'Hidden',
                #     'Immutable',
                #     'LockDynamic',
                #     'MaterialEdit',
                #     'NoMaterialListEdit',
                #     'NoModify',
                #     'NoRecompute',
                #     'Output',
                #     'PartialTrigger',
                #     'ReadOnly',
                #     'Transient',
                #     'UserEdit'
                # ]
                obj.setPropertyStatus(
                    property_name,
                    "-"*int(obj.IntermittentWeld) + "Hidden"
                )


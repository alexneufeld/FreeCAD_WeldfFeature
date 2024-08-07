import colorsys
import FreeCAD
import FreeCADGui


def parse_and_clean_selection():
    """By default, FreeCAD sort of obfuscates the entities that are selected when an
    object inside a group or a feature of a PartDesign body is selected.
    This function carefully inspects the selection and tries to correctly disambiguate
    the users intended geometry selection. It returns a nested list, I.E.:
    [(<Obj1>, ('Edge1', 'Edge2')), (<Obj2>, ('Edge5', 'Face2'))]"""

    # TODO: also investigate usage of the expandSubName and flattenSubName methods
    # of document objects

    doc = FreeCAD.ActiveDocument
    complete_un_messed_up_selection = FreeCADGui.Selection.getCompleteSelection(0)
    # We must use resolve=0 in the second argument, otherwise important
    # information about the selection hierarchy is just lost...
    list_of_fixed_selections = []
    for selitem in complete_un_messed_up_selection:
        # skip selection items that don't have SubObjects
        if (
            selitem.SubElementNames == ("",)
            or not selitem.HasSubObjects
            or len(selitem.SubElementNames) == 1
            and selitem.SubElementNames[0].endswith(".")
        ):
            FreeCAD.Console.PrintUserWarning(
                "Skipping selected item with no subobjects"
            )
            continue
        # we need to parse the required info by brute force. E.G.:
        # selitem.FullName is something like:
        # "(App.getDocument('Unnamed').getObject('Part'),['Link.Chamfer.Edge2',])"
        # we care about these: ----------------------------^------------^
        # I.E.: we need to know that Link.Edge2 was what the user actually selected
        # AFAIK this isn't easy to do for 2 main reasons
        # - backwards compatibility issues with App:Links and Toponaming
        # - many commands (such as partdesign stuff) actually want Chamfer.Edge2
        #   in this sort of situation
        if not selitem.HasSubObjects:
            # we need some geometry (edges, faces, points) to be selected
            # a selection object will not have sub-objects if the document object
            # was selected in the tree view, for example...
            raise RuntimeError(
                "You must select some geometric elements, not just a document object!"
            )
        # continuing with our previous example, the call to SubElementNames should
        # return something like this: ('Link.Chamfer.Edge2', 'Link.Chamfer.Edge10')
        # We assume that each selection object will contain only geometry of a single
        # document object. Testing indicates that this is correct,
        # but TODO: further verify!
        # Based on this assumption, all of the paths in the list of subelements should
        # be identical up to the last node. Therefore, only run the following logic
        # on the first one
        the_actual_object = None
        # SubElementNames looks like:
        # ('Box.Edge10',)  # version 0.20
        # ('Pad001.;g1v1;SKT;:H6bb,V;:G;XTR;:H6bb:7,E.Edge1',)  # version 0.22
        # in newer versions the full element naming path is shown
        sub_names = selitem.SubElementNames[0].split(".")
        for sub_index, sub_name in enumerate(sub_names):
            # sub_thing should be a valid name for a document object in the active
            # document. We need the actual object to inspect it, not just the name
            doc_obj = doc.getObject(sub_name)
            if doc_obj is None:
                # Most likely we iterated to the end of the subelement chain without
                # otherwise breaking the loop somehow. If the current sub_name is the
                # last in the chain, it is most likely something like 'Edge010' or
                # 'Face002', and no error has occurred.
                if sub_index + 1 == len(sub_names):
                    continue
                elif ";" in sub_name:
                    # account for element naming history if present
                    # this is probably not strictly correct - the naming history doesn't
                    # neccesarily HAVE to contain a semicolon...
                    continue
                else:
                    raise RuntimeError(
                        "Couldn't parse the correct selected geometry... "
                        f"Object '{sub_name}' was not found in the active document."
                    )
            if (doc_obj.TypeId == "App::Part") or (
                doc_obj.TypeId == "App::DocumentObjectGroup"
            ):
                # Parts and groups will appear in the chain, but we want to essentially
                # ignore them. If we incorrectly infer that a Part container is the
                # selected object when the user actually meant to select some other
                # object grouped under the App::Part in the tree view, we will likely
                # end up placing our object in an incorrect location in the 3D view.
                continue
            if doc_obj.isDerivedFrom("PartDesign::Feature"):
                # PartDesign bodies have some particularly nasty selection behaviour
                # By default, a PartDesign::Body's ViewProvider's 'DisplayModeBody'
                # property is set to 'Through'. This allows correct selection of Body
                # feature geometry when creating chamfers or adding sketches, for
                # example. But when not editing the body itself, this behaviour causes
                # headaches. The subelements of the bodies' tip will be selected instead
                # of the subelements of the body itself, (These 2 things are the same
                # geometry, but using the former causes FreeCAD to complain that "Links
                # go out of the allowed scope" for example)
                #  Therefore, we loop past these features
                continue
            # we assume that all objects that aren't well known Container types of
            # partdesign nonsense will offer up a Shape nicely and not screw around
            # with the placement of their subobjects. In the broadly general case,
            # this is likely not correct. One could likely write a custom python
            # object that specifically breaks this assumption, for example.
            if hasattr(doc_obj, "Shape"):
                the_actual_object = doc_obj
                break
            # if we iterated over all of the subelements and didn't find something
            # suitable to use as the actual selected object, our next best guess
            # is to use the root object of the complete selection
        if the_actual_object is None:
            the_actual_object = selitem.Object
        # finally, also grab the descriptive names of each of the geometric elements
        # selected:
        geom_subnames = [list(x.split("."))[-1] for x in selitem.SubElementNames]
        list_of_fixed_selections.append((the_actual_object, tuple(geom_subnames)))
    return list_of_fixed_selections


def set_default_values(document_object, value_map):
    for k, v in value_map.items():
        setattr(document_object, k, v)


class FreeCADColorUtils:
    @staticmethod
    def int_to_rgba(i: int) -> tuple[int]:
        r = ((i & 0xFF000000) >> 24) / 255
        g = ((i & 0x00FF0000) >> 16) / 255
        b = ((i & 0x0000FF00) >> 8) / 255
        a = (i & 0x000000FF) / 255
        return (r, g, b, a)

    @staticmethod
    def rgba_to_int(r, g, b, a) -> int:
        ri, gi, bi, ai = [int(x * 255) for x in (r, g, b, a)]
        return (ri << 24) + (gi << 16) + (bi << 8) + ai

    @staticmethod
    def rgba_to_hex(r, g, b, a) -> str:
        vals = tuple([int(x * 255) for x in (r, g, b, a)])
        return "#%0.2X%0.2X%0.2X%0.2X" % vals


def get_complementary_shade(rgb: tuple):
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    change = 0.25
    if v <= 0.5:
        # the alternate color is the base color, but 25% lighter
        new_v = v + change
    elif v > 0.5:
        # the alternate color is the base color, but 25% darker
        new_v = v - change
    return colorsys.hsv_to_rgb(h, s, new_v)


def get_best_default_object_colors(document_object):
    """Tries to choose a sensible default color for weld bead objects"""
    base_color = None
    if hasattr(document_object.ViewObject, "ShapeColor"):
        base_color = document_object.ViewObject.ShapeColor
    elif hasattr(document_object.ViewObject, "Color"):
        base_color = document_object.ViewObject.Color
    else:
        # if we couldn't infer a usable color from the base object,
        # use FreeCAD's default object shape color:
        view_params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View")
        color_int = view_params.GetUnsigned("DefaultShapeColor", 0xFF0000FF)
        base_color = FreeCADColorUtils.int_to_rgba(color_int)
    # choose an alternate color from the base color:
    rgb = base_color[:3]
    alternate_color = (*get_complementary_shade(rgb), 1.0)

    return (base_color, alternate_color)

from enum import Enum
from enum import auto

class ConnectModes(Enum):
    CLOSEST = auto()
    FIRST = auto()
    LAST = auto()


def discretize_list_of_edges(edge_list, connectmode=ConnectModes.CLOSEST):
    """returns a list of FreeCAD.Vector"""
    resultant_points = []
    is_first = True
    for edge in edge_list:
        # Ititial implementation - just break edge into n equal segments
        # In the future, we should use an error tolerance based algorithm
        # Can possibly just steal something from the CurvesWB
        if is_first:
            correctly_oriented_edge = edge
            is_first = False
        elif connectmode == ConnectModes.FIRST:
            # this mode always used the forward orientation
            correctly_oriented_edge = edge
        elif connectmode == ConnectModes.LAST:
            # this mode always used the reverse orientation
            correctly_oriented_edge = edge.reversed()
        elif connectmode == ConnectModes.CLOSEST:
            first_param, last_param = edge.ParameterRange
            distance_to_first = edge.valueAt(first_param).distanceToPoint(resultant_points[-1])
            distance_to_last = edge.valueAt(last_param).distanceToPoint(resultant_points[-1])
            if distance_to_first < distance_to_last:
                correctly_oriented_edge = edge
            else:
                correctly_oriented_edge = edge.reversed()
        # get the parameter range again, in case reversing it changed the range somehow
        first_param, last_param = correctly_oriented_edge.ParameterRange
        fn = 100
        for i in range(fn):
            # NOTE: this neglects the last point on the edge
            resultant_points.append(correctly_oriented_edge.valueAt(first_param + i/fn*(last_param-first_param)))
    return resultant_points

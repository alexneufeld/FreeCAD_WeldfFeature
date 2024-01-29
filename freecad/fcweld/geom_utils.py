import math
import FreeCAD
import collections
import itertools
import copy
import Part


def round_vector(vec, eps=1e-5):
    return FreeCAD.Vector(*[round(d, math.ceil(-math.log10(eps))) for d in vec])

def should_flip_edges(this_edge, next_edge, eps=1e-5):
    this_first = this_edge.valueAt(this_edge.FirstParameter)
    this_last = this_edge.valueAt(this_edge.LastParameter)
    next_first = next_edge.valueAt(next_edge.FirstParameter)
    next_last = next_edge.valueAt(next_edge.LastParameter)
    if this_last.distanceToPoint(next_first) < eps:
        return (False, False)
    if this_last.distanceToPoint(next_last) < eps:
        return (False, True)
    if this_first.distanceToPoint(next_first) < eps:
        return (True, False)
    if this_first.distanceToPoint(next_last) < eps:
        return (True, True)
    raise RuntimeError("Edges are not connected")

def discretize_list_of_edges(edge_list, pitch):
    """returns a list of FreeCAD.Vector
    This function should be supplied a list of connected edges. They don't neccesarliy need to be in order of connection
    """
    # first check that all edges are connected
    incidence_list = []
    vertex_list = []
    for edge in edge_list:
        first_param, last_param = edge.ParameterRange
        first_vertex=round_vector(edge.valueAt(first_param))
        last_vertex=round_vector(edge.valueAt(last_param))
        if first_vertex not in vertex_list:
            vertex_list.append(first_vertex)
            first_index = len(vertex_list) - 1
        else:
            first_index = vertex_list.index(first_vertex)
        if last_vertex not in vertex_list:
            vertex_list.append(last_vertex)
            last_index = len(vertex_list) - 1
        else:
            last_index = vertex_list.index(last_vertex)
        incidence_list.append([first_index, last_index])
    len_diff = len(vertex_list) - len(incidence_list)
    # print(f"{vertex_list=}")
    # print(f"{incidence_list=}")
    degrees_of_vertexes = collections.Counter(itertools.chain.from_iterable(incidence_list))
    # print(f"{degrees_of_vertexes=}")
    # count the number of times each vertex appears in the indidence list
    numbers_of_vertexes_of_degree_n = collections.Counter(degrees_of_vertexes.values())
    # print(numbers_of_vertexes_of_degree_n)
    if dict(numbers_of_vertexes_of_degree_n) == {2: len(incidence_list)}:
        FreeCAD.Console.PrintLog("graph is a cycle\n")
        is_closed = True
        is_degenerate = False
    if dict(numbers_of_vertexes_of_degree_n) == {1: 2,}:
        FreeCAD.Console.PrintLog("graph is a single non-cyclic edge\n")
        is_closed = False
        is_degenerate = False
    if dict(numbers_of_vertexes_of_degree_n) == {1: 2, 2: len(incidence_list) - 1}:
        FreeCAD.Console.PrintLog("graph is a path")
        is_closed = False
        is_degenerate = False
    if [k for k in numbers_of_vertexes_of_degree_n.keys()] == [1, 2] and numbers_of_vertexes_of_degree_n[1] > 2:
        FreeCAD.Console.PrintLog("Multiple discontinous edge sets selected. This may cause unexpected behaviour!\n")
        is_closed = False
        is_degenerate = True
    if [k for k in numbers_of_vertexes_of_degree_n.keys() if k > 2] != []:
        FreeCAD.Console.PrintLog("One or more pairs of vertices in the selected edge set are conected by more than one edge. This may cause unexpected behaviour!\n")
        is_closed = False
        is_degenerate = True

    # sort the edges. Or don't, in the case of degenerate stuff
    if is_degenerate:
        sorted_edges = edge_list
    # elif is_closed:
    #     unsorted_edges = edge_list.copy()
    #     sorted_edges = []
    #     # the graph is a cycle. we can start with any edge. We just have to make sure not to use any edges more than once
    #     edge_map = dict(zip(itertools.count(), incidence_list))
    #     last_index = 0
    #     connected_vertices = edge_map.pop(last_index)
    #     sorted_edges.append(edge_list[last_index])
    #     while len(sorted_edges) < len(edge_list):
    #         # find any ramining edge connected to the last edge. There should only be 1
    #         for x in edge_map:
    #             if set(connected_vertices) & set(edge_map[x]) != set():
    #                 last_index = x
    #                 break
    #         connected_vertices = edge_map.pop(last_index)
    #         sorted_edges.append(edge_list[last_index])
    # else:  # path graph, non-degenerate
    #     unsorted_edges = edge_list.copy()
    #     sorted_edges = []
    #     # start with one of the edges that has a degree 1 vertex
    #     edge_map = dict(zip(itertools.count(), incidence_list))
    #     # start with an edge with a vertex of degree 1
    #     for index, (v1, v2) in edge_map.items():
    #         if (degrees_of_vertexes[v1] == 1) or (degrees_of_vertexes[v2] == 1):
    #             last_index = index
    #             connected_vertices = edge_map.pop(last_index)
    #             sorted_edges.append(edge_list[last_index])
    #             break
    #     while len(sorted_edges) < len(edge_list):
    #         for x in edge_map:
    #             if set(connected_vertices) & set(edge_map[x]) != set():
    #                 last_index = x
    #                 break
    #         connected_vertices = edge_map.pop(last_index)
    #         sorted_edges.append(edge_list[last_index])
    else:
        sorted_edges = Part.sortEdges(edge_list)[0]
    # print(f"{sorted_edges=}")
    resultant_points = []
    is_first = True
    if len(sorted_edges) == 1:
        # special case for a single edge
        return sorted_edges[0].discretize(max([2, math.floor(sorted_edges[0].Length / pitch)]))

    for index, edge in enumerate(sorted_edges):
        # Part.show(edge, f"Edge{index}")
        is_first = index == 0
        is_last = index == len(sorted_edges) - 1
        if is_first:
            next_edge = sorted_edges[1]
            if not should_flip_edges(edge, next_edge)[0]:
                should_flip = True
                print(f"flipping edge {index}")
            else:
                should_flip = False
                print(f"NOT flipping edge {index}")
        else:
            last_edge = sorted_edges[index-1]
            if not should_flip_edges(last_edge, edge)[1]:
                should_flip = False
                print(f"flipping edge {index}")
            else:
                should_flip = False
                print(f"NOT flipping edge {index}")
        # # get the parameter range again, in case reversing it changed the range somehow
        # fn = max([2, math.floor(correctly_oriented_edge.Length / pitch)])
        # points = correctly_oriented_edge.discretize(fn)
        fn = max([2, math.floor(edge.Length / pitch)])
        points = edge.discretize(fn)
        if is_first:
            resultant_points.extend(points[:-1])
        elif is_last:
            resultant_points.extend(points)
        else:
            resultant_points.extend(points[:-1])
    # print(resultant_points)
    # shift the first and last points in a little to prevent face coincidence
    resultant_points[0] = resultant_points[0] + 0.05 * (resultant_points[1] - resultant_points[0])
    resultant_points[-1] = resultant_points[-1] - 0.05 * (resultant_points[-1] - resultant_points[-2])
    return resultant_points

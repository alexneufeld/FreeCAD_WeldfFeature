import math
import FreeCAD
import collections
import itertools
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


class CompositeEdge:
    def __init__(self, list_of_edges):
        self._list_of_edges = Part.sortEdges(list_of_edges)[0]
        self._list_of_lengths = [x.Length for x in self._list_of_edges]
        self._should_flip_list = []
        is_first = True
        for index, edge in enumerate(self._list_of_edges):
            if is_first:
                is_first = False
                next_edge = self._list_of_edges[1]
                if not should_flip_edges(edge, next_edge)[0]:
                    should_flip = True
                else:
                    should_flip = False
            else:
                last_edge = self._list_of_edges[index - 1]
                if not should_flip_edges(last_edge, edge)[1]:
                    should_flip = True
                else:
                    should_flip = False
            self._should_flip_list.append(not should_flip)

    @property
    def Length(self):
        return sum(x.Length for x in self._list_of_edges)

    def discretize(self, n):
        points = []
        firstparam, lastparam = self.ParameterRange
        for i in range(n):
            points.append(self.valueAt(i/n*(lastparam-firstparam)))
        points.append(self.valueAt(lastparam))
        return points

    @property
    def ParameterRange(self):
        return (0.0, self.Length)

    def valueAt(self, param):
        if (param  < self.ParameterRange[0]) or (param > self.ParameterRange[1]):
            raise ValueError(f"Requested point ({param}) is outside the parameter range ({self.ParameterRange})")
        running_total = 0.0
        for i in range(len(self._list_of_edges)):
            running_total += self._list_of_edges[i].Length
            index_of_the_edge = i
            if param <= running_total:
                break
        the_edge = self._list_of_edges[index_of_the_edge]
        firstparam, lastparam = the_edge.ParameterRange
        e_length = the_edge.Length
        len_of_all_previous = running_total - e_length
        if not self._should_flip_list[index_of_the_edge]:
            # don't flip
            traverse = (param - len_of_all_previous) / e_length
        else:
            traverse = 1 - (param - len_of_all_previous) / e_length
        value = the_edge.valueAt(firstparam + traverse * (lastparam - firstparam))
        return value

def discretize_list_of_edges(edge_list, pitch):
    if len(edge_list) == 1:
        # special case for a single edge
        comp = edge_list[0]
    comp = CompositeEdge(edge_list)
    elen = comp.Length
    number_to_split_into = max(2, round(elen / pitch))
    points = comp.discretize(number_to_split_into)
    print(points)
    return points

def _discretize_list_of_edges(edge_list, pitch):
    """returns a list of FreeCAD.Vector
    This function should be supplied a list of connected edges.
    They don't neccesarliy need to be in order of connection
    """
    # first check that all edges are connected
    incidence_list = []
    vertex_list = []
    for edge in edge_list:
        first_param, last_param = edge.ParameterRange
        first_vertex = round_vector(edge.valueAt(first_param))
        last_vertex = round_vector(edge.valueAt(last_param))
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
    # print(f"{vertex_list=}")
    # print(f"{incidence_list=}")
    degrees_of_vertexes = collections.Counter(
        itertools.chain.from_iterable(incidence_list)
    )
    # print(f"{degrees_of_vertexes=}")
    # count the number of times each vertex appears in the indidence list
    numbers_of_vertexes_of_degree_n = collections.Counter(degrees_of_vertexes.values())
    # print(numbers_of_vertexes_of_degree_n)
    if dict(numbers_of_vertexes_of_degree_n) == {2: len(incidence_list)}:
        FreeCAD.Console.PrintLog("graph is a cycle\n")
        # is_closed = True
        is_degenerate = False
    if dict(numbers_of_vertexes_of_degree_n) == {
        1: 2,
    }:
        FreeCAD.Console.PrintLog("graph is a single non-cyclic edge\n")
        # is_closed = False
        is_degenerate = False
    if dict(numbers_of_vertexes_of_degree_n) == {1: 2, 2: len(incidence_list) - 1}:
        FreeCAD.Console.PrintLog("graph is a path\n")
        # is_closed = False
        is_degenerate = False
    if [k for k in numbers_of_vertexes_of_degree_n.keys()] == [
        1,
        2,
    ] and numbers_of_vertexes_of_degree_n[1] > 2:
        FreeCAD.Console.PrintLog(
            "Multiple discontinous edge sets selected."
            " This may cause unexpected behaviour!\n"
        )
        # is_closed = False
        is_degenerate = True
    if [k for k in numbers_of_vertexes_of_degree_n.keys() if k > 2] != []:
        FreeCAD.Console.PrintLog(
            "One or more pairs of vertices in the selected edge set "
            "are conected by more than one edge."
            " This may cause unexpected behaviour!\n"
        )
        # is_closed = False
        is_degenerate = True

    # sort the edges. Or don't, in the case of degenerate stuff
    if is_degenerate:
        sorted_edges = Part.sortEdges(edge_list)[0]
    else:
        sorted_edges = Part.sortEdges(edge_list)[0]
    # print(f"{sorted_edges=}")
    resultant_points = []
    is_first = True
    if len(sorted_edges) == 1:
        # special case for a single edge
        return sorted_edges[0].discretize(
            max([2, math.floor(sorted_edges[0].Length / pitch)])
        )

    for index, edge in enumerate(sorted_edges):
        # Part.show(edge, f"Edge{index}")
        is_first = index == 0
        is_last = index == len(sorted_edges) - 1
        if is_first:
            next_edge = sorted_edges[1]
            if not should_flip_edges(edge, next_edge)[0]:
                should_flip = True
            else:
                should_flip = False
        else:
            last_edge = sorted_edges[index - 1]
            if not should_flip_edges(last_edge, edge)[1]:
                should_flip = True
            else:
                should_flip = False
        should_flip = not should_flip
        fn = max([2, math.floor(edge.Length / pitch)])
        points = edge.discretize(fn)
        if should_flip:
            points.reverse()
        if is_first:
            resultant_points.extend(points[:-1])
        elif is_last:
            resultant_points.extend(points)
        else:
            resultant_points.extend(points[:-1])
    return resultant_points

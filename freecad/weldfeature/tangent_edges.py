import math
from functools import lru_cache
from itertools import combinations
import Part
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from .geom_utils import should_flip_edges

# import numpy as np


def edges_are_connected(edge1, edge2):
    try:
        _ = should_flip_edges(edge1, edge2)
    except RuntimeError:
        return False
    return True


def angle_between_connected_endpoints(edge1, edge2):
    flip_first, flip_last = should_flip_edges(edge1, edge2)
    if not flip_first:
        v1 = edge1.derivative1At(edge1.LastParameter)
    else:
        v1 = edge1.derivative1At(edge1.FirstParameter) * -1
    if flip_last:
        v2 = edge2.derivative1At(edge2.LastParameter)
    else:
        v2 = edge2.derivative1At(edge2.FirstParameter) * -1
    angle = v1.getAngle(v2)  # in radians
    return angle


def get_edgeweight(angle: float):
    # return (angle / math.pi)**4
    # return math.pi - angle + 0.01  # small fudge factor to prevent having to deal with zeros
    return int(angle > math.pi * 0.99)


@lru_cache(maxsize=64)
# def propagate(shape: Part.Shape, edge_index: int) -> list:
def propagate(shape: Part.Shape):
    weights = []
    rows = []
    cols = []
    msize = len(shape.Edges)
    for comb in combinations(enumerate(shape.Edges), 2):
        i, edge_i = comb[0]
        j, edge_j = comb[1]
        if edges_are_connected(edge_i, edge_j):
            w = get_edgeweight(angle_between_connected_endpoints(edge_i, edge_j))
            if w > 0:
                weights.append(w)
                rows.append(i)
                cols.append(j)
        # print(f"Edge{i+1}<->Edge{j+1}")

    adjacency_matrix = csr_matrix((weights, (rows, cols)), shape=(msize, msize))
    dist_matrix, predecessors = dijkstra(
        adjacency_matrix, directed=False, return_predecessors=True, limit=100.0
    )
    # get the indexes in dist_matrix[edge_index] that aren't -inf
    # row = list(dist_matrix[edge_index])
    # print(row)
    # expanded_edge_set = [i for i in range(len(row)) if row[i] < float('inf')]
    return dist_matrix
    # print(predecessors)
    # return expanded_edge_set


def expand_selection_to_geometry(geom_selection, expand=False) -> list[Part.Edge]:
    unsorted_edges = []
    for subselection in geom_selection:
        base_object, subelement_names = subselection
        # flatten the list of selected document objects.
        # We'll then re-sort them into groups of connected edges,
        # ignoring which document objects those edges originally belonged to.
        if not hasattr(base_object, "Shape"):
            continue
        if base_object.Shape.isNull():
            continue  # yet another check for null garbage on document restore
        for subel in subelement_names:
            if subel.startswith("Edge"):
                if expand:
                    index = int(subel.lstrip("Edge")) - 1
                    dist_matrix = propagate(base_object.Shape)
                    row = list(dist_matrix[index])
                    expanded_index_list = [
                        i for i in range(len(row)) if row[i] < float("inf")
                    ]
                    unsorted_edges.extend(
                        list(
                            map(
                                lambda x: base_object.Shape.Edges[x],
                                expanded_index_list,
                            )
                        )
                    )
                else:
                    unsorted_edges.append(base_object.getSubObject(subel))
            elif subel.startswith("Face"):
                unsorted_edges.extend(base_object.getSubObject(subel).Edges)
            else:
                raise RuntimeError(
                    f"Subelement {subel} of {base_object.Name} is not a face or edge"
                )
    return unsorted_edges

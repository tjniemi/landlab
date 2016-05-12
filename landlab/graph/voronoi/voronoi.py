import numpy as np
from scipy.spatial import Voronoi
from scipy.spatial import Delaunay

from ..graph import Graph


class VoronoiGraph(Graph):

    """Graph of a voronoi grid.

    Examples
    --------
    >>> from landlab.graph import VoronoiGraph
    """

    def __init__(self, nodes, **kwds):
        """Create a voronoi grid.

        Parameters
        ----------
        nodes : tuple of array_like
            Coordinates of every node. First *y*, then *x*.

        Examples
        --------
        >>> from landlab.graph import VoronoiGraph
        >>> node_x = [0, 1, 2,
        ...           1, 2, 3]
        >>> node_y = [0, 0, 0,
        ...           2, 2, 2]
        >>> graph = VoronoiGraph((node_y, node_x), rot_sort=True)
        >>> graph.x_of_node
        array([ 0.,  1.,  2.,  1.,  2.,  3.])
        >>> graph.y_of_node
        array([ 0.,  0.,  0.,  2.,  2.,  2.])
        >>> graph.nodes_at_link # doctest: +NORMALIZE_WHITESPACE
        array([[3, 0], [0, 1], [1, 3], [2, 5], [5, 4], [4, 2], [1, 2], [4, 1],
               [4, 3]])
        >>> graph.links_at_node # doctest: +NORMALIZE_WHITESPACE
        array([[ 1,  0, -1, -1], [ 6,  7,  2,  1], [ 3,  5,  6, -1],
               [ 8,  0,  2, -1], [ 4,  8,  7,  5], [ 4,  3, -1, -1]])
        >>> graph.links_at_patch
        array([[2, 0, 1], [3, 4, 5], [5, 7, 6], [7, 8, 2]])
        >>> graph.nodes_at_patch # doctest: +NORMALIZE_WHITESPACE
        array([[3, 0, 1], [5, 4, 2], [4, 1, 2], [4, 3, 1]])
        """
        xy_sort = kwds.pop('xy_sort', True)
        rot_sort = kwds.pop('rot_sort', True)
        max_node_spacing = kwds.pop('max_node_spacing', None)

        from .ext.delaunay import _setup_links_at_patch, remove_tris

        node_y, node_x = (np.asarray(nodes[0], dtype=float),
                          np.asarray(nodes[1], dtype=float))

        delaunay = Delaunay(list(zip(node_x, node_y)))
        # nodes_at_patch = delaunay.simplices

        nodes_at_patch = np.array(delaunay.simplices, dtype=int)
        neighbors_at_patch = np.array(delaunay.neighbors, dtype=int)

        if max_node_spacing is not None:
            max_node_dist = np.ptp(delaunay.simplices, axis=1)
            bad_patches = np.where(max_node_dist > max_node_spacing)[0]
            if len(bad_patches) > 0:
                remove_tris(nodes_at_patch, neighbors_at_patch, bad_patches)
                nodes_at_patch = nodes_at_patch[:-len(bad_patches), :]
                neighbors_at_patch = neighbors_at_patch[:-len(bad_patches), :]

        n_patches = len(nodes_at_patch)
        n_shared_links = np.count_nonzero(neighbors_at_patch > -1)
        n_links = 3 * n_patches - n_shared_links // 2

        links_at_patch = np.empty((n_patches, 3), dtype=int)
        nodes_at_link = np.empty((n_links, 2), dtype=int)

        _setup_links_at_patch(nodes_at_patch,
                              neighbors_at_patch,
                              nodes_at_link, links_at_patch)

        super(VoronoiGraph, self).__init__((node_y.flat, node_x.flat),
                                           links=nodes_at_link,
                                           patches=links_at_patch,
                                           xy_sort=xy_sort,
                                           rot_sort=rot_sort)

import numpy as np
import pysal


class PolygonCollection:
    """
    # function from:
    # https://github.com/pysal/pysal/blob/master/pysal/weights/weights_from_geojson.ipynb
    """
    def __init__(self, polygons, bbox=None):
        """

        Parameters
        ==========
        polygons: dict
                  key is polygon Id, value is PySAL Polygon object
        bbox: list (optional)
              [left, lower, right, upper]

        Notes
        =====
        bbox is supported in geojson specification at both the feature and
        feature collection level. However, not all geojson writers generate
        the bbox at the feature collection level.

        In those cases, the bbox property will be set on initial access.

        """

        self.type = pysal.cg.Polygon
        self.n = len(polygons)
        self.polygons = polygons
        if bbox is None:
            self._bbox = None
        else:
            self._bbox = bbox

    @property
    def bbox(self):
        bboxes = np.array([self.polygons[p].bbox for p in self.polygons])
        mins = bboxes.min(axis=0)
        maxs = bboxes.max(axis=0)
        self._bbox = [mins[0], mins[1], maxs[2], maxs[3]]
        return self._bbox

    def get(self, index):
        return self.polygons[index]

    def __getitem__(self, index):
        return self.polygons[index]


# converting gpd dataframes to polygon collections / points array
def gpd_polygons(gpdf):
    """
    Constructs polygon collection from a geopandas object

    """
    ids = range(len(gpdf))
    polys = list(gpdf['geometry'].apply(pysal.cg.asShape))
    polygons = PolygonCollection(dict(zip(ids, polys)))
    return polygons


def gpd_points(gpdf):
    """
    Constructs points from a geopandas dataframe of polygons
    """
    centroids = gpdf.centroid
    points = list(centroids.apply(lambda x: pysal.cg.asShape(x)))
    return points


def gpd_contiguity(gpdf):
    """
    Contiguity weights
    https://github.com/pysal/pysal/blob/master/pysal/weights/_contW_binning.py
    """
    polygons = gpd_polygons(gpdf)
    neighbors = pysal.weights.\
        Contiguity.ContiguityWeightsPolygons(polygons).w
    # neighbors = pysal.weights.\
    # Contiguity.ContiguityWeightsPolygons(polygons, 2).w    # for rook
    return pysal.W(neighbors)


def gpd_knnW(gpdf, k=2, p=2, ids=None):
    """
    Constructs distance-based spatial weights from a geopandas object
    :param gpd: geopandas dataframe
    :param k: int number of nearest neighbors
    :param p: float
    :return weight

    https://github.com/pysal/pysal/blob/master/pysal/weights/Distance.py
    """
    points = gpd_points(gpdf)
    kd = pysal.cg.kdtree.KDTree(points)
    w = pysal.knnW(kd, k, p, ids)
    return w


def gpd_distanceBandW(gpdf, threshold=11.2):
    """
    https://github.com/pysal/pysal/blob/master/pysal/weights/Distance.py
    """
    points = gpd_points(gpdf)
    w = pysal.DistanceBand(points, threshold)
    return w


def gpd_kernel(gpdf, bandwidth=None, fixed=True, k=2, diagonal=False,
               function='triangular', eps=1.0000001, ids=None):
    """
    Kernel weights
    https://github.com/pysal/pysal/blob/master/pysal/weights/Distance.py
    """
    points = gpd_points(gpdf)
    kw = pysal.Kernel(points, bandwidth=bandwidth, fixed=fixed, k=k,
                      diagonal=diagonal, function=function, eps=eps, ids=ids)
    return kw

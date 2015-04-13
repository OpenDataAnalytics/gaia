"""This package contains interface adapters for IO."""

__all__ = ()

try:
    import netCDF4
except ImportError:
    netCDF4 = None

if netCDF4 is not None:
    __all__ += ('NetCDFReader',)

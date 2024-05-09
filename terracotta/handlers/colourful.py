"""handlers/colourful.py

Handle /colourful API endpoint. Band file retrieval is multi-threaded.
"""

from typing import Sequence, Tuple, Optional, TypeVar
from typing.io import BinaryIO
from concurrent.futures import Future

from terracotta import get_settings, get_driver, image, xyz, exceptions
from terracotta.profile import trace

NumberOrString = TypeVar("NumberOrString", int, float, str)
ListOfRanges = Sequence[
    Optional[Tuple[Optional[NumberOrString], Optional[NumberOrString]]]
]



@trace("colourful_handler")
def colourful(
    some_keys: Sequence[str],
    tile_xyz: Optional[Tuple[int, int, int]] = None,
    *,
    tile_size: Optional[Tuple[int, int]] = None
) -> BinaryIO:
    """Return RGB image as PNG
    """
    import numpy as np

    settings = get_settings()

    if tile_size is None:
        tile_size_ = settings.DEFAULT_TILE_SIZE
    else:
        tile_size_ = tile_size

    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    with driver.connect():
        key_names = driver.key_names

        if len(some_keys) != len(key_names):
            raise exceptions.InvalidArgumentsError(
                "must specify all keys"
            )

        def get_band_future(band_index: int) -> Future:
            return xyz.get_tile_data(
                driver,
                some_keys,
                tile_xyz=tile_xyz,
                tile_size=tile_size_,
                asynchronous=True,
                band_index=band_index
            )

        futures = [get_band_future(key) for key in range(1, 4)]
        out_arrays = []

        for i, band_data_future  in enumerate(futures):
            metadata = driver.get_metadata(some_keys)

            band_stretch_range = list(metadata["range"])

            band_data = band_data_future.result()
            out_arrays.append(image.to_uint8(band_data, *band_stretch_range))

    out = np.ma.stack(out_arrays, axis=-1)
    return image.array_to_png(out)

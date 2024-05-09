"""server/rgb.py

Flask route to handle /rgb calls.
"""

from typing import Optional, Any, Mapping, Dict, Tuple
import json

from marshmallow import Schema, fields, validate, pre_load, ValidationError, EXCLUDE
from flask import request, send_file, Response

from terracotta.server.fields import StringOrNumber, validate_stretch_range
from terracotta.server.flask_api import TILE_API


class ColourfulQuerySchema(Schema):
    keys = fields.String(
        required=True, description="Keys identifying dataset, in order"
    )
    tile_z = fields.Int(required=True, description="Requested zoom level")
    tile_y = fields.Int(required=True, description="y coordinate")
    tile_x = fields.Int(required=True, description="x coordinate")


class ColourfulOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    tile_size = fields.List(
        fields.Integer(),
        validate=validate.Length(equal=2),
        example="[256,256]",
        description="Pixel dimensions of the returned PNG image as JSON list.",
    )


@TILE_API.route("/colourful/<int:tile_z>/<int:tile_x>/<int:tile_y>.png", methods=["GET"])
@TILE_API.route(
    "/colourful/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png", methods=["GET"]
)
def get_colourful(tile_z: int, tile_y: int, tile_x: int, keys: str = "") -> Response:
    """Return the requested RGB tile as a PNG image.
    ---
    get:
        summary: /rgb (tile)
        description: Combine three datasets to RGB image, and return tile as PNG
        parameters:
            - in: path
              schema: ColourfulQuerySchema
            - in: query
              schema: ColourfulOptionSchema
        responses:
            200:
                description:
                    PNG image of requested tile
            400:
                description:
                    Invalid query parameters
            404:
                description:
                    No dataset found for given key combination
    """
    tile_xyz = (tile_x, tile_y, tile_z)
    return _get_colourful_image(keys, tile_xyz=tile_xyz)


class ColourfulPreviewQuerySchema(Schema):
    keys = fields.String(
        required=True, description="Keys identifying dataset, in order"
    )


@TILE_API.route("/rgb/preview.png", methods=["GET"])
@TILE_API.route("/rgb/<path:keys>/preview.png", methods=["GET"])
def get_colourful_preview(keys: str = "") -> Response:
    """Return the requested RGB dataset preview as a PNG image.
    ---
    get:
        summary: /rgb (preview)
        description: Combine three datasets to RGB image, and return preview as PNG
        parameters:
            - in: path
              schema: ColourfulPreviewQuerySchema
            - in: query
              schema: ColourfulOptionSchema
        responses:
            200:
                description:
                    PNG image of requested tile
            400:
                description:
                    Invalid query parameters
            404:
                description:
                    No dataset found for given key combination
    """
    return _get_colourful_image(keys)


def _get_colourful_image(
    keys: str, tile_xyz: Optional[Tuple[int, int, int]] = None
) -> Response:
    from terracotta.handlers.colourful import colourful

    option_schema = ColourfulOptionSchema()
    options = option_schema.load(request.args)

    some_keys = [key for key in keys.split("/") if key]

    image = colourful(
        some_keys,
        tile_xyz=tile_xyz,
        **options,
    )

    return send_file(image, mimetype="image/png")

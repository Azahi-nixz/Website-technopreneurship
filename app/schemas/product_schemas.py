from marshmallow import Schema, fields, validate


class ProductImageSchema(Schema):
    id = fields.UUID(dump_default=None)
    product_id = fields.UUID(dump_default=None)
    image_url = fields.String(dump_default=None)
    display_order = fields.Integer(dump_default=None)


class ProductSchema(Schema):
    id = fields.UUID(dump_default=None)
    name = fields.String(dump_default=None)
    description = fields.String(load_default=None, dump_default=None, allow_none=True)
    price = fields.Decimal(
        places=2,
        validate=validate.Range(min=0),
        dump_default=None,
    )
    is_active = fields.Boolean(dump_default=None)
    created_at = fields.DateTime(dump_default=None)
    images = fields.List(fields.Nested(ProductImageSchema), load_default=list, dump_default=list)

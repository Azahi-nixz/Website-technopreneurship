from marshmallow import Schema, fields, validate


class ProductImageSchema(Schema):
    id = fields.String(dump_default=None)
    product_id = fields.String(dump_default=None)
    image_url = fields.String(dump_default=None)
    display_order = fields.Integer(dump_default=None)


class ProductSchema(Schema):
    id = fields.String(dump_default=None)
    name = fields.String(dump_default=None)
    description = fields.String(load_default=None, dump_default=None, allow_none=True)
    price = fields.String(dump_default=None)          # serialized as string to avoid Decimal JSON issues
    compare_at_price = fields.String(load_default=None, dump_default=None, allow_none=True)
    tier = fields.String(load_default=None, dump_default=None, allow_none=True)
    is_active = fields.Boolean(dump_default=None)
    created_at = fields.DateTime(dump_default=None)
    images = fields.List(fields.Nested(ProductImageSchema), load_default=list, dump_default=list)

from marshmallow import Schema, fields, validate

from .product_schemas import ProductSchema


class CartItemSchema(Schema):
    id = fields.UUID(dump_default=None)
    user_id = fields.UUID(dump_default=None)
    product_id = fields.UUID(dump_default=None)
    quantity = fields.Integer(
        validate=validate.Range(min=1),
        dump_default=None,
    )
    updated_at = fields.DateTime(dump_default=None)
    product = fields.Nested(ProductSchema, load_default=None, dump_default=None, allow_none=True)


class AddToCartSchema(Schema):
    product_id = fields.UUID(required=True)
    quantity = fields.Integer(
        validate=validate.Range(min=1),
        load_default=1,
    )


class UpdateCartItemSchema(Schema):
    quantity = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

from marshmallow import Schema, fields, validate


class OrderItemSchema(Schema):
    id = fields.String(dump_default=None)
    order_id = fields.String(dump_default=None)
    product_id = fields.String(dump_default=None)
    quantity = fields.Integer(
        validate=validate.Range(min=1),
        dump_default=None,
    )
    unit_price = fields.String(dump_default=None)  # serialized as string to avoid Decimal JSON issues


class OrderSchema(Schema):
    id = fields.String(dump_default=None)
    user_id = fields.String(dump_default=None)
    total_amount = fields.String(dump_default=None)  # serialized as string
    status = fields.String(dump_default=None)
    created_at = fields.DateTime(dump_default=None)
    items = fields.List(fields.Nested(OrderItemSchema), load_default=list, dump_default=list)


class BuyNowSchema(Schema):
    product_id = fields.UUID(required=True)

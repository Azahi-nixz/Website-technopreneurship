from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        validate=validate.Length(min=8),
    )


class LoginSchema(Schema):
    # Accept any non-empty string — the admin account intentionally uses
    # a non-email identifier, so we validate format only on registration.
    email = fields.String(required=True, validate=validate.Length(min=1))
    password = fields.String(required=True, validate=validate.Length(min=1))

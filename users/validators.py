import re
from rest_framework import serializers


def validate_strong_password(value):
    errors = []

    if not re.search(r"[A-Za-z]", value):
        errors.append("يجب أن تحتوي كلمة المرور على حرف واحد على الأقل")

    if not re.search(r"\d", value):
        errors.append("يجب أن تحتوي كلمة المرور على رقم واحد على الأقل")

    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]", value):
        errors.append("يجب أن تحتوي كلمة المرور على رمز واحد على الأقل")

    if errors:
        raise serializers.ValidationError(errors)

    return value
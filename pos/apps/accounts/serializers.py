from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class SuperAdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        user = authenticate(username=email, password=password)
        if not user or not user.is_super_admin:
            raise serializers.ValidationError("Invalid credentials or not a super admin.")
        
        data["user"] = user
        return data
        if user.is_franchise_admin:
            user_role = 'franchise_admin'
        elif user.is_staff_member:
            user_role = 'staff_member'
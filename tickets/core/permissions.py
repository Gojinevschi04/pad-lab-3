from rest_framework import permissions


class IsTicketOwner(permissions.BasePermission):
    """Allows access only to the owner of the ticket."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

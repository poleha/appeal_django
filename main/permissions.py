from rest_framework import permissions


def create_permission_for_owner(excluded_methods=None, included_methods=None, allow=True):
    class WrappedPermission(permissions.BasePermission):

        def has_object_permission(self, request, view, obj):
            if excluded_methods and request.method in excluded_methods \
                    or included_methods and request.method not in included_methods:
                return allow
            else:
                if obj.user == request.user:
                    return allow
                else:
                    return not allow
    return WrappedPermission

IsOwnerOrReadOnly = create_permission_for_owner('GET')


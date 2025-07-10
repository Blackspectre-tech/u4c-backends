from rest_framework.permissions import BasePermission

class Is_Org(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_organization)
        

class isOrgOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class isDonorObjOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.profile == request.user.profile

class isOrgObjOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.organization == request.user.organization


class Is_Donor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and not request.user.is_organization)


# from rest_framework import permissions


# class AdminOrReadOnly(permissions.BasePermission):
#     def has_permission(self, request, view):
#         is_admin = bool(request.user and request.user.is_staff)
#         return request.method == 'GET' or is_admin



# class AuthorOnly(permissions.BasePermission):
#     def has_object_permission(self, request, view, obj):
#         if request.method in permissions.SAFE_METHODS:
#             return True 
#         else:
#             return request.user == obj.author

# class AdminOrReadOnly(permissions.BasePermission):
#     def has_permission(self, request, view):
#         is_admin = bool(request.user and request.user.is_staff)
#         return request.method == 'GET' or is_admin
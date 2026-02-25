from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from.models import User,Organization,Donor,Social,OrganizationKycItem,KycRequirement
from django.utils.translation import gettext_lazy as _
from django.contrib import admin, messages
from django.shortcuts import redirect
from django import forms
from django.urls import path, reverse
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from .utils import organization_approval_mail
from django.contrib.admin.models import LogEntry
from django.utils.html import format_html
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError






@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_time', 'content_type', 'object_repr', 'action_flag', 'change_message', 'view_object_link')
    list_filter = ('user', 'content_type', 'action_flag')
    search_fields = ('object_repr', 'change_message')

    def view_object_link(self, obj):
        if obj.action_flag == 3:  # Deletion
            return "(deleted)"
        return format_html('<a href="{}">View</a>', obj.get_admin_url())
    
    view_object_link.short_description = "View Object"






class UserProfileInline(admin.StackedInline):
    model = Donor
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'username','first_name','last_name','anonymous',
            )
        else:  # Adding a new object
                return ()
                

class OrganizationProfileInline(admin.StackedInline):
    model = Organization
    can_delete = False
    verbose_name_plural = 'Organization Profile'
    # fk_name = 'user'

    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'name','website','country','address','description',
            )
        else:  # adding new object
            return ()

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'name','website','country','address','description',
            )
        else:  # Adding a new object
                return ()








@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    ordering = ('email',)
    list_display = ('email', 'is_active', 'is_staff', 'is_organization')
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('phone_number','wallets')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_organization', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', )}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'phone_number', 'is_organization', 'is_staff', 'is_superuser'),
        }),
        
    )

    def get_readonly_fields(self, request, obj=None):
            readonly = super().get_readonly_fields(request, obj) + ('email','phone_number','last_login','wallets',)
            if not request.user.is_superuser:
                readonly = readonly + ('is_superuser','is_staff','groups', 'user_permissions','groups')
            return readonly


    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []

        if obj.is_organization:
            return [OrganizationProfileInline(self.model, self.admin_site)]
        else:
            return [UserProfileInline(self.model, self.admin_site)]




# class OrganizationAdminForm(forms.ModelForm):
#     upload_cac = forms.FileField(required=False)

#     class Meta:
#         model = Organization
#         fields = ['upload_cac']
    
#     def clean_upload_cac(self):
#         file = self.cleaned_data.get("upload_cac")
#         if file:
#             if not file.name.endswith('.pdf'):
#                 raise ValidationError("Only PDF files are allowed.")
#             if file.size > 1024 * 1024: # 1MB
#                 raise ValidationError("File size cannot exceed 1MB.")
#         return file



class KycInline(admin.StackedInline):
    model = OrganizationKycItem
    extra = 0
    can_delete = False
    fields = ['requirement','file','value','status','rejection_reason','reviewed_at','reviewed_by',]
    verbose_name_plural = 'KYC'
    # fk_name = 'user'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'requirement','file','value','reviewed_at','reviewed_by',
            )
        else:  # Adding a new object
                return ()



class SocialsInline(admin.StackedInline):
    model = Social
    extra = 1
    can_delete = False
    fields = ['instagram', 'youtube', 'twitter', 'facebook']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'instagram', 'youtube', 'twitter', 'facebook'
            )
        else:  # Adding a new object
                return ()
        
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    inlines = [SocialsInline,KycInline]

    list_display = (
        "name", 'user__email', 'kyc_status'
    )

    search_fields = ('name',)



    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'name', 'website', 'country', 'user',
                'address', 'description', 'kyc_status',
            )
            
        else:  # adding new object
            return (
                'user', 'name', 'website', 'country',
                'address', 'description',
            )


    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing 
            return (
                'name', 'website', 'country',
                'address', 'description', 'kyc_status', 'user',
            )
            
        else:  # Adding a new object
            return ()

    change_form_template = None  # set in changeform_view

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if object_id:
            # load custom template for the *edit* page
            self.change_form_template = 'admin/account/organization_changeform.html'
        else:
            self.change_form_template = None
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<uuid:pk>/approve/',
                self.admin_site.admin_view(self.approve_organization),
                name='approve_mail'
            ),
            path(
                '<uuid:pk>/disapprove/',
                self.admin_site.admin_view(self.disapprove_organization),
                name='disapprove_mail'
            ),
        ]
        return custom + urls

    def approve_organization(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        
        try:
            organization_approval_mail(organization)
            messages.success(request, "✅ kyc approval email sent.")
        except Exception as e:
            messages.error(request, f"kyc approval email failed to send: {e}")

        return redirect(reverse('admin:accounts_organization_change', args=[pk]))

    def disapprove_organization(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)

        try:
            organization_approval_mail(organization, approved=False)
        except Exception as e:
            messages.error(request, f"kyc disapproval email failed to send: {e}")
        else:
            messages.success(request, "kyc disapproval email sent.")

        # go back to change‐list
        # return redirect(reverse('admin:accounts_organization_changelist'))
        return redirect(reverse('admin:accounts_organization_change', args=[pk]))
    

    def change_view(self, request, object_id, form_url="", extra_context=None):
        organization = self.get_object(request, object_id)

        if organization:
            requirements = KycRequirement.objects.filter(is_required=True)

            for req in requirements:
                OrganizationKycItem.objects.get_or_create(
                    organization=organization,
                    requirement=req
                )

        return super().change_view(request, object_id, form_url, extra_context)

    
    def save_model(self, request, obj, form, change):
    # makes the user object an organization if saving a new model instance
        if not change:
            user = obj.user
            user.is_organization = True
            user.save()
        
        super().save_model(request, obj, form, change)




@admin.register(Donor)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user__email','username', 'user__is_active',)
    list_filter = ('user__is_active',)
    search_fields = ('user__email',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing existing object
            return ('first_name', 'last_name', 'username','user','anonymous',)
        # adding a new object
        return ()

@admin.register(KycRequirement)
class KycRequirementAdmin(admin.ModelAdmin):
    list_display = ('name','field_type', 'is_required',)
    fields = ['name','field_type', 'is_required',]
    








    
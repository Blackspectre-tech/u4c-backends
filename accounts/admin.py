from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from.models import User,Organization,Profile,Social
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
    model = Profile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'

class OrganizationProfileInline(admin.StackedInline):
    model = Organization
    can_delete = False
    verbose_name_plural = 'Organization Profile'
    # fk_name = 'user'

    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'name','website','country','address','description','cac_document',
            )
        else:  # adding new object
            return ()

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'name','website','country','address','description','cac_document',
            )
        else:  # Adding a new object
                return ()
    # readonly_fields = (
    # 'approved_at', 'disapproved_at',
    # 'approved_by', 'disapproved_by', 'disapproval_reason', 'approval_status'
    # )

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    ordering = ('email',)
    list_display = ('email', 'is_active', 'is_staff', 'is_organization')
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('phone_number',)}),
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
            readonly = super().get_readonly_fields(request, obj)
            if not request.user.is_superuser:
                readonly = readonly + ('is_superuser','is_staff','groups', 'user_permissions',)
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

class SocialsInline(admin.StackedInline):
    model = Social
    extra = 1
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
    inlines = [SocialsInline]

    list_display = (
        "name", 'user__email', 'approval_status'
    )

    list_filter = ('approval_status',)
    search_fields = ('name',)



    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            fields = (
                'name', 'website', 'country', 'user',
                'address', 'description', 'approval_status','reg_no','cac_document',
            )

            if obj.approval_status == Organization.APPROVED:
                return fields + ('approved_by', 'approverd_at')
            
            elif obj.approval_status == Organization.DISAPPROVED:
                return fields + ('disapproved_by', 'disapproverd_at', 'disapproval_reason')
            
            else:
                return fields
        else:  # adding new object
            return (
                'user', 'name', 'website', 'country',
                'address', 'description','reg_no','cac_document',
            )


    def get_readonly_fields(self, request, obj=None):

        if obj:  # Editing an existing 
            read_only = (
                'name', 'website', 'country', 'reg_no',
                'address', 'description', 'approval_status', 'user','cac_document',
            )

            if obj.approval_status == Organization.APPROVED:
                return read_only + ('approved_by', 'approverd_at')
            
            elif obj.approval_status == Organization.DISAPPROVED:
                return read_only + ('disapproved_by', 'disapproverd_at', 'disapproval_reason')
            
            else:
                return read_only
        else:  # Adding a new object
            return ()

    change_form_template = None  # set in changeform_view

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if object_id:
            # load your custom template for the *edit* page
            self.change_form_template = 'admin/account/organization_changeform.html'
        else:
            self.change_form_template = None
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:pk>/approve/',
                self.admin_site.admin_view(self.approve_organization),
                name='approve_organization'
            ),
            path(
                '<int:pk>/disapprove/',
                self.admin_site.admin_view(self.disapprove_organization),
                name='disapprove_organization'
            ),
        ]
        return custom + urls

    def approve_organization(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        if organization.approval_status == Organization.APPROVED:
            messages.warning(request, "organization already approved.")
            return redirect(reverse('admin:accounts_organization_change', args=[pk]))
        else:
            organization.approval_status = Organization.APPROVED
            organization.disapproval_reason = None
            organization.approverd_at = timezone.now()
            organization.approved_by = request.user.email
            organization.disapproved_by = None
            organization.save()
            

            try:
                organization_approval_mail(organization)
                messages.success(request, "✅ Organization approved and email sent.")
            except Exception as e:
                messages.error(request, f"Organization approved but email failed: {e}")

            
        return redirect(reverse('admin:accounts_organization_changelist'))

    def disapprove_organization(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)

        if request.method == 'GET':
            # Show a standalone form
            return render(request, 'admin/account/disapprove_organization_form.html', {'organization': organization})

        # POST: process the denial
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "You must provide a reason for disapproval.")
            return redirect(reverse('admin:disapprove_organization', args=[pk]))

        if organization.approval_status == Organization.DISAPPROVED:
            messages.warning(request, "Organization already disapproved.")
            return redirect(reverse('admin:accounts_organization_change', args=[pk]))

        organization.approval_status = Organization.DISAPPROVED
        organization.disapproval_reason = reason
        organization.disapproved_by = request.user.email
        organization.disapproverd_at = timezone.now()
        organization.approved_by = None
        organization.save()
        
        try:
            organization_approval_mail(organization, reason, approved=False)
        except Exception as e:
            messages.error(request, f"Organization disapproved but email failed: {e}")
        else:
            messages.success(request, "Organization disapproved and email sent.")

        # go back to change‐list
        return redirect(reverse('admin:accounts_organization_changelist'))



    def save_model(self, request, obj, form, change):
        user = obj.user
        user.is_organization = True
        user.save()
        
        super().save_model(request, obj, form, change)




@admin.register(Profile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user__email','username', 'user__is_active',)
    list_filter = ('user__is_active',)
    search_fields = ('user__email',)










    
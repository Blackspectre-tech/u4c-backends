from django.contrib import admin, messages
import markdown
from django.utils.safestring import mark_safe
from django.urls import path, reverse
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
# from django.core.exceptions import ValidationError
from django.forms import ValidationError as FormValidationError
from accounts.utils import project_approval_mail
from .models import Category, Project, Milestone, MilestoneImage
from accounts.utils import resize_and_upload
from core.settings import IMG
from django import forms
from django.forms.models import BaseInlineFormSet
# Register your models here.




class ProjectAdminForm(forms.ModelForm):
    upload_image = forms.ImageField(required=False, label='Upload Image')

    class Meta:
        model = Project
        fields = ['upload_image']
    

# enabling markup formating for readonly textfields for the admin panel
def render_markdown_safe(content):
    if not content:
            return "(no content)"
    html = markdown.markdown(content, extensions=["extra"])
    html = html.replace(
        "<ul>",
        '<ul style="list-style-type: disc !important; margin-left: 20px !important; padding-left: 20px !important;">'
    ).replace(
        "<ol>",
        '<ol style="list-style-type: decimal !important; margin-left: 20px !important; padding-left: 20px !important;">'
    ).replace(
        "<li>",
        '<li style="margin-bottom: 5px !important;">'
    )

    return mark_safe(f'<div class="markdown-preview">{html}</div>')


class MilestoneFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        total_goal = Decimal("0.00")

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                goal = form.cleaned_data.get('goal', Decimal("0.00"))
                total_goal += goal

        # Access the parent instance's goal (the Project's goal)
        project_goal = self.instance.goal or Decimal("0.00")

        if total_goal != project_goal:
            raise forms.ValidationError("⚠️ The total milestone goals must equal the project goal.")



class MilestoneInline(admin.StackedInline):
    model = Milestone
    extra = 1
    formset = MilestoneFormSet

    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'milestone_no', 'title', 'formatted_details', 'goal'
            )
        else:  # adding new object
            return (
                'project', 'milestone_no', 'title', 'goal', 'details',
            )
        

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'milestone_no', 'goal', 'title', 'details', 'formatted_details',
            )
        else:  # Adding a new object
                return ()
    
    def formatted_details(self, obj):
            return render_markdown_safe(content=obj.details)
    formatted_details.short_description = "Details"

    # def preview(self, obj):
    #     if obj.image:
    #         return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
    #     return "No Image"

    # preview.short_description = 'Preview'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    inlines = [MilestoneInline]
    form = ProjectAdminForm
    list_display = (
        "title", 'goal', 'approval_status', 'status', 'progress'
    )
    list_filter = ('approval_status', 'status', 'categories',)
    search_fields = ('title',)


    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            fields = (
                'organization', 'categories', 'title', 'goal', 'total_funds', 'progress', 'country', 'longitude',
                'latitude', 'approval_status', 'video',
                'formatted_problem_to_address', 'formatted_solution', 'formatted_summary',
                'formatted_description', 'image_preview','created_at', 'updated_at',
            )

            if obj.approval_status != Project.PENDING and obj.approval_status != Project.APPROVED:
                return fields + ('admin_action_by', 'admin_action_at', 'reason')
            else:
                return fields

        else:  # adding new object
            return (
                'organization', 'categories', 'title', 'goal', 'country', 'longitude',
                'latitude', 'upload_image', 'video','description', 
                'problem_to_address', 'solution', 'summary', 
            )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            fields = (
                'organization','categories', 'title', 'goal', 'country', 'longitude',
                'latitude', 'formatted_description', 'milestones', 'image', 'video', 'approval_status',
                'formatted_problem_to_address', 'formatted_solution', 'formatted_summary','image_preview',
                'created_at', 'updated_at', 'progress',
            )

            if obj.approval_status != Project.PENDING:
                return fields + ('admin_action_by', 'admin_action_at', 'reason')
            
            else:
                return fields
            
        else:  # Adding a new object
            return ()

    def formatted_solution(self, obj):
        return render_markdown_safe(content=obj.solution)
    
    def formatted_summary(self, obj):
        return render_markdown_safe(content=obj.summary)
    
    def formatted_description(self, obj):
        return render_markdown_safe(content=obj.description)

    def formatted_problem_to_address(self, obj):
        return render_markdown_safe(content=obj.problem_to_address)
    
    formatted_problem_to_address.short_description = "Problem_to_address"   
    formatted_description.short_description = "Description"
    formatted_solution.short_description = "Solution"


    change_form_template = None  # set in changeform_view

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if object_id:
            # load your custom template for the *edit* page
            self.change_form_template = 'admin/project/project_changeform.html'
        else:
            self.change_form_template = None
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:pk>/approve/',
                self.admin_site.admin_view(self.approve_project),
                name='projects_project_approve'
            ),
            path(
                '<int:pk>/deny/',
                self.admin_site.admin_view(self.disapprove_project),
                name='projects_project_deny'
            ),
            path(
                '<int:pk>/flag/',
                self.admin_site.admin_view(self.flag_project),
                name='flag_project_url'
            ),
        ]
        return custom + urls

    def approve_project(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if project.approval_status == Project.APPROVED:
            messages.warning(request, "Project already approved.")
        else:
            project.approval_status = Project.APPROVED
            project.approverd_at = timezone.now()
            project.admin_action_by = request.user.email
            project.admin_action_at = timezone.now()
            project.save()
            

        try:
            project_approval_mail(project)
            messages.success(request, "✅ Project approved and email sent.")
        except Exception as e:
            messages.error(request, f"project approved but email failed: {e}")
            
        return redirect(reverse('admin:projects_project_changelist'))

    def disapprove_project(self, request, pk, flag = False):
        project = get_object_or_404(Project, pk=pk)

        if request.method == 'GET':
            # Show a standalone form
            return render(request, 'admin/project/deny_project_form.html', {'project': project, 'flag':flag})

        # POST: process the denial
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "You must provide a reason for disapproval.")
            return redirect(reverse('admin:projects_project_deny', args=[pk]))

        if project.approval_status == Project.DISAPPROVED:
            messages.warning(request, "Project already disapproved.")
            return redirect(reverse('admin:projects_project_change', args=[pk]))

        project.approval_status = Project.DISAPPROVED
        project.reason = reason
        project.admin_action_by = request.user.email
        project.admin_action_at = timezone.now()
        project.save()

        try:
            project_approval_mail(project, reason, approved=False)
        except Exception as e:
            messages.error(request, f"Disapproved but email failed: {e}")
        else:
            messages.success(request, "Project disapproved and email sent.")

        # go back to change‐list
        return redirect(reverse('admin:projects_project_changelist'))
    

    def flag_project(self, request, pk, flag = True):
        project = get_object_or_404(Project, pk=pk)
        
        if request.method == 'GET':
            # Show a standalone form
            return render(request, 'admin/project/deny_project_form.html', {'project': project, 'flag':flag})

        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "you must provide a reason for flagging the project.")
            return redirect(reverse('admin:flag_project_url', args=[pk]))

        if project.approval_status == project.FLAGGED:
            messages.warning(request, "Project already flagged.")
            return redirect(reverse('admin:flag_project_url', args=[pk]))

        project.approval_status = project.FLAGGED
        project.reason = reason
        project.admin_action_by = request.user.email
        project.admin_action_at = timezone.now()
        project.save()

        try:
            project_approval_mail(project, reason, approved=False)
        except Exception as e:
            messages.error(request, f"Flagged but email failed: {e}")
        else:
            messages.success(request, "Project Flagged and email sent.")

        # go back to change‐list
        return redirect(reverse('admin:projects_project_changelist'))


    def save_model(self, request, obj, form, change):

        image_file = form.cleaned_data.get('upload_image')
        if image_file:
            image_url = resize_and_upload(image_file, IMG['projects'] + str(obj.title))
            obj.image = image_url
        super().save_model(request, obj, form, change)




class MilestoneimagesAdminForm(forms.ModelForm):
    upload_image = forms.ImageField(required=False, label='Upload Image')

    class Meta:
        model = MilestoneImage
        fields = ['upload_image']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        image_file = self.cleaned_data.get('upload_image')

        if image_file:
            
            image_url = resize_and_upload(image_file, IMG['milestones'] + instance.milestone.title)
            instance.image = image_url

        if commit:
            instance.save()
        return instance



class MilestoneImagesInline(admin.StackedInline):
    model = MilestoneImage
    extra = 1
    form = MilestoneimagesAdminForm

    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'image_url', 'image_preview','upload_image'
            )
        else:  # adding new object
            return ('upload_image',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'image_url','image_preview'
            )
        else:  # Adding a new object
                return ()


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    inlines = [MilestoneImagesInline]
    list_display = (
        "project__title", 'project__organization__name','milestone_no', 'goal', 'progress',
    )
    search_fields = ('project__title',)

    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'project', 'milestone_no', 'title', 'goal', 'status', 'formatted_details',
            )
        else:  # adding new object
            return (
                'project', 'milestone_no', 'title', 'goal', 'details',
            )


    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'project', 'milestone_no', 'title', 'goal', 'status', 'formatted_details',
            )
        else:  # Adding a new object
            return ()



    def formatted_details(self, obj):
            return render_markdown_safe(content=obj.details)
    formatted_details.short_description = "Details"
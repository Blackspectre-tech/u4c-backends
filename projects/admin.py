from django.contrib import admin, messages
import markdown
from django.utils.safestring import mark_safe
from django.urls import path, reverse
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.forms import ValidationError as FormValidationError
from accounts.utils import project_approval_mail
from .models import Project, Milestone, MilestoneImage, Donation
from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html
from django.core.cache import cache
from contract.blockchain import contract, send_owner_tx


# class ProjectAdminForm(forms.ModelForm):
#     upload_image = forms.ImageField(required=False, label='Upload Image')

#     class Meta:
#         model = Project
#         fields = ['upload_image']



# admin.site.register(Donation)
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'project', 'amount' ,
    )
    list_filter = ('project',)
    search_fields = ['project__title',]

    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'project', 'amount','wallet' ,'refundable',
            )
        else:  # adding new object
            return (
                
            )


    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'project', 'amount','wallet' ,'refundable',
            )
        else:  # Adding a new object
            return ()



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

        # for form in self.forms:
        #     if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
        #         goal = form.cleaned_data.get('goal', Decimal("0.00"))
        #         total_goal += goal

        # Access the parent instance's goal (the Project's goal)
        # project_goal = self.instance.goal or Decimal("0.00")

        if len(self.forms)>3:
            raise forms.ValidationError("projects are limited to a maximum of 3 milestones")



class MilestoneInline(admin.StackedInline):
    model = Milestone
    extra = 1
    formset = MilestoneFormSet

    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'milestone_no', 'title', 'formatted_details', 'goal', 'status',
            )
        else:  # adding new object
            return (
                'project', 'milestone_no', 'title', 'goal', 'details',
            )
        

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'milestone_no', 'goal', 'title', 'details', 'formatted_details','status',
            )
        else:  # Adding a new object
                return ()
    
    def formatted_details(self, obj):
            return render_markdown_safe(content=obj.details)
    formatted_details.short_description = "Details"



@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [MilestoneInline]
    list_display = (
        "title",'organization__name', 'goal', 'approval_status', 'status', 'progress_percenage','deadline',
    )
    list_filter = ('approval_status', 'status', 'categories',)
    search_fields = ('title',)

    change_form_template = None  # set in changeform_view

    # -------------------------
    # Use fieldsets so Jazmin shows collapsible sections
    # -------------------------
    def get_fieldsets(self, request, obj=None):
        """
        Return fieldsets for add / change pages.
        When editing and deployed + contract_id present, add a collapsible 'Contract Info' fieldset.
        """
        # Base fieldset used on change page (edit)
        base_fields = [
            'organization', 'categories', 'title', 'goal', 'total_funds', 'progress_percenage',
            'country', 'approval_status', 'formatted_description', 'image', 'created_at', 'updated_at',
            'formatted_summary', 'deployed', 'wallet_address', 'duration_in_days', 'deadline','contract_id','status',
        ]

        # If adding a new project, show a simpler layout
        if obj is None:
            return (
                (None, {'fields': ('organization', 'categories', 'title', 'goal', 'country', 'image', 'description', 'summary')}),
            )

        # Change page: build main fieldset (readonly fields handled separately)
        fieldsets = [
            (None, {'fields': tuple(base_fields)}),
        ]

        # If deployed and has contract_id, add collapsible Contract Info fieldset
        if getattr(obj, "deployed", False) and getattr(obj, "contract_id", None) is not None:
            fieldsets.append(
                ("Contract Info", {
                    'fields': ('onchain_info',),
                    'classes': ('collapse',),   # makes it collapsible in Django admin / Jazmin
                    'description': "On-chain details pulled from the MilestoneCrowdfund contract (read-only)."
                })
            )

        # If project is not in PENDING/APPROVED states we want to show admin action fields in a separate fieldset
        if obj.approval_status != Project.PENDING and obj.approval_status != Project.APPROVED:
            fieldsets.append(
                ("Admin Action", {'fields': ('admin_action_by', 'admin_action_at', 'reason')})
            )

        return tuple(fieldsets)

    # -------------------------
    # readonly fields
    # -------------------------
    def get_readonly_fields(self, request, obj=None):
        readonly = (
            'organization','categories', 'title', 'goal', 'country', 'formatted_description', 'milestones', 'image',
            'approval_status', 'formatted_summary', 'created_at', 'updated_at', 'progress_percenage',
            'deployed', 'wallet_address',  'duration_in_days', 'deadline', 'total_funds','contract_id','status',
        )

        # Make sure onchain_info is readonly when displayed
        if obj and getattr(obj, "deployed", False) and getattr(obj, "contract_id", None) is not None:
            readonly = readonly + ('onchain_info',)

        if obj and obj.approval_status != Project.PENDING:
            return readonly + ('admin_action_by', 'admin_action_at', 'reason')
        return readonly if obj else ()

    # -------------------------
    # Formatting helpers
    # -------------------------
    def formatted_summary(self, obj):
         return render_markdown_safe(content=obj.summary)

    def formatted_description(self, obj):
        return render_markdown_safe(content=obj.description)

    formatted_description.short_description = "Description"

    # -------------------------
    # On-chain info (read-only field)
    # -------------------------
    def onchain_info(self, obj):
        """
        Read-only HTML displaying getCampaignCore and milestones.
        Only shown when obj.deployed == True and obj.contract_id is not None.
        Cached for 30 seconds.
        """
        if obj is None or not getattr(obj, "deployed", False) or obj.contract_id is None:
            return format_html("<i>Not deployed on-chain</i>")

        contract_id = obj.contract_id
        cache_key = f"onchain_campaign_{contract_id}"
        core = cache.get(cache_key)

        status_dict = {
            0:'Fundraising',
            1:'Succeeded',
            2:'Failed',
            3:'Cancelled',
        }
        curreny_dict = {
            0:'ETH',
            1:'ERC20',
        }

        if not core:
            try:
                core = contract.functions.getCampaignCore(contract_id).call()
                cache.set(cache_key, core, 30)  # cache for 30s
            except Exception as e:
                # Friendly error for admin UI
                return format_html(
                    "<div style='color:#b33;'>Could not fetch on-chain info (contract_id: {}). Error: {}</div>",
                    contract_id,
                    str(e)
                )

        try:
            # Unpack core tuple
            creator, currencyType, token, goal, pledged, deadline, state, milestoneCount = core

            # Build a small HTML table
            rows = [
                ("Contract ID", contract_id),
                ("Creator", creator),
                ("CurrencyType (ETH,ERC20)", curreny_dict[int(currencyType)]),
                ("Token", token if token and token != "0x0000000000000000000000000000000000000000" else "ETH"),
                ("Goal ($)",str(Decimal(goal) / (Decimal(10) ** 6))),   #Decimal(str(tipAmount)) if tipAmount != 0 else Decimal(0) #str(goal)),
                ("Pledged ($)", str(Decimal(pledged) / (Decimal(10) ** 6))), #str(pledged)),
                ("Deadline", str(self._timestamp_to_dt(deadline))),
                ("State", status_dict[int(state)]),
                ("Milestone count", int(milestoneCount)),
            ]

            html = "<table style='border-collapse:collapse;'>"
            for k, v in rows:
                html += (
                    "<tr>"
                    f"<td style='padding:4px 8px; font-weight:600; vertical-align:top; border-bottom:1px solid #eee'>{k}</td>"
                    f"<td style='padding:4px 8px; border-bottom:1px solid #eee'>{v}</td>"
                    "</tr>"
                )
            html += "</table>"

            # Optionally show milestones (if any)
            if int(milestoneCount) > 0:
                html += "<h4 style='margin-top:8px;margin-bottom:6px'>Milestones</h4>"
                html += "<table style='border-collapse:collapse;width:100%'>"
                html += "<tr><th style='text-align:left;padding:4px 8px;'>#</th><th style='text-align:left;padding:4px 8px;'>Name</th><th style='text-align:left;padding:4px 8px;'>Amount</th><th style='text-align:left;padding:4px 8px;'>Approved</th><th style='text-align:left;padding:4px 8px;'>Released</th></tr>"
                for i in range(int(milestoneCount)):
                    try:
                        name, amount, approved, released = contract.functions.getMilestone(contract_id, i).call()
                        html += (
                            "<tr>"
                            f"<td style='padding:4px 8px; vertical-align:top'>{i}</td>"
                            f"<td style='padding:4px 8px; vertical-align:top'>{name}</td>"
                            f"<td style='padding:4px 8px; vertical-align:top'>{str(Decimal(amount) / (Decimal(10) ** 6))}</td>"
                            f"<td style='padding:4px 8px; vertical-align:top'>{approved}</td>"
                            f"<td style='padding:4px 8px; vertical-align:top'>{released}</td>"
                            "</tr>"
                        )
                    except Exception:
                        html += (
                            "<tr>"
                            f"<td style='padding:4px 8px;'>{i}</td>"
                            f"<td colspan='4' style='padding:4px 8px;color:#888;'>Could not read milestone #{i}</td>"
                            "</tr>"
                        )
                html += "</table>"

            return format_html(html)

        except Exception as exc:
            return format_html("<div style='color:#b33;'>Error formatting on-chain info: {}</div>", str(exc))

    onchain_info.short_description = "On-chain Campaign (getCampaignCore + milestones preview)"

    def _timestamp_to_dt(self, ts):
        try:
            return timezone.datetime.fromtimestamp(int(ts), tz=timezone.get_default_timezone())
        except Exception:
            return ts

    # -------------------------
    # changeform template override 
    # -------------------------
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if object_id:
            # load your custom template for the *edit* page
            self.change_form_template = 'admin/project/project_changeform.html'
        else:
            self.change_form_template = None
        return super().changeform_view(request, object_id, form_url, extra_context)

    # -------------------------
    # Custom admin urls + actions 
    # -------------------------
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
                '<int:pk>/finalize/',
                self.admin_site.admin_view(self.finalize_project_onchain),
                name='finalize_project_url'
            ),
            path(
                '<int:pk>/approve_milestone/',
                self.admin_site.admin_view(self.approve_milestone_onchain),
                name='approve_milestone_url'
            ),
        ]
        return custom + urls

    def approve_project(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        org = project.organization
        if project.approval_status == Project.APPROVED:
            messages.warning(request, "Project already approved.")
            return redirect(reverse('admin:projects_project_change', args=[pk]))
        elif project.deployed:
            messages.warning(request, "can't alter state of deployed project.")
            return redirect(reverse('admin:projects_project_change', args=[pk]))
        elif org.projects.filter(approval_status=Project.APPROVED,deployed=False).count() > 0:
            messages.warning(request, "organization has an approved project that hasn't been deployed.")
            return redirect(reverse('admin:projects_project_change', args=[pk]))
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

        if project.deployed:
            messages.warning(request, "cant alter state of deployed project.")
            return redirect(reverse('admin:projects_project_change', args=[pk]))

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
        return redirect(reverse('admin:projects_project_changelist'))

    def finalize_project_onchain(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        try:
            if project.status != Project.Funding:
                messages.warning(request, f"Project State Already changed")
                return redirect(reverse('admin:projects_project_change', args=[pk]))
           
            if project.deployed:
            
                campaign_id = project.contract_id
                tx_hash = send_owner_tx(contract.functions.finalize(campaign_id))

                messages.success(request, f"Project finalized, tx_hash: {tx_hash}")
                return redirect(reverse('admin:projects_project_change', args=[pk]))
            else:
                messages.warning(request, f"project not on-chain")
                return redirect(reverse('admin:projects_project_change', args=[pk]))
            
        except Exception as e:
            # ContractLog.objects.create(
            #     data=traceback.format_exc(),
            #     error=str(e),
            # )  
            messages.warning(request, f"Error: {e}")
            return redirect(reverse('admin:projects_project_change', args=[pk]))
        


    def approve_milestone_onchain(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if project.deployed:
            try:
                active_milestone = project.milestones.filter(status=Milestone.COMPLETED,approved=False).first()
                if active_milestone:
                    index = active_milestone.milestone_no -1
                    campaign_id = project.contract_id
                    tx_hash = send_owner_tx(contract.functions.approveMilestone(campaign_id, index))
                    
                    messages.success(request, f"milestone approved, tx_hash: {tx_hash}")
                    return redirect(reverse('admin:projects_project_change', args=[pk]))
                else:
                    messages.warning(request, f"project has no unapproved completed milestone")
                    return redirect(reverse('admin:projects_project_change', args=[pk]))
            except Exception as e:
                # ContractLog.objects.create(
                #     data=traceback.format_exc(),
                #     error=str(e),
                # )  
                messages.warning(request, f"Error: {e}")
                return redirect(reverse('admin:projects_project_change', args=[pk]))
        else:
            messages.warning(request, f"project not on-chain")
            return redirect(reverse('admin:projects_project_change', args=[pk]))


class MilestoneImagesInline(admin.StackedInline):
    model = MilestoneImage
    extra = 1

    def get_fields(self, request, obj=None):
        if obj:  # editing existing object
            return (
                'image',
            )
        else:  # adding new object
            return ('image',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return (
                'image',
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


    
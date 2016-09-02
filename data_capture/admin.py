from django.contrib import admin
from django.db import models
from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib import messages

from . import email
from .schedules import registry
from .models import SubmittedPriceList, SubmittedPriceListRow


class SubmittedPriceListRowInline(admin.TabularInline):
    model = SubmittedPriceListRow

    can_delete = False

    fields = (
        'labor_category',
        'education_level',
        'min_years_experience',
        'hourly_rate_year1',
        'current_price',
        'sin',
        'is_muted',
    )

    readonly_fields = ()

    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput}
    }

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_approved:
            return self.fields
        return self.readonly_fields


def approve(modeladmin, request, queryset):
    unapproved = queryset.filter(is_approved=False)
    count = unapproved.count()
    for price_list in unapproved:
        price_list.approve()
        email.price_list_approved(price_list)

    messages.add_message(
        request,
        messages.INFO,
        '{} price list(s) have been approved and added to CALC.'.format(
            count
        )
    )


approve.short_description = (
    'Approve selected price lists (add their data to CALC)'
)


def unapprove(modeladmin, request, queryset):
    approved = queryset.filter(is_approved=True)
    count = approved.count()
    for price_list in approved:
        price_list.unapprove()
        email.price_list_unapproved(price_list)
    messages.add_message(
        request,
        messages.INFO,
        '{} price list(s) have been unapproved and removed from CALC.'.format(
            count
        )
    )


unapprove.short_description = (
    'Unapprove selected price lists (remove their data from CALC)'
)


class UndeletableModelAdmin(admin.ModelAdmin):
    '''
    Represents a model admin UI that offers no way of deleting
    instances. This is useful to ensure accidental data loss, especially
    when we want to keep it around for historical/data provenance purposes.
    '''

    # http://stackoverflow.com/a/25813184/2422398
    def get_actions(self, request):
        actions = super().get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SubmittedPriceList)
class SubmittedPriceListAdmin(UndeletableModelAdmin):
    list_display = ('contract_number', 'vendor_name', 'submitter',
                    'created_at', 'is_approved')

    actions = [approve, unapprove]

    fields = (
        'contract_number',
        'vendor_name',
        'is_small_business',
        'schedule_title',
        'contractor_site',
        'contract_year',
        'contract_start',
        'contract_end',
        'submitter',
        'created_at',
        'updated_at',
        'is_approved',
        'current_status',
    )

    readonly_fields = (
        'schedule_title',
        'created_at',
        'updated_at',
        'is_approved',
        'current_status'
    )

    list_filter = (
        'is_approved',
    )

    inlines = [
        SubmittedPriceListRowInline
    ]

    def current_status(self, instance):
        if instance.is_approved:
            return mark_safe(
                "<span style=\"color: green\">"
                "This price list has been approved, so its data is now "
                "in CALC. To unapprove it, you will need to use the "
                "'Unapprove selected price lists' action from the "
                "<a href=\"..\">list view</a>. Note also that in order "
                "to edit the fields in this price list, you will first "
                "need to unapprove it."
            )
        return mark_safe(
            "<span style=\"color: red\">"
            "This price list is not currently approved, so its data is "
            "not in CALC. To approve it, you will need to use the "
            "'Approve selected price lists' action from the "
            "<a href=\"..\">list view</a>."
        )

    def schedule_title(self, instance):
        return registry.get_class(instance.schedule).title

    schedule_title.short_description = 'Schedule'

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_approved:
            return self.fields
        return self.readonly_fields


@admin.register(SubmittedPriceListRow)
class SubmittedPriceListRowAdmin(UndeletableModelAdmin):
    list_display = (
        'contract_number',
        'vendor_name',
        'labor_category',
        'education_level',
        'min_years_experience',
        'hourly_rate_year1',
        'current_price',
        'sin',
        'is_muted',
    )

    list_editable = (
        'is_muted',
    )

    def contract_number(self, obj):
        url = reverse('admin:data_capture_submittedpricelist_change',
                      args=(obj.price_list.id,))
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.price_list.contract_number
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(price_list__is_approved=False)

    def vendor_name(self, obj):
        return obj.price_list.vendor_name

    def has_add_permission(self, request):
        return False

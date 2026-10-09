from django.contrib import admin
from .models import (
    Employee,
    EmployeeSalaryHistory,
    EmployeeChangeHistory,
)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "name",
        "joining_date",
        "designation",
        "department",
        "current_ctc",
    )
    search_fields = ("employee_id", "name", "department")
    list_filter = ("department", "designation")


@admin.register(EmployeeSalaryHistory)
class EmployeeSalaryHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "ctc",
        "effective_from",
        "effective_to",
        "reason",
        "idempotency_key",
        "created_at",
    )
    search_fields = (
        "employee__employee_id",
        "employee__name",
        "idempotency_key",
    )
    list_filter = ("effective_from",)


@admin.register(EmployeeChangeHistory)
class EmployeeChangeHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "field_name",
        "old_value",
        "new_value",
        "effective_date",
        "changed_by",
        "correlation_id",
    )
    search_fields = (
        "employee__employee_id",
        "employee__name",
        "field_name",
        "correlation_id",
    )
    list_filter = ("field_name", "effective_date")

from decimal import Decimal
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Employee(models.Model):
    """
    Stores the current information of an employee.
    Historical salary information is stored separately
    in EmployeeSalaryHistory.
    """

    employee_id = models.CharField(
        max_length=50,
        unique=True,
    )

    name = models.CharField(
        max_length=150,
    )

    joining_date = models.DateField()

    designation = models.CharField(
        max_length=150,
    )

    department = models.CharField(
        max_length=150,
    )

    current_ctc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.employee_id} - {self.name}"


class EmployeeSalaryHistory(models.Model):
    """
    Stores every salary/CTC version of an employee.

    effective_to = NULL means that this salary
    is currently active.
    """

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="salary_history",
    )

    ctc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
    )
    idempotency_key = models.CharField(
       max_length=100,
       null=True,
       blank=True,
       unique=True,
)

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_salary_history",
    )

    class Meta:
        ordering = ["-effective_from"]
        indexes = [
            models.Index(
                fields=[
                    "employee",
                    "effective_from",
                    "effective_to",
                ]
            ),
        ]

    def clean(self):
        if self.ctc <= Decimal("0.00"):
            raise ValidationError(
                "CTC must be greater than zero."
            )

        if self.effective_to is not None:
            if self.effective_to < self.effective_from:
                raise ValidationError(
                    "Effective-to date cannot be before effective-from date."
                )

        if self.effective_from < self.employee.joining_date:
            raise ValidationError(
                "Salary effective date cannot be before employee joining date."
            )

    def __str__(self):
        return (
            f"{self.employee.employee_id} - "
            f"{self.ctc} - "
            f"{self.effective_from}"
        )


class EmployeeChangeHistory(models.Model):
    """
    Stores an audit/history record whenever important
    employee information is changed.

    This answers:
    Who changed what?
    When was it changed?
    Why was it changed?
    """

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="change_history",
    )

    field_name = models.CharField(
        max_length=100,
    )

    old_value = models.TextField(
        null=True,
        blank=True,
    )

    new_value = models.TextField(
        null=True,
        blank=True,
    )

    effective_date = models.DateField(
        null=True,
        blank=True,
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
    )

    changed_at = models.DateTimeField(
        auto_now_add=True,
    )
    correlation_id = models.UUIDField(
    default=uuid.uuid4,
    editable=False,
    db_index=True,
)

    changed_by = models.CharField(
    max_length=150,
    blank=True,
    null=True,
)
    

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return (
            f"{self.employee.employee_id} - "
            f"{self.field_name} - "
            f"{self.changed_at}"
        )

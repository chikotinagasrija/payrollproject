from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from payroll.models import (
    Employee,
    EmployeeSalaryHistory,
    EmployeeChangeHistory,
)


class SalaryHistoryService:
    """
    Handles employee salary/CTC updates while preserving
    complete salary history and audit information.
    """

    @staticmethod
    @transaction.atomic
    def update_salary(
        employee,
        new_ctc,
        effective_from,
        reason="",
        changed_by="",
        idempotency_key=None,
        correlation_id=None
    ):

        """
        Update employee salary and preserve the previous
        salary record.

        All database changes happen inside one transaction.
        """

        # -------------------------------------------------
        # 1. Validate employee
        # -------------------------------------------------

        if not isinstance(employee, Employee):
            raise ValidationError(
                "Invalid employee."
            )

        # -------------------------------------------------
        # 2. Validate CTC
        # -------------------------------------------------

        if new_ctc <= 0:
            raise ValidationError(
                "CTC must be greater than zero."
            )

        # -------------------------------------------------
        # 3. Validate effective date
        # -------------------------------------------------

        if effective_from < employee.joining_date:
            raise ValidationError(
                "Salary effective date cannot be "
                "before employee joining date."
            )
        if idempotency_key:
          existing_salary = (
            EmployeeSalaryHistory.objects
            .filter(idempotency_key=idempotency_key)
            .first()
        )

        if existing_salary:
            return existing_salary

        # -------------------------------------------------
        # 4. Lock existing salary records
        # -------------------------------------------------

        salary_records = list(
            EmployeeSalaryHistory.objects
            .select_for_update()
            .filter(employee=employee)
            .order_by("effective_from")
        )

        # -------------------------------------------------
        # 5. Check for overlapping salary periods
        # -------------------------------------------------

        overlapping_records = (
            EmployeeSalaryHistory.objects
            .select_for_update()
            .filter(
                employee=employee,
                effective_from__lte=effective_from,
            )
            .filter(
                Q(effective_to__isnull=True)
                | Q(effective_to__gte=effective_from)
            )
        )

        # We allow the current active record to be closed
        # and replaced by the new record.
        current_record = (
            EmployeeSalaryHistory.objects
            .select_for_update()
            .filter(
                employee=employee,
                effective_to__isnull=True,
            )
            .order_by("-effective_from")
            .first()
        )

        for record in overlapping_records:

            if current_record is not None:

                if record.pk == current_record.pk:
                    continue

            raise ValidationError(
                "Salary period overlaps with an existing "
                "salary history record."
            )

        # -------------------------------------------------
        # 6. Determine previous salary
        # -------------------------------------------------

        old_ctc = None

        if current_record:

            # New salary cannot start before or on the
            # current salary's start date.
            if (
                effective_from
                <= current_record.effective_from
            ):
                raise ValidationError(
                    "New salary effective date must be "
                    "after the current salary effective date."
                )

            old_ctc = current_record.ctc

            # -------------------------------------------------
            # 7. Close previous salary period
            # -------------------------------------------------

            from datetime import timedelta

            current_record.effective_to = (
                effective_from - timedelta(days=1)
            )

            current_record.save(
                update_fields=["effective_to"]
            )

        # -------------------------------------------------
        # 8. Create new salary history record
        # -------------------------------------------------

        new_salary = (
            EmployeeSalaryHistory.objects.create(
                employee=employee,
                ctc=new_ctc,
                effective_from=effective_from,
                effective_to=None,
                reason=reason,
                created_by=None,
                idempotency_key=idempotency_key,
            )
        )

        # -------------------------------------------------
        # 9. Update current employee CTC
        # -------------------------------------------------

        employee.current_ctc = new_ctc

        employee.save(
            update_fields=[
                "current_ctc",
                "updated_at",
            ]
        )

        # -------------------------------------------------
        # 10. Create audit/history record
        # -------------------------------------------------

        EmployeeChangeHistory.objects.create(
            employee=employee,
            field_name="current_ctc",
            old_value=(
                str(old_ctc)
                if old_ctc is not None
                else None
            ),
            new_value=str(new_ctc),
            effective_date=effective_from,
            reason=reason,
            changed_by=changed_by,
            correlation_id=correlation_id,
        )

        # -------------------------------------------------
        # 11. Return new salary record
        # -------------------------------------------------
        print(
           "NEW SALARY RECORD:",
            new_salary.pk,
            new_salary.employee.employee_id,
            new_salary.employee_id,
            new_salary.ctc,
)


        return new_salary
    @staticmethod
    def get_salary_for_date(employee, target_date):
        salary = (
            EmployeeSalaryHistory.objects
            .filter(
                employee=employee,
                effective_from__lte=target_date
            )
            .filter(
                Q(effective_to__isnull=True) |
                Q(effective_to__gte=target_date)
            )
            .order_by("-effective_from")
            .first()
        )

        if not salary:
            raise ValidationError(
                "No salary found for the requested date."
            )

        return salary

from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from payroll.models import (
    Employee,
    EmployeeSalaryHistory,
    EmployeeChangeHistory,
)
from payroll.services.salary_history_service import SalaryHistoryService


class SalaryHistoryServiceTestCase(TestCase):

    def setUp(self):
        self.employee = Employee.objects.create(
            employee_id="TEST001",
            name="Test Employee",
            joining_date=date(2026, 1, 1),
            designation="Software Engineer",
            department="Engineering",
            current_ctc=500000,
        )

    def test_invalid_employee(self):
        with self.assertRaises(ValidationError):
            SalaryHistoryService.update_salary(
                employee="invalid",
                new_ctc=600000,
                effective_from=date(2026, 10, 7),
            )

    def test_ctc_must_be_greater_than_zero(self):
        with self.assertRaisesMessage(
            ValidationError,
            "CTC must be greater than zero.",
        ):
            SalaryHistoryService.update_salary(
                employee=self.employee,
                new_ctc=0,
                effective_from=date(2026, 10, 7),
            )

    def test_effective_date_cannot_be_before_joining_date(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Salary effective date cannot be before employee joining date.",
        ):
            SalaryHistoryService.update_salary(
                employee=self.employee,
                new_ctc=600000,
                effective_from=date(2025, 12, 1),
            )

    def test_salary_update_creates_salary_history(self):
        salary = SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=600000,
            effective_from=date(2026, 10, 7),
            reason="Annual revision",
            changed_by="Priya",
            idempotency_key="TEST-IDEMPOTENCY-001",
        )

        self.assertEqual(salary.employee, self.employee)
        self.assertEqual(salary.ctc, 600000)
        self.assertEqual(salary.effective_from, date(2026, 10, 7))

    def test_employee_current_ctc_is_updated(self):
        SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=600000,
            effective_from=date(2026, 10, 7),
            idempotency_key="TEST-CTC-001",
        )

        self.employee.refresh_from_db()

        self.assertEqual(self.employee.current_ctc, 600000)

    def test_idempotency_returns_existing_salary(self):
        first_salary = SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=600000,
            effective_from=date(2026, 10, 7),
            idempotency_key="TEST-IDEMPOTENCY-002",
        )

        second_salary = SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=600000,
            effective_from=date(2026, 10, 7),
            idempotency_key="TEST-IDEMPOTENCY-002",
        )

        self.assertEqual(first_salary.id, second_salary.id)

        self.assertEqual(
            EmployeeSalaryHistory.objects.filter(
                idempotency_key="TEST-IDEMPOTENCY-002"
            ).count(),
            1,
        )

    def test_first_salary_update_creates_audit_history(self):
        correlation_id = "12345678-1234-5678-1234-567812345678"

        SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=600000,
            effective_from=date(2026, 10, 7),
            reason="Annual revision",
            changed_by="Priya",
            idempotency_key="TEST-AUDIT-001",
            correlation_id=correlation_id,
        )

        history = EmployeeChangeHistory.objects.get(
            employee=self.employee
        )

        self.assertEqual(history.field_name, "current_ctc")
        self.assertIsNone(history.old_value)
        self.assertEqual(history.new_value, "600000")
        self.assertEqual(history.changed_by, "Priya")
        self.assertEqual(str(history.correlation_id), correlation_id)

    def test_previous_salary_period_is_closed(self):
        first_salary = SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=500000,
            effective_from=date(2026, 1, 1),
            idempotency_key="TEST-PERIOD-001",
        )

        second_salary = SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=600000,
            effective_from=date(2026, 10, 7),
            idempotency_key="TEST-PERIOD-002",
        )

        first_salary.refresh_from_db()

        self.assertEqual(first_salary.effective_to, date(2026, 10, 6))
        self.assertIsNone(second_salary.effective_to)

    def test_new_salary_date_cannot_be_before_current_salary_date(self):
        SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=500000,
            effective_from=date(2026, 5, 1),
            idempotency_key="TEST-DATE-001",
        )

        with self.assertRaisesMessage(
            ValidationError,
            "New salary effective date must be after the current salary effective date.",
        ):
            SalaryHistoryService.update_salary(
                employee=self.employee,
                new_ctc=600000,
                effective_from=date(2026, 5, 1),
                idempotency_key="TEST-DATE-002",
            )

    def test_get_salary_for_date_returns_correct_salary(self):
        SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=500000,
            effective_from=date(2026, 1, 1),
            idempotency_key="TEST-LOOKUP-001",
        )

        SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=600000,
            effective_from=date(2026, 7, 1),
            idempotency_key="TEST-LOOKUP-002",
        )

        salary = SalaryHistoryService.get_salary_for_date(
            employee=self.employee,
            target_date=date(2026, 5, 1),
        )

        self.assertEqual(salary.ctc, 500000)

    def test_get_salary_for_date_returns_latest_salary(self):
        SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=500000,
            effective_from=date(2026, 1, 1),
            idempotency_key="TEST-LATEST-001",
        )

        SalaryHistoryService.update_salary(
            employee=self.employee,
            new_ctc=600000,
            effective_from=date(2026, 7, 1),
            idempotency_key="TEST-LATEST-002",
        )

        salary = SalaryHistoryService.get_salary_for_date(
            employee=self.employee,
            target_date=date(2026, 8, 1),
        )

        self.assertEqual(salary.ctc, 600000)

    def test_get_salary_for_date_when_no_salary_exists(self):
        with self.assertRaisesMessage(
            ValidationError,
            "No salary found for the requested date.",
        ):
            SalaryHistoryService.get_salary_for_date(
                employee=self.employee,
                target_date=date(2025, 12, 1),
            )
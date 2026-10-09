from decimal import Decimal

from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from payroll.services.salary_structure_service import (
    SalaryStructureService,
)


class SalaryStructureServiceTests(SimpleTestCase):
    """
    Tests for salary calculation service.
    """

    def test_annual_ctc(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("6")
            )
        )

        self.assertEqual(
            result["annual_ctc"],
            Decimal("600000.00")
        )

    def test_monthly_ctc(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("6")
            )
        )

        self.assertEqual(
            result["monthly_ctc"],
            Decimal("50000.00")
        )

    def test_basic(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("6")
            )
        )

        self.assertEqual(
            result["salary_structure"]["basic"],
            Decimal("25000.00")
        )

    def test_hra(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("6")
            )
        )

        self.assertEqual(
            result["salary_structure"]["hra"],
            Decimal("12500.00")
        )

    def test_special_allowance(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("6")
            )
        )

        self.assertEqual(
            result["salary_structure"]["special_allowance"],
            Decimal("12500.00")
        )

    def test_components_reconcile(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("6")
            )
        )

        structure = result["salary_structure"]

        total = (
            structure["basic"]
            + structure["hra"]
            + structure["special_allowance"]
        )

        self.assertEqual(
            total,
            result["monthly_ctc"]
        )

    def test_decimal_lpa(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("4.5")
            )
        )

        self.assertEqual(
            result["annual_ctc"],
            Decimal("450000.00")
        )

        self.assertEqual(
            result["monthly_ctc"],
            Decimal("37500.00")
        )

    def test_three_lpa(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("3")
            )
        )

        self.assertEqual(
            result["annual_ctc"],
            Decimal("300000.00")
        )

        self.assertEqual(
            result["monthly_ctc"],
            Decimal("25000.00")
        )

    def test_ten_lpa(self):

        result = (
            SalaryStructureService
            .generate_salary_structure(
                Decimal("10")
            )
        )

        self.assertEqual(
            result["annual_ctc"],
            Decimal("1000000.00")
        )

        self.assertEqual(
            result["monthly_ctc"],
            Decimal("83333.33")
        )


class SalaryStructureAPITests(APITestCase):
    """
    Tests for Salary Structure API.
    """

    def test_empty_request(self):

        response = self.client.post(
            reverse(
                "salary-structure-generate"
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400
        )

    def test_zero_lpa(self):

        response = self.client.post(
            reverse(
                "salary-structure-generate"
            ),
            {"lpa": 0},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400
        )

    def test_negative_lpa(self):

        response = self.client.post(
            reverse(
                "salary-structure-generate"
            ),
            {"lpa": -5},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400
        )

    def test_invalid_lpa(self):

        response = self.client.post(
            reverse(
                "salary-structure-generate"
            ),
            {"lpa": "abc"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400
        )

    def test_valid_lpa(self):

        response = self.client.post(
            reverse(
                "salary-structure-generate"
            ),
            {"lpa": 6},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_decimal_lpa_api(self):

        response = self.client.post(
            reverse(
                "salary-structure-generate"
            ),
            {"lpa": 4.5},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["annual_ctc"],
            Decimal("450000.00")
        )

        self.assertEqual(
            response.data["monthly_ctc"],
            Decimal("37500.00")
        )

    def test_six_lpa_api_response(self):

        response = self.client.post(
            reverse(
                "salary-structure-generate"
            ),
            {"lpa": 6},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["annual_ctc"],
            Decimal("600000.00")
        )

        self.assertEqual(
            response.data["monthly_ctc"],
            Decimal("50000.00")
        )

        self.assertEqual(
            response.data["salary_structure"]["basic"],
            Decimal("25000.00")
        )

        self.assertEqual(
            response.data["salary_structure"]["hra"],
            Decimal("12500.00")
        )

        self.assertEqual(
            response.data[
                "salary_structure"
            ]["special_allowance"],
            Decimal("12500.00")
        )
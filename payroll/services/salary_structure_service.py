from decimal import Decimal, ROUND_HALF_UP

from payroll.constants import (
    BASIC_PERCENTAGE,
    HRA_PERCENTAGE,
)


class SalaryStructureService:

    @staticmethod
    def round_money(amount):
        return amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calculate_annual_ctc(lpa):
        """
        Convert LPA into annual CTC.

        Example:
        6 LPA = 6 * 100000 = 600000
        """
        return lpa * Decimal("100000")

    @staticmethod
    def calculate_monthly_ctc(annual_ctc):
        """
        Convert annual CTC into monthly CTC.
        """
        return annual_ctc / Decimal("12")

    @staticmethod
    def calculate_basic(monthly_ctc):
        """
        Basic = 50% of Monthly CTC.
        """
        return monthly_ctc * BASIC_PERCENTAGE

    @staticmethod
    def calculate_hra(basic):
        """
        HRA = 50% of Basic.
        """
        return basic * HRA_PERCENTAGE

    @staticmethod
    def calculate_remaining_allowance(
        monthly_ctc,
        basic,
        hra
    ):
        """
        Special Allowance = remaining amount.
        """
        return monthly_ctc - basic - hra

    @classmethod
    def generate_salary_structure(cls, lpa):

        # 1. LPA -> Annual CTC
        annual_ctc = cls.calculate_annual_ctc(lpa)

        # 2. Annual CTC -> Monthly CTC
        monthly_ctc = cls.calculate_monthly_ctc(
            annual_ctc
        )

        # 3. Calculate Basic
        basic = cls.calculate_basic(
            monthly_ctc
        )

        # 4. Calculate HRA
        hra = cls.calculate_hra(
            basic
        )

        # 5. Calculate remaining allowance
        special_allowance = (
            cls.calculate_remaining_allowance(
                monthly_ctc,
                basic,
                hra
            )
        )

        # 6. Verify reconciliation
        component_total = (
            basic +
            hra +
            special_allowance
        )

        if (
            cls.round_money(component_total)
            != cls.round_money(monthly_ctc)
        ):
            raise ValueError(
                "Salary components do not reconcile "
                "with monthly CTC."
            )

        # 7. Return complete salary structure
        return {
            "annual_ctc": cls.round_money(
                annual_ctc
            ),

            "monthly_ctc": cls.round_money(
                monthly_ctc
            ),

            "salary_structure": {
                "basic": cls.round_money(
                    basic
                ),

                "hra": cls.round_money(
                    hra
                ),

                "special_allowance": cls.round_money(
                    special_allowance
                ),
            },

            "annual_salary_structure": {
                "basic": cls.round_money(
                    basic * Decimal("12")
                ),

                "hra": cls.round_money(
                    hra * Decimal("12")
                ),

                "special_allowance": cls.round_money(
                    special_allowance * Decimal("12")
                ),
            },

            "calculation_rules": {
                "basic": "50% of monthly CTC",
                "hra": "50% of basic",
                "special_allowance": "remaining amount",
            },
        }
from decimal import Decimal

from rest_framework import serializers
from payroll.models import (
    Employee,
    EmployeeSalaryHistory,
    EmployeeChangeHistory,
)


class SalaryStructureRequestSerializer(serializers.Serializer):
    """
    Validates the LPA provided by the client.
    """

    lpa = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal("0.01")
    )


class SalaryComponentsSerializer(serializers.Serializer):

    basic = serializers.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    hra = serializers.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    special_allowance = serializers.DecimalField(
        max_digits=15,
        decimal_places=2
    )


class CalculationRulesSerializer(serializers.Serializer):

    basic = serializers.CharField()

    hra = serializers.CharField()

    special_allowance = serializers.CharField()


class SalaryStructureResponseSerializer(serializers.Serializer):

    annual_ctc = serializers.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    monthly_ctc = serializers.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    salary_structure = SalaryComponentsSerializer()

    annual_salary_structure = SalaryComponentsSerializer()

    calculation_rules = CalculationRulesSerializer()

    input = serializers.DictField()



class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying the current employee information.
    """

    class Meta:
        model = Employee
        fields = [
            "employee_id",
            "name",
            "joining_date",
            "designation",
            "department",
            "current_ctc",
        
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]


class SalaryUpdateSerializer(serializers.Serializer):
    """
    Serializer used when HR wants to update an employee's salary.
    """

    new_ctc = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01")
    )

    effective_from = serializers.DateField()

    reason = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )
    changed_by = serializers.CharField(
        max_length=150,
        required=True,
    )
    idempotency_key = serializers.CharField(
    max_length=100,
    required=True
)

    def validate_new_ctc(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "New CTC must be greater than zero."
            )

        return value


class EmployeeSalaryHistorySerializer(
    serializers.ModelSerializer
):
    """
    Serializer for displaying salary history.
    """
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeSalaryHistory
        fields = [
            "id",
            "employee",
            "ctc",
            "effective_from",
            "effective_to",
            "reason",
            "idempotency_key",
            "created_at",
            "created_by",
            
        ]

        read_only_fields = [
            "id",
            "created_at",
            "created_by",
        ]
    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return None

class EmployeeChangeHistorySerializer(
    serializers.ModelSerializer
):
    """
    Serializer for displaying employee change/audit history.
    """

    class Meta:
        model = EmployeeChangeHistory
        fields = [
            "id",
            "employee",
            "field_name",
            "old_value",
            "new_value",
            "effective_date",
            "reason",
            "changed_at",
            "changed_by",
            "correlation_id",
        ]

        read_only_fields = [
            "id",
            "changed_at",
            "changed_by",
        ]
class SalaryDateLookupSerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import uuid
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal, InvalidOperation

from .serializers import (
    SalaryStructureRequestSerializer,
    SalaryStructureResponseSerializer,
)
from .services.salary_structure_service import (
    SalaryStructureService,
)
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from payroll.models import (
    Employee,
    EmployeeSalaryHistory,
    EmployeeChangeHistory,
)

from payroll.serializers import (
    EmployeeSerializer,
    SalaryUpdateSerializer,
    EmployeeSalaryHistorySerializer,
    EmployeeChangeHistorySerializer,
)


from payroll.services.salary_history_service import (
    SalaryHistoryService,
)
from payroll.serializers import SalaryDateLookupSerializer




class SalaryStructureGenerateAPIView(APIView):
    """
    Generate salary structure from employee LPA.
    """

    def post(self, request):

        # Validate request
        request_serializer = SalaryStructureRequestSerializer(
            data=request.data
        )

        request_serializer.is_valid(
            raise_exception=True
        )

        lpa = request_serializer.validated_data["lpa"]

        # Generate salary structure
        result = (
            SalaryStructureService
            .generate_salary_structure(lpa)
        )

        # Add original input
        result["input"] = {
            "lpa": lpa
        }

        # Serialize response
        response_serializer = SalaryStructureResponseSerializer(
            data=result
        )

        response_serializer.is_valid(
            raise_exception=True
        )

        return Response(
            response_serializer.validated_data,
            status=status.HTTP_200_OK
        )
class EmployeeDetailAPIView(APIView):
    """
    GET /api/employees/<employee_id>/

    Returns the current employee information.
    """

    def get(self, request, employee_id):

        employee = get_object_or_404(
            Employee,
            employee_id=employee_id,
        )

        serializer = EmployeeSerializer(employee)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class EmployeeHistoryAPIView(APIView):
    """
    GET /api/employees/<employee_id>/history/

    Returns employee change/audit history.
    """

    def get(self, request, employee_id):

        employee = get_object_or_404(
            Employee,
            employee_id=employee_id,
        )

        history = (
            EmployeeChangeHistory.objects
            .filter(employee=employee)
            .order_by("-changed_at")
        )

        serializer = EmployeeChangeHistorySerializer(
            history,
            many=True,
        )

        return Response(
            {
                "employee_id": employee.employee_id,
                "history": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class EmployeeSalaryHistoryAPIView(APIView):
    """
    GET /api/employees/<employee_id>/salary-history/

    Returns the employee's complete salary history.

    """
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):

        employee = get_object_or_404(
            Employee,
            employee_id=employee_id,
        )

        salary_history = (
            EmployeeSalaryHistory.objects
            .filter(employee=employee)
            .order_by("-effective_from")
        )

        serializer = EmployeeSalaryHistorySerializer(
            salary_history,
            many=True,
        )

        return Response(
            {
                "employee_id": employee.employee_id,
                "salary_history": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class EmployeeSalaryUpdateAPIView(APIView):
    """
    PATCH /api/employees/<employee_id>/salary/

    Updates employee salary while preserving
    the previous salary as history.
    """

    def patch(self, request, employee_id):

        employee = get_object_or_404(
            Employee,
            employee_id=employee_id,
        )
        print(
          "SALARY UPDATE:",
          employee.employee_id,
          employee.pk,
          employee.current_ctc,
)

        serializer = SalaryUpdateSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        correlation_id = request.headers.get("X-Correlation-ID")

        if not correlation_id:
           correlation_id = str(uuid.uuid4())


        try:

            new_salary = (
                SalaryHistoryService.update_salary(
                    employee=employee,
                    new_ctc=serializer.validated_data[
                        "new_ctc"
                    ],
                    effective_from=serializer.validated_data[
                        "effective_from"
                    ],
                    reason=serializer.validated_data.get(
                        "reason",
                        "",
                    ),
                    changed_by=serializer.validated_data["changed_by"],
                    correlation_id=correlation_id,
                    idempotency_key=serializer.validated_data["idempotency_key"],
                )
            )
                
            

        except ValidationError as exc:

            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = (
            EmployeeSalaryHistorySerializer(
                new_salary
            )
        )

        return Response(
            {
                "message": "Salary updated successfully.",
                "employee_id": employee.employee_id,
                "correlation_id": correlation_id,
                "salary": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )
class EmployeeSalaryEffectiveDateAPIView(APIView):
    def get(self, request, employee_id):
        employee = get_object_or_404(
            Employee,
            employee_id=employee_id
        )

        serializer = SalaryDateLookupSerializer(
            data=request.query_params
        )

        serializer.is_valid(raise_exception=True)

        target_date = serializer.validated_data["date"]

        try:
            salary = SalaryHistoryService.get_salary_for_date(
                employee=employee,
                target_date=target_date
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND
            )

        response_serializer = EmployeeSalaryHistorySerializer(
            salary
        )

        return Response(
            {
                "employee_id": employee.employee_id,
                "date": target_date,
                "salary": response_serializer.data
            },
            status=status.HTTP_200_OK
        )
class EmployeeCreateAPIView(APIView):
    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        employee = serializer.save()

        return Response(
            {
                "message": "Employee created successfully.",
                "employee": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
class AllEmployeeHistoryAPIView(APIView):
    def get(self, request):
        history = (
            EmployeeChangeHistory.objects
            .select_related("employee")
            .all()
            .order_by("employee__employee_id", "-changed_at")
        )

        serializer = EmployeeChangeHistorySerializer(history, many=True)

        return Response(
            {
                "count": history.count(),
                "history": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
class SalaryRangeHistoryAPIView(APIView):
    """
    GET /api/payroll/employees/salary-range-history/

    Returns employees whose current CTC is within
    the requested LPA range, along with salary history
    and change history.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        min_lpa = request.query_params.get("min_lpa")
        max_lpa = request.query_params.get("max_lpa")

        # Validate required parameters
        if min_lpa is None or max_lpa is None:
            return Response(
                {
                    "detail": "Both min_lpa and max_lpa are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Convert LPA values to Decimal
        try:
            min_lpa = Decimal(min_lpa)
            max_lpa = Decimal(max_lpa)
        except InvalidOperation:
            return Response(
                {
                    "detail": "min_lpa and max_lpa must be valid numbers."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate range
        if min_lpa < 0 or max_lpa < 0:
            return Response(
                {
                    "detail": "LPA values cannot be negative."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if min_lpa > max_lpa:
            return Response(
                {
                    "detail": "min_lpa cannot be greater than max_lpa."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Convert LPA to annual CTC
        min_ctc = min_lpa * Decimal("100000")
        max_ctc = max_lpa * Decimal("100000")

        # Find employees within CTC range
        employees = (
            Employee.objects
            .filter(
                current_ctc__gte=min_ctc,
                current_ctc__lte=max_ctc,
            )
            .order_by("employee_id")
        )

        result = []

        for employee in employees:

            # Employee salary history
            salary_history = (
                EmployeeSalaryHistory.objects
                .filter(employee=employee)
                .order_by("-effective_from")
            )

            # Employee change history
            change_history = (
                EmployeeChangeHistory.objects
                .filter(employee=employee)
                .order_by("-changed_at")
            )

            result.append(
                {
                    "employee": EmployeeSerializer(employee).data,
                    "salary_history": EmployeeSalaryHistorySerializer(
                        salary_history,
                        many=True
                    ).data,
                    "change_history": EmployeeChangeHistorySerializer(
                        change_history,
                        many=True
                    ).data,
                }
            )

        return Response(
            {
                "min_lpa": str(min_lpa),
                "max_lpa": str(max_lpa),
                "min_ctc": str(min_ctc),
                "max_ctc": str(max_ctc),
                "count": len(result),
                "employees": result,
            },
            status=status.HTTP_200_OK,
        )
class HistoryByLPAAPIView(APIView):
    """
    GET /api/payroll/employees/history-by-lpa/?lpa=6

    Returns employee history for employees
    having exactly the requested LPA.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        lpa = request.query_params.get("lpa")

        # Check LPA parameter
        if lpa is None:
            return Response(
                {
                    "detail": "lpa is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Convert LPA to Decimal
        try:
            lpa = Decimal(lpa)
        except InvalidOperation:
            return Response(
                {
                    "detail": "lpa must be a valid number."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # LPA cannot be negative
        if lpa < 0:
            return Response(
                {
                    "detail": "lpa cannot be negative."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Convert LPA to annual CTC
        ctc = lpa * Decimal("100000")

        # Find employees having EXACTLY this CTC
        employees = (
            Employee.objects
            .filter(current_ctc=ctc)
            .order_by("employee_id")
        )

        result = []

        for employee in employees:

            history = (
                EmployeeChangeHistory.objects
                .filter(employee=employee)
                .order_by("-changed_at")
            )

            result.append(
                {
                    "employee": EmployeeSerializer(employee).data,
                    "history": EmployeeChangeHistorySerializer(
                        history,
                        many=True
                    ).data,
                }
            )

        return Response(
            {
                "lpa": str(lpa),
                "ctc": str(ctc),
                "count": len(result),
                "employees": result,
            },
            status=status.HTTP_200_OK,
        )
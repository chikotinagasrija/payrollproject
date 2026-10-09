from django.urls import path

from .views import SalaryStructureGenerateAPIView
from .views import (
    EmployeeCreateAPIView,
    EmployeeDetailAPIView,
    EmployeeHistoryAPIView,
    EmployeeSalaryHistoryAPIView,
    EmployeeSalaryUpdateAPIView,
    EmployeeSalaryEffectiveDateAPIView,
    AllEmployeeHistoryAPIView,
    SalaryRangeHistoryAPIView,
    HistoryByLPAAPIView,
)


urlpatterns = [

    path(
        "salary-structure/generate/",
        SalaryStructureGenerateAPIView.as_view(),
        name="salary-structure-generate"
    ),

    # ALL EMPLOYEE HISTORY — keep BEFORE <employee_id>
    path(
        "employees/history/",
        AllEmployeeHistoryAPIView.as_view(),
        name="all-employee-history",
    ),
    path(
    "employees/salary-range-history/",
    SalaryRangeHistoryAPIView.as_view(),
    name="salary-range-history",
),
    path(
        "employees/history-by-lpa/",
        HistoryByLPAAPIView.as_view(),
        name="history-by-lpa",
    ),

    # EMPLOYEE DETAIL
    path(
        "employees/<str:employee_id>/",
        EmployeeDetailAPIView.as_view(),
        name="employee-detail",
    ),

    # INDIVIDUAL EMPLOYEE HISTORY
    path(
        "employees/<str:employee_id>/history/",
        EmployeeHistoryAPIView.as_view(),
        name="employee-history",
    ),

    path(
        "employees/<str:employee_id>/salary-history/",
        EmployeeSalaryHistoryAPIView.as_view(),
        name="employee-salary-history",
    ),

    path(
        "employees/<str:employee_id>/salary/update/",
        EmployeeSalaryUpdateAPIView.as_view(),
        name="employee-salary-update",
    ),

    path(
        "employees/<str:employee_id>/salary/",
        EmployeeSalaryEffectiveDateAPIView.as_view(),
        name="employee-salary-effective-date",
    ),

    path(
        "employees/",
        EmployeeCreateAPIView.as_view(),
        name="employee-create",
    ),
]
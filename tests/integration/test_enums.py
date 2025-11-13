from luna_bench._internal.usecases.benchmark.enums import UseCaseErrorHandlingMode
from luna_bench.components.enums import ErrorHandlingMode


class TestEnums:
    def test_error_handling_enums_in_sync(self) -> None:
        for use_case_enum_member in UseCaseErrorHandlingMode:
            component_enum_member = ErrorHandlingMode(use_case_enum_member.value)

            assert use_case_enum_member.name == component_enum_member.name

        for component_enum_member in ErrorHandlingMode:
            use_case_enum_member = UseCaseErrorHandlingMode(component_enum_member.value)

            assert component_enum_member.name == use_case_enum_member.name

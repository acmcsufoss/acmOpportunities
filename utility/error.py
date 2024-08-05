from dataclasses import dataclass


@dataclass
class ErrorMsg:
    """Custom error message data class."""

    @staticmethod
    def status_code_failure(status_code: str) -> str:
        """A function returns an status code that is not 200."""

        return f"Execution failure. Status code returned: {status_code}."

    @staticmethod
    def date_difference_failure(error: str) -> str:
        """Calculating the date difference is not possible."""

        return f"Error calculating date difference: {error}."

    @staticmethod
    def file_open_failure(file_path: str) -> str:
        """Unable to open file path."""

        return f"Unable to open/read file path: '{file_path}'."

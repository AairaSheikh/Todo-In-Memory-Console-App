"""Main entry point for the Todo In-Memory Console App."""

from src.task_list import TaskList
from src.console_interface import ConsoleInterface


def main():
    """Initialize and run the Todo application."""
    task_list = TaskList()
    console = ConsoleInterface(task_list)
    console.run()


if __name__ == "__main__":
    main()

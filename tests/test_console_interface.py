"""Unit tests for the ConsoleInterface."""

import pytest
from io import StringIO
import sys
from src.task_list import TaskList
from src.console_interface import ConsoleInterface


class TestCommandParsing:
    """Test command parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.task_list = TaskList()
        self.console = ConsoleInterface(self.task_list)

    def test_parse_add_command_simple(self):
        """Test parsing simple add command."""
        command, args = self.console.parse_command("add Buy groceries")
        
        assert command == "add"
        assert args == ["Buy groceries"]

    def test_parse_add_command_with_priority(self):
        """Test parsing add command with priority."""
        command, args = self.console.parse_command("add Buy milk --priority High")
        
        assert command == "add"
        assert args[0] == "Buy milk"
        assert "--priority" in args
        assert "High" in args

    def test_parse_delete_command(self):
        """Test parsing delete command."""
        command, args = self.console.parse_command("delete 1")
        
        assert command == "delete"
        assert args == ["1"]

    def test_parse_update_command_description_only(self):
        """Test parsing update command with description only."""
        command, args = self.console.parse_command("update 1 --description New task")
        
        assert command == "update"
        assert args[0] == "1"
        assert "--description" in args
        assert "New task" in args

    def test_parse_update_command_priority_only(self):
        """Test parsing update command with priority only."""
        command, args = self.console.parse_command("update 1 --priority High")
        
        assert command == "update"
        assert args[0] == "1"
        assert "--priority" in args
        assert "High" in args

    def test_parse_update_command_both_fields(self):
        """Test parsing update command with both description and priority."""
        command, args = self.console.parse_command("update 1 --description New --priority Low")
        
        assert command == "update"
        assert args[0] == "1"
        assert "--description" in args
        assert "--priority" in args

    def test_parse_complete_command(self):
        """Test parsing complete command."""
        command, args = self.console.parse_command("complete 1")
        
        assert command == "complete"
        assert args == ["1"]

    def test_parse_view_command(self):
        """Test parsing view command."""
        command, args = self.console.parse_command("view")
        
        assert command == "view"
        assert args == []

    def test_parse_help_command(self):
        """Test parsing help command."""
        command, args = self.console.parse_command("help")
        
        assert command == "help"
        assert args == []

    def test_parse_exit_command(self):
        """Test parsing exit command."""
        command, args = self.console.parse_command("exit")
        
        assert command == "exit"
        assert args == []

    def test_parse_empty_input(self):
        """Test parsing empty input."""
        command, args = self.console.parse_command("")
        
        assert command == ""
        assert args == []

    def test_parse_whitespace_only_input(self):
        """Test parsing whitespace-only input."""
        command, args = self.console.parse_command("   ")
        
        assert command == ""
        assert args == []

    def test_parse_command_case_insensitive(self):
        """Test that commands are case-insensitive."""
        command1, _ = self.console.parse_command("ADD task")
        command2, _ = self.console.parse_command("Add task")
        command3, _ = self.console.parse_command("add task")
        
        assert command1 == command2 == command3 == "add"


class TestDisplayMethods:
    """Test display methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.task_list = TaskList()
        self.console = ConsoleInterface(self.task_list)

    def test_display_empty_message(self, capsys):
        """Test displaying empty message."""
        self.console.display_empty_message()
        captured = capsys.readouterr()
        
        assert "No tasks" in captured.out

    def test_display_confirmation(self, capsys):
        """Test displaying confirmation message."""
        self.console.display_confirmation("Task added")
        captured = capsys.readouterr()
        
        assert "Task added" in captured.out
        assert "✓" in captured.out

    def test_display_error(self, capsys):
        """Test displaying error message."""
        self.console.display_error("Invalid input")
        captured = capsys.readouterr()
        
        assert "Invalid input" in captured.out
        assert "✗" in captured.out

    def test_display_tasks_empty(self, capsys):
        """Test displaying empty task list."""
        self.console.display_tasks([])
        captured = capsys.readouterr()
        
        assert "No tasks" in captured.out

    def test_display_tasks_with_tasks(self, capsys):
        """Test displaying tasks."""
        task1 = self.task_list.add_task("Buy milk", priority="High")
        task2 = self.task_list.add_task("Clean house", priority="Low")
        
        tasks = self.task_list.get_all_tasks()
        self.console.display_tasks(tasks)
        captured = capsys.readouterr()
        
        assert "Buy milk" in captured.out
        assert "Clean house" in captured.out
        assert "High" in captured.out
        assert "Low" in captured.out


class TestCommandHandlers:
    """Test command handler methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.task_list = TaskList()
        self.console = ConsoleInterface(self.task_list)

    def test_handle_add_valid(self, capsys):
        """Test handling valid add command."""
        self.console.handle_add(["Buy groceries"])
        captured = capsys.readouterr()
        
        assert "Task added" in captured.out
        assert len(self.task_list.get_all_tasks()) == 1

    def test_handle_add_with_priority(self, capsys):
        """Test handling add command with priority."""
        self.console.handle_add(["Buy milk", "--priority", "High"])
        captured = capsys.readouterr()
        
        assert "Task added" in captured.out
        task = self.task_list.get_task(1)
        assert task.priority == "High"

    def test_handle_add_no_args(self, capsys):
        """Test handling add command with no arguments."""
        self.console.handle_add([])
        captured = capsys.readouterr()
        
        assert "Error" in captured.out
        assert "Usage" in captured.out

    def test_handle_delete_valid(self, capsys):
        """Test handling valid delete command."""
        self.task_list.add_task("Task to delete")
        self.console.handle_delete(["1"])
        captured = capsys.readouterr()
        
        assert "Task deleted" in captured.out
        assert len(self.task_list.get_all_tasks()) == 0

    def test_handle_delete_invalid_id(self, capsys):
        """Test handling delete command with invalid ID."""
        self.console.handle_delete(["999"])
        captured = capsys.readouterr()
        
        assert "Error" in captured.out

    def test_handle_delete_no_args(self, capsys):
        """Test handling delete command with no arguments."""
        self.console.handle_delete([])
        captured = capsys.readouterr()
        
        assert "Error" in captured.out
        assert "Usage" in captured.out

    def test_handle_update_description(self, capsys):
        """Test handling update command with description."""
        self.task_list.add_task("Original")
        self.console.handle_update(["1", "--description", "Updated"])
        captured = capsys.readouterr()
        
        assert "Task updated" in captured.out
        assert self.task_list.get_task(1).description == "Updated"

    def test_handle_update_priority(self, capsys):
        """Test handling update command with priority."""
        self.task_list.add_task("Task", priority="Low")
        self.console.handle_update(["1", "--priority", "High"])
        captured = capsys.readouterr()
        
        assert "Task updated" in captured.out
        assert self.task_list.get_task(1).priority == "High"

    def test_handle_update_no_args(self, capsys):
        """Test handling update command with no arguments."""
        self.console.handle_update([])
        captured = capsys.readouterr()
        
        assert "Error" in captured.out
        assert "Usage" in captured.out

    def test_handle_complete_valid(self, capsys):
        """Test handling valid complete command."""
        self.task_list.add_task("Task")
        self.console.handle_complete(["1"])
        captured = capsys.readouterr()
        
        assert "marked as complete" in captured.out
        assert self.task_list.get_task(1).completed is True

    def test_handle_complete_toggle(self, capsys):
        """Test toggling completion status."""
        self.task_list.add_task("Task")
        self.console.handle_complete(["1"])
        self.console.handle_complete(["1"])
        captured = capsys.readouterr()
        
        assert "marked as incomplete" in captured.out
        assert self.task_list.get_task(1).completed is False

    def test_handle_complete_no_args(self, capsys):
        """Test handling complete command with no arguments."""
        self.console.handle_complete([])
        captured = capsys.readouterr()
        
        assert "Error" in captured.out
        assert "Usage" in captured.out

    def test_handle_view(self, capsys):
        """Test handling view command."""
        self.task_list.add_task("Task 1")
        self.task_list.add_task("Task 2")
        self.console.handle_view()
        captured = capsys.readouterr()
        
        assert "Task 1" in captured.out
        assert "Task 2" in captured.out

    def test_handle_help(self, capsys):
        """Test handling help command."""
        self.console.handle_help()
        captured = capsys.readouterr()
        
        assert "Available Commands" in captured.out
        assert "add" in captured.out
        assert "delete" in captured.out

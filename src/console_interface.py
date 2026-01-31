"""ConsoleInterface for the Todo application."""

from typing import Tuple, List
from src.task_list import TaskList


class ConsoleInterface:
    """Handles command-line interaction with the user.
    
    Provides methods for parsing user input, displaying tasks, and managing
    the main event loop for the Todo application.
    """

    def __init__(self, task_list: TaskList):
        """Initialize the ConsoleInterface.
        
        Args:
            task_list: The TaskList instance to manage
        """
        self.task_list = task_list

    def parse_command(self, user_input: str) -> Tuple[str, List[str]]:
        """Parse user input into command and arguments.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            Tuple of (command, arguments_list)
            
        Examples:
            "add Buy milk" -> ("add", ["Buy milk"])
            "delete 1" -> ("delete", ["1"])
            "update 1 --description New task" -> ("update", ["1", "--description", "New task"])
        """
        parts = user_input.strip().split(maxsplit=1)
        
        if not parts:
            return ("", [])
        
        command = parts[0].lower()
        args_str = parts[1] if len(parts) > 1 else ""
        
        # Parse arguments based on command type
        if command == "add":
            # Parse: add <description> [--priority <priority>]
            args = self._parse_add_args(args_str)
        elif command == "delete":
            # Parse: delete <task_id>
            args = args_str.split() if args_str else []
        elif command == "update":
            # Parse: update <task_id> [--description <desc>] [--priority <priority>]
            args = self._parse_update_args(args_str)
        elif command == "complete":
            # Parse: complete <task_id>
            args = args_str.split() if args_str else []
        elif command in ("view", "help", "exit"):
            args = []
        else:
            args = args_str.split() if args_str else []
        
        return (command, args)

    def _parse_add_args(self, args_str: str) -> List[str]:
        """Parse arguments for add command.
        
        Format: <description> [--priority <priority>]
        """
        if not args_str:
            return []
        
        # Check for --priority flag
        if "--priority" in args_str:
            parts = args_str.split("--priority")
            description = parts[0].strip()
            priority = parts[1].strip() if len(parts) > 1 else ""
            return [description, "--priority", priority] if priority else [description]
        
        return [args_str.strip()]

    def _parse_update_args(self, args_str: str) -> List[str]:
        """Parse arguments for update command.
        
        Format: <task_id> [--description <desc>] [--priority <priority>]
        """
        if not args_str:
            return []
        
        parts = args_str.split(maxsplit=1)
        task_id = parts[0] if parts else ""
        rest = parts[1] if len(parts) > 1 else ""
        
        args = [task_id]
        
        if "--description" in rest:
            desc_parts = rest.split("--description", 1)
            if len(desc_parts) > 1:
                desc_content = desc_parts[1].strip()
                # Check if there's a --priority after description
                if "--priority" in desc_content:
                    desc_and_priority = desc_content.split("--priority", 1)
                    args.extend(["--description", desc_and_priority[0].strip()])
                    if len(desc_and_priority) > 1:
                        args.extend(["--priority", desc_and_priority[1].strip()])
                else:
                    args.extend(["--description", desc_content])
        elif "--priority" in rest:
            priority_parts = rest.split("--priority", 1)
            if len(priority_parts) > 1:
                args.extend(["--priority", priority_parts[1].strip()])
        
        return args

    def display_welcome(self) -> None:
        """Display welcome message and available commands."""
        print("\n" + "=" * 60)
        print("Welcome to Todo In-Memory Console App".center(60))
        print("=" * 60)
        print("\nAvailable Commands:")
        print("  add <description> [--priority <priority>]")
        print("      Add a new task (priority: High, Medium, Low)")
        print("  delete <task_id>")
        print("      Delete a task by ID")
        print("  update <task_id> [--description <desc>] [--priority <priority>]")
        print("      Update a task's description and/or priority")
        print("  view")
        print("      Display all tasks")
        print("  complete <task_id>")
        print("      Toggle task completion status")
        print("  help")
        print("      Show this help message")
        print("  exit")
        print("      Exit the application")
        print("=" * 60 + "\n")

    def display_tasks(self, tasks: List) -> None:
        """Display all tasks in a formatted table.
        
        Args:
            tasks: List of Task objects to display
        """
        if not tasks:
            self.display_empty_message()
            return
        
        print("\n" + "-" * 80)
        print(f"{'ID':<4} {'Status':<8} {'Priority':<10} {'Description':<50}")
        print("-" * 80)
        
        for task in tasks:
            status = "✓ DONE" if task.completed else "○ TODO"
            # Truncate description if too long
            desc = task.description[:47] + "..." if len(task.description) > 50 else task.description
            print(f"{task.task_id:<4} {status:<8} {task.priority:<10} {desc:<50}")
        
        print("-" * 80 + "\n")

    def display_empty_message(self) -> None:
        """Display message when task list is empty."""
        print("\n📭 No tasks yet. Add one with: add <description>\n")

    def display_confirmation(self, message: str) -> None:
        """Display operation success message.
        
        Args:
            message: Confirmation message to display
        """
        print(f"\n✓ {message}\n")

    def display_error(self, message: str) -> None:
        """Display error message.
        
        Args:
            message: Error message to display
        """
        print(f"\n✗ Error: {message}\n")

    def handle_add(self, args: List[str]) -> None:
        """Handle add command.
        
        Args:
            args: Parsed command arguments
        """
        if not args:
            self.display_error("Usage: add <description> [--priority <priority>]")
            return
        
        description = args[0]
        priority = "Medium"
        
        # Check for priority flag
        if len(args) > 2 and args[1] == "--priority":
            priority = args[2]
        
        try:
            task = self.task_list.add_task(description, priority=priority)
            self.display_confirmation(f"Task added: [{task.task_id}] {task.description} (Priority: {task.priority})")
        except ValueError as e:
            self.display_error(str(e))

    def handle_delete(self, args: List[str]) -> None:
        """Handle delete command.
        
        Args:
            args: Parsed command arguments
        """
        if not args:
            self.display_error("Usage: delete <task_id>")
            return
        
        try:
            task_id = int(args[0])
            task = self.task_list.delete_task(task_id)
            self.display_confirmation(f"Task deleted: [{task.task_id}] {task.description}")
        except ValueError as e:
            if "invalid literal" in str(e):
                self.display_error("Task ID must be a number")
            else:
                self.display_error(str(e))

    def handle_update(self, args: List[str]) -> None:
        """Handle update command.
        
        Args:
            args: Parsed command arguments
        """
        if not args:
            self.display_error("Usage: update <task_id> [--description <desc>] [--priority <priority>]")
            return
        
        try:
            task_id = int(args[0])
            description = None
            priority = None
            
            # Parse optional flags
            i = 1
            while i < len(args):
                if args[i] == "--description" and i + 1 < len(args):
                    description = args[i + 1]
                    i += 2
                elif args[i] == "--priority" and i + 1 < len(args):
                    priority = args[i + 1]
                    i += 2
                else:
                    i += 1
            
            if description is None and priority is None:
                self.display_error("Usage: update <task_id> [--description <desc>] [--priority <priority>]")
                return
            
            task = self.task_list.update_task(task_id, description=description, priority=priority)
            self.display_confirmation(f"Task updated: [{task.task_id}] {task.description} (Priority: {task.priority})")
        except ValueError as e:
            if "invalid literal" in str(e):
                self.display_error("Task ID must be a number")
            else:
                self.display_error(str(e))

    def handle_complete(self, args: List[str]) -> None:
        """Handle complete command.
        
        Args:
            args: Parsed command arguments
        """
        if not args:
            self.display_error("Usage: complete <task_id>")
            return
        
        try:
            task_id = int(args[0])
            task = self.task_list.toggle_completion(task_id)
            status = "marked as complete" if task.completed else "marked as incomplete"
            self.display_confirmation(f"Task {status}: [{task.task_id}] {task.description}")
        except ValueError as e:
            if "invalid literal" in str(e):
                self.display_error("Task ID must be a number")
            else:
                self.display_error(str(e))

    def handle_view(self) -> None:
        """Handle view command."""
        tasks = self.task_list.get_all_tasks()
        self.display_tasks(tasks)

    def handle_help(self) -> None:
        """Handle help command."""
        self.display_welcome()

    def run(self) -> None:
        """Main event loop for the console interface."""
        self.display_welcome()
        
        while True:
            try:
                user_input = input("todo> ").strip()
                
                if not user_input:
                    continue
                
                command, args = self.parse_command(user_input)
                
                if command == "exit":
                    print("\nGoodbye!\n")
                    break
                elif command == "add":
                    self.handle_add(args)
                elif command == "delete":
                    self.handle_delete(args)
                elif command == "update":
                    self.handle_update(args)
                elif command == "complete":
                    self.handle_complete(args)
                elif command == "view":
                    self.handle_view()
                elif command == "help":
                    self.handle_help()
                else:
                    self.display_error(f"Unknown command: {command}")
                    print("Type 'help' for available commands.\n")
            
            except KeyboardInterrupt:
                print("\n\nGoodbye!\n")
                break
            except Exception as e:
                self.display_error(f"Unexpected error: {str(e)}")

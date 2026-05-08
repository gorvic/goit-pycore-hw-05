from collections.abc import Callable, Iterator, MutableMapping
from dataclasses import dataclass
from functools import wraps
from typing import Optional


@dataclass(frozen=True, slots=True)
class Contact:
    """Represent a single contact record."""

    name: str
    phone: str


class Contacts(MutableMapping[str, Contact]):
    """
    Case-insensitive contact storage.

    Contacts are stored by normalized names, but original names are preserved
    for display. The class implements MutableMapping to behave like a regular
    dictionary while keeping validation and normalization centralized.
    """

    def __init__(self) -> None:
        self._db: dict[str, Contact] = {}

    def add(self, name: str, phone: str) -> bool:
        """
        Add a new contact.

        Returns False if contact already exists or input data is invalid.
        """
        prepared = self._prepare_contact(name, phone)

        if prepared is None:
            result = False
        else:
            key, contact = prepared

            if key in self._db:
                result = False
            else:
                self._db[key] = contact
                result = True

        return result

    def replace(self, name: str, phone: str) -> bool:
        """
        Replace phone number for an existing contact.

        Returns False if contact does not exist or input data is invalid.
        """
        key = self._normalize_name(name)
        clean_phone = phone.strip()

        if not key or not clean_phone or key not in self._db:
            result = False
        else:
            old_contact = self._db[key]
            self._db[key] = Contact(name=old_contact.name, phone=clean_phone)
            result = True

        return result

    def set(self, name: str, phone: str) -> bool:
        """
        Add or replace contact.

        Returns False only if input data is invalid.
        """
        prepared = self._prepare_contact(name, phone)

        if prepared is None:
            result = False
        else:
            key, contact = prepared
            self._db[key] = contact
            result = True

        return result

    def remove(self, name: str) -> bool:
        """
        Remove contact by name.

        Returns False if contact does not exist or name is invalid.
        """
        key = self._normalize_name(name)

        if not key or key not in self._db:
            result = False
        else:
            del self._db[key]
            result = True

        return result

    def exists(self, name: str) -> bool:
        """Return True if contact exists."""
        return name in self

    def get_phone(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Return contact phone by name.

        Returns default if contact does not exist.
        """
        contact = self.get(name)
        result = contact.phone if contact is not None else default

        return result

    def ordered_by_name(self, descending: bool = False) -> Iterator[Contact]:
        """Iterate over contacts sorted by display name."""
        contacts = sorted(
            self._db.values(),
            key=lambda contact: contact.name.lower(),
            reverse=descending,
        )

        return iter(contacts)

    def find(self, query: str) -> Iterator[Contact]:
        """
        Yield contacts whose name or phone contains the query.

        Empty query returns no results.
        """
        normalized_query = query.strip().lower()

        if normalized_query:
            for contact in self._db.values():
                name = contact.name.lower()
                phone = contact.phone.lower()

                if normalized_query in name or normalized_query in phone:
                    yield contact

    def find_all(self, query: str) -> list[Contact]:
        """Return all contacts matching query."""
        return list(self.find(query))

    def find_first(self, query: str) -> Optional[Contact]:
        """Return first contact matching query or None."""
        return next(self.find(query), None)

    def __getitem__(self, key: str) -> Contact:
        return self._db[self._normalize_name(key)]

    def __setitem__(self, key: str, value: Contact) -> None:
        """
        Store contact by normalized name.

        Mapping key must match contact.name to avoid inconsistent internal state.
        """
        normalized_key = self._normalize_name(key)
        normalized_contact_name = self._normalize_name(value.name)

        if not normalized_key:
            raise KeyError("Contact name cannot be empty")

        if normalized_key != normalized_contact_name:
            raise ValueError("Mapping key must match contact name")

        self._db[normalized_key] = value

    def __delitem__(self, key: str) -> None:
        del self._db[self._normalize_name(key)]

    def __iter__(self) -> Iterator[str]:
        return iter(self._db)

    def __len__(self) -> int:
        return len(self._db)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            result = self._normalize_name(key) in self._db
        else:
            result = False

        return result

    @classmethod
    def _prepare_contact(cls, name: str, phone: str) -> Optional[tuple[str, Contact]]:
        """
        Normalize and validate raw contact data before storing it.
        """
        clean_name = name.strip()
        clean_phone = phone.strip()
        key = cls._normalize_name(clean_name)

        if not key or not clean_phone:
            result = None
        else:
            result = key, Contact(name=clean_name, phone=clean_phone)

        return result

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize contact name for case-insensitive storage and lookup."""
        return name.strip().lower()


@dataclass(frozen=True, slots=True)
class CommandResult:
    """
    Represent command execution result.

    exit=True tells the main loop to stop the application.
    """

    message: str
    exit: bool = False


Handler = Callable[["CommandContext"], "CommandResult"]


@dataclass(frozen=True, slots=True)
class Command:
    """
    Describe one CLI command.

    Attributes:
        name: Command name.
        args: Required positional argument names.
        handler: Function that executes command logic.
    """

    name: str
    args: list[str]
    handler: Handler


@dataclass(frozen=True, slots=True)
class CommandContext:
    """
    Runtime context passed to command handlers.

    This keeps handler signatures stable even if more shared dependencies
    are added later.
    """

    db: Contacts
    commands: dict[str, Command]
    args: dict[str, str]


class ContactsError(Exception):
    """Base user-facing contact error."""


class CommandError(Exception):
    """Base user-facing command error."""


def input_error(handler: Handler) -> Handler:
    """Convert handler exceptions into command results."""

    @wraps(handler)
    def wrapper(context: CommandContext) -> CommandResult:
        try:
            result = handler(context)

        except (CommandError, ContactsError, ValueError, KeyError, IndexError) as error:
            result = CommandResult(
                error.args[0] if error.args else str(error)
            )

        return result

    return wrapper


def show_help(context: CommandContext) -> CommandResult:
    """Return a formatted list of available commands."""
    lines = ["Available commands:"]

    for command in context.commands.values():
        if command.args:
            arguments = " ".join(f"[{arg}]" for arg in command.args)
            lines.append(f"  {command.name} {arguments}")
        else:
            lines.append(f"  {command.name}")

    return CommandResult("\n".join(lines))


def show_greeting(context: CommandContext) -> CommandResult:
    """Return greeting message."""
    return CommandResult("How can I help you?")


@input_error
def add_contact(context: CommandContext) -> CommandResult:
    """Add a new contact to the contact book."""
    name = context.args["name"]
    phone = context.args["phone"]

    if not context.db.add(name, phone):
        raise ContactsError("Contact already exists or data is invalid.")

    return CommandResult("Contact added.")


@input_error
def change_contact(context: CommandContext) -> CommandResult:
    """Change phone number for an existing contact."""
    name = context.args["name"]
    phone = context.args["phone"]

    if not context.db.replace(name, phone):
        raise ContactsError("Contact not found or data is invalid.")

    return CommandResult("Contact updated.")


@input_error
def show_contact(context: CommandContext) -> CommandResult:
    """Return phone number for a contact by name."""
    name = context.args["name"]
    phone = context.db.get_phone(name)

    if phone is None:
        raise ContactsError("Contact not found.")

    return CommandResult(phone)


@input_error
def show_all_contacts(context: CommandContext) -> CommandResult:
    """Return all saved contacts sorted by name."""
    if not context.db:
        raise ContactsError("No contacts found.")

    contacts = (
        f"{contact.name}: {contact.phone}"
        for contact in context.db.ordered_by_name()
    )

    contacts_str = "\n".join(contacts)

    return CommandResult(f"Contacts:\n{contacts_str}")


def close_app(context: CommandContext) -> CommandResult:
    """Return final message and request application shutdown."""
    return CommandResult("Good bye!", exit=True)


def parse_input(user_input: str) -> tuple[str, list[str]]:
    """
    Parse raw user input into command name and positional arguments.

    Command name is case-insensitive. Arguments are preserved as entered.
    """
    parts = user_input.split()

    command = parts[0].lower() if parts else ""
    args = parts[1:] if parts else []

    return command, args


def named_args(required: list[str], args: list[str]) -> Optional[dict[str, str]]:
    """
    Convert positional arguments into named command arguments.

    Returns None if argument count does not match command signature.
    """
    if len(required) != len(args):
        result = None
    else:
        result = dict(zip(required, args))

    return result


def usage(command: Command) -> str:
    """Return usage message for a command."""
    if command.args:
        arguments = " ".join(f"[{arg}]" for arg in command.args)
        result = f"Usage: {command.name} {arguments}"
    else:
        result = f"Usage: {command.name}"

    return result


def execute_command(
    db: Contacts,
    commands: dict[str, Command],
    command: Command,
    args: list[str],
) -> CommandResult:
    """Validate command arguments and execute command handler."""
    parsed_args = named_args(command.args, args)

    if parsed_args is None:
        raise CommandError(usage(command))

    context = CommandContext(
        db=db,
        commands=commands,
        args=parsed_args,
    )
    result = command.handler(context)

    return result


def process_command(
    db: Contacts,
    commands: dict[str, Command],
    user_input: str,
) -> CommandResult:
    """Parse user input and dispatch command to a matching handler."""
    try:

        command_name, args = parse_input(user_input)

        if not command_name:
            raise CommandError("No command found.")

        if command_name not in commands:
            raise CommandError("Invalid command.")

        result = execute_command(
            db=db,
            commands=commands,
            command=commands[command_name],
            args=args,
        )

    except CommandError as error:
        result = CommandResult(error.args[0] if error.args else str(error))

    return result


def create_commands() -> dict[str, Command]:
    """
    Build command registry.

    Adding a new command should usually require only:
    - a handler function
    - one new item in this registry
    """
    return {
        "help": Command("help", [], show_help),
        "hello": Command("hello", [], show_greeting),
        "add": Command("add", ["name", "phone"], add_contact),
        "change": Command("change", ["name", "phone"], change_contact),
        "phone": Command("phone", ["name"], show_contact),
        "all": Command("all", [], show_all_contacts),
        "close": Command("close", [], close_app),
        "exit": Command("exit", [], close_app),
    }


def main() -> None:
    """Run assistant bot command loop."""
    contacts = Contacts()
    commands = create_commands()

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        result = process_command(contacts, commands, user_input)

        print(result.message)

        if result.exit:
            break


if __name__ == "__main__":
    main()

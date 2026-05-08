from collections.abc import Callable
from functools import wraps
from typing import Final


Contacts = dict[str, tuple[str, str]]
Handler = Callable[[Contacts, list[str]], str]


EXIT_COMMANDS: Final[set[str]] = {"close", "exit"}


class ContactsError(Exception):
    """Base user-facing contact error."""


def input_error(handler: Handler) -> Handler:
    """Convert handler exceptions into user-friendly messages."""

    @wraps(handler)
    def wrapper(contacts: Contacts, args: list[str]) -> str:
        try:
            message = handler(contacts, args)
        except (ContactsError, ValueError, KeyError, IndexError) as error:
            message = error.args[0] if error.args else str(error)

        return message

    return wrapper


def normalize_name(name: str) -> str:
    """Normalize contact name for case-insensitive lookup."""
    return name.strip().lower()


def parse_input(user_input: str) -> tuple[str, list[str]]:
    """Parse user input into command and arguments."""
    parts = user_input.split()

    command = parts[0].lower() if parts else ""
    args = parts[1:] if parts else []

    return command, args


@input_error
def contact_add(contacts: Contacts, args: list[str]) -> str:
    """Add a new contact if it does not exist yet."""
    try:
        name, phone = args
    except ValueError:
        raise ValueError("Usage: add [name] [phone]")

    key = normalize_name(name)
    clean_phone = phone.strip()

    if not key or not clean_phone:
        raise ValueError("Invalid contact data.")

    if key in contacts:
        raise ContactsError("Contact already exists.")

    contacts[key] = (name.strip(), clean_phone)

    return "Contact added."


@input_error
def contact_change(contacts: Contacts, args: list[str]) -> str:
    """Change phone number for an existing contact."""
    try:
        name, phone = args

    except ValueError:
        raise ValueError("Usage: change [name] [phone]")

    key = normalize_name(name)
    clean_phone = phone.strip()

    if not key or not clean_phone:
        raise ValueError("Invalid contact data.")

    if key not in contacts:
        raise KeyError("Contact not found.")

    old_name, _ = contacts[key]

    contacts[key] = (old_name, clean_phone)

    return "Contact updated."


@input_error
def show_phone(contacts: Contacts, args: list[str]) -> str:
    """Show phone number by contact name."""
    try:
        name, = args
    except ValueError:
        raise ValueError("Usage: phone [name]")

    try:
        contact = contacts[normalize_name(name)]
    except KeyError:
        raise KeyError("Contact not found.")

    return contact[1]


@input_error
def show_all(contacts: Contacts, args: list[str]) -> str:
    """Show all saved contacts sorted by name."""
    if args:
        raise ValueError("Usage: all")

    if not contacts:
        raise ContactsError("No contacts found.")

    lines = [
        f"{name}: {phone}"
        for name, phone in sorted(
            contacts.values(),
            key=lambda item: item[0].lower(),
        )
    ]

    return "\n".join(lines)


@input_error
def show_greeting(contacts: Contacts, args: list[str]) -> str:
    """Show greeting message."""
    if args:
        raise ValueError("Usage: hello")

    return "How can I help you?"


def create_handlers() -> dict[str, Handler]:
    """Create command handler registry."""
    return {
        "hello": show_greeting,
        "add": contact_add,
        "change": contact_change,
        "phone": show_phone,
        "all": show_all,
    }


def main() -> None:
    """Run assistant bot command loop."""
    contacts: Contacts = {}
    handlers = create_handlers()

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in EXIT_COMMANDS:
            print("Good bye!")
            break

        handler = handlers.get(command)
        message = handler(contacts, args) if handler is not None else "Invalid command."

        print(message)


if __name__ == "__main__":
    main()
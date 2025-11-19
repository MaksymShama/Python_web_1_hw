import pickle
import os
from collections import UserDict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


# ==================== Field Classes ====================
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Phone number must contain exactly 10 digits")
        super().__init__(value)

    @staticmethod
    def validate(value):
        return value.isdigit() and len(value) == 10


class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)


# ==================== Record and AddressBook ====================
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)
        else:
            raise ValueError(f"Phone {phone} not found")

    def edit_phone(self, old_phone, new_phone):
        phone_obj = self.find_phone(old_phone)
        if not phone_obj:
            raise ValueError(f"Phone {old_phone} not found")

        if not Phone.validate(new_phone):
            raise ValueError("New phone number must contain exactly 10 digits")

        self.phones.remove(phone_obj)
        self.phones.append(Phone(new_phone))

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones)
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError(f"Contact {name} not found")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday_date = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
            birthday_this_year = birthday_date.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_date.replace(year=today.year + 1)

            days_until_birthday = (birthday_this_year - today).days

            if 0 <= days_until_birthday <= 7:
                congratulation_date = birthday_this_year
                if birthday_this_year.weekday() == 5:  # Субота
                    congratulation_date += timedelta(days=2)
                elif birthday_this_year.weekday() == 6:  # Неділя
                    congratulation_date += timedelta(days=1)

                upcoming.append({
                    "name": record.name.value,
                    "birthday": congratulation_date.strftime("%d.%m.%Y")
                })

        return upcoming

    def __str__(self):
        if not self.data:
            return "Address book is empty"
        return "\n".join(str(record) for record in self.data.values())


# ==================== View Layer (Abstract Base Class) ====================
class BaseView(ABC):
    """Абстрактний базовий клас для представлення інформації користувачу"""

    @abstractmethod
    def show_message(self, message: str):
        """Відображає просте текстове повідомлення"""
        pass

    @abstractmethod
    def show_contacts(self, book: AddressBook):
        """Відображає всі контакти з адресної книги"""
        pass

    @abstractmethod
    def show_contact(self, record: Record):
        """Відображає окремий контакт"""
        pass

    @abstractmethod
    def show_commands(self):
        """Відображає список доступних команд"""
        pass

    @abstractmethod
    def show_birthdays(self, birthdays: list):
        """Відображає список майбутніх днів народження"""
        pass

    @abstractmethod
    def get_input(self, prompt: str = "") -> str:
        """Отримує введення від користувача"""
        pass

    @abstractmethod
    def show_welcome(self):
        """Відображає привітальне повідомлення"""
        pass

    @abstractmethod
    def show_goodbye(self):
        """Відображає прощальне повідомлення"""
        pass


# ==================== Console View Implementation ====================
class ConsoleView(BaseView):
    """Конкретна реалізація для консольного інтерфейсу"""

    def show_message(self, message: str):
        print(message)

    def show_contacts(self, book: AddressBook):
        if not book.data:
            print("No contacts saved.")
            return

        print("\n" + "=" * 50)
        print("ALL CONTACTS")
        print("=" * 50)
        for record in book.data.values():
            self.show_contact(record)
            print("-" * 50)

    def show_contact(self, record: Record):
        phones_str = '; '.join(p.value for p in record.phones) if record.phones else "No phones"
        birthday_str = f"Birthday: {record.birthday}" if record.birthday else "No birthday set"

        print(f"Name: {record.name.value}")
        print(f"Phones: {phones_str}")
        print(f"{birthday_str}")

    def show_commands(self):
        commands = [
            ("hello", "greet the bot"),
            ("add [name] [phone]", "add contact or phone"),
            ("change [name] [old_phone] [new_phone]", "change phone"),
            ("phone [name]", "show contact phones"),
            ("all", "show all contacts"),
            ("add-birthday [name] [DD.MM.YYYY]", "add birthday"),
            ("show-birthday [name]", "show birthday"),
            ("birthdays", "show upcoming birthdays (next 7 days)"),
            ("delete [name]", "delete contact"),
            ("remove [name] [phone]", "remove specific phone"),
            ("close/exit", "exit the bot"),
        ]

        print("\n" + "=" * 50)
        print("AVAILABLE COMMANDS")
        print("=" * 50)
        for cmd, description in commands:
            print(f"  {cmd:<40} - {description}")
        print("=" * 50)

    def show_birthdays(self, birthdays: list):
        if not birthdays:
            print("No upcoming birthdays in the next 7 days.")
            return

        print("\n" + "=" * 50)
        print("UPCOMING BIRTHDAYS")
        print("=" * 50)
        for item in birthdays:
            print(f"  {item['name']:<20} : {item['birthday']}")
        print("=" * 50)

    def get_input(self, prompt: str = ">>> ") -> str:
        return input(f"\n{prompt}")

    def show_welcome(self):
        print("\n" + "=" * 50)
        print("WELCOME TO THE ASSISTANT BOT!")
        print("=" * 50)
        print("Type 'help' to see available commands")
        print("=" * 50)

    def show_goodbye(self):
        print("\n" + "=" * 50)
        print("Good bye! Have a great day!")
        print("=" * 50)


# ==================== Data Persistence ====================
def save_data(book, filename="addressbook.pkl"):
    """Зберігає адресну книгу у файл за допомогою pickle"""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    """Завантажує адресну книгу з файлу, або створює нову, якщо файл не знайдено"""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# ==================== Input Parsing ====================
def parse_input(user_input: str):
    parts = user_input.strip().split()
    if not parts:
        return None, []
    command = parts[0].lower()
    args = parts[1:]
    return command, args


# ==================== Error Handling Decorator ====================
def input_error(func):
    def wrapper(args, book, view):
        try:
            return func(args, book, view)
        except ValueError as e:
            return f"Error: {e}"
        except IndexError:
            return "Not enough arguments. Please try again."
        except KeyError as e:
            return f"Error: {e}" if str(e) else "This contact does not exist."
        except AttributeError:
            return "This contact does not exist."
        except Exception as e:
            return f"Unexpected error: {e}"

    return wrapper


# ==================== Command Handlers ====================
@input_error
def add_contact(args, book, view):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."

    if phone:
        record.add_phone(phone)

    return message


@input_error
def change_contact(args, book, view):
    name, old_phone, new_phone = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return f"Phone updated for {name}."


@input_error
def show_phone(args, book, view):
    name, *_ = args
    record = book.find(name)

    if not record.phones:
        return f"No phones for {name}."

    phones_str = '; '.join(p.value for p in record.phones)
    return f"Contact name: {name}, phones: {phones_str}"


@input_error
def show_all(args, book, view):
    view.show_contacts(book)
    return None  # View already handled the output


@input_error
def delete_contact(args, book, view):
    name, *_ = args
    book.delete(name)
    return f"Contact {name} deleted."


@input_error
def remove_phone(args, book, view):
    name, phone = args
    record = book.find(name)
    record.remove_phone(phone)
    return f"Phone {phone} removed from {name}."


@input_error
def add_birthday(args, book, view):
    name, birthday = args
    record = book.find(name)
    record.add_birthday(birthday)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args, book, view):
    name, *_ = args
    record = book.find(name)

    if record.birthday:
        return f"{name}'s birthday: {record.birthday}"
    else:
        return f"No birthday set for {name}."


@input_error
def birthdays(args, book, view):
    upcoming = book.get_upcoming_birthdays()
    view.show_birthdays(upcoming)
    return None  # View already handled the output


# ==================== Main Application ====================
def main():
    # Ініціалізація view та завантаження даних
    view = ConsoleView()
    book = load_data()

    # Показуємо привітання
    view.show_welcome()

    while True:
        user_input = view.get_input()
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            view.show_goodbye()
            break
        elif command == "hello":
            view.show_message("How can I help you?")
        elif command == "help":
            view.show_commands()
        elif command == "add":
            result = add_contact(args, book, view)
            if result:
                view.show_message(result)
        elif command == "change":
            result = change_contact(args, book, view)
            if result:
                view.show_message(result)
        elif command == "phone":
            result = show_phone(args, book, view)
            if result:
                view.show_message(result)
        elif command == "all":
            show_all(args, book, view)
        elif command == "add-birthday":
            result = add_birthday(args, book, view)
            if result:
                view.show_message(result)
        elif command == "show-birthday":
            result = show_birthday(args, book, view)
            if result:
                view.show_message(result)
        elif command == "birthdays":
            birthdays(args, book, view)
        elif command == "delete":
            result = delete_contact(args, book, view)
            if result:
                view.show_message(result)
        elif command == "remove":
            result = remove_phone(args, book, view)
            if result:
                view.show_message(result)
        else:
            view.show_message("Invalid command. Type 'help' to see available commands.")


if __name__ == "__main__":
    main()
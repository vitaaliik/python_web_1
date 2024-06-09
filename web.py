from datetime import datetime, timedelta, date
import pickle
from abc import ABC, abstractmethod

class Field:
    pass

class Name(Field):
    def __init__(self, value):
        self.value = value

class Phone(Field):
    def __init__(self, value):
        if not self.validate_phone(value):
            raise ValueError("Phone number must be 10 digits.")
        self.value = value

    @staticmethod
    def validate_phone(value):
        return value.isdigit() and len(value) == 10

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def change_phone(self, old_phone, new_phone):
        old_phone_obj = self.find_phone(old_phone)
        if old_phone_obj is None:
            raise ValueError("Old phone number not found")
        if not Phone.validate_phone(new_phone):
            raise ValueError("Invalid new phone number format")
        old_phone_obj.value = new_phone

    def find_phone(self, phone_value):
        for phone in self.phones:
            if phone.value == phone_value:
                return phone
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

class AddressBook:
    def __init__(self):
        self.records = {}

    def add_record(self, record):
        self.records[record.name.value] = record

    def find(self, name):
        return self.records.get(name, None)

    def get_upcoming_birthdays(self):
        users = prepare_user_list([{"name": record.name.value, "birthday": record.birthday.value.strftime("%Y.%m.%d")} for record in self.records.values() if record.birthday])
        upcoming_birthdays = get_upcoming_birthdays(users)
        return upcoming_birthdays

def string_to_date(date_string):
    return datetime.strptime(date_string, "%Y.%m.%d").date()

def date_to_string(date):
    return date.strftime("%Y.%m.%d")

def prepare_user_list(user_data):
    prepared_list = []
    for user in user_data:
        prepared_list.append({"name": user["name"], "birthday": string_to_date(user["birthday"])})
    return prepared_list

def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)

def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        return find_next_weekday(birthday, 0)
    return birthday

def get_upcoming_birthdays(users, days=7):
    upcoming_birthdays = []
    today = date.today()

    for user in users:
        birthday_this_year = user["birthday"].replace(year=today.year)

        # Перевірка, чи не буде день народження вже наступного року
        if birthday_this_year < today:
            birthday_this_year = birthday_this_year.replace(year=today.year + 1)

        # Перенесення дати на наступний робочий день, якщо день народження припадає на вихідний
        if birthday_this_year.weekday() >= 5:  # 5 - субота, 6 - неділя
            birthday_this_year = find_next_weekday(birthday_this_year, 0)  # Понеділок - 0 день тижня

        days_until_birthday = (birthday_this_year - today).days
        if 0 <= days_until_birthday <= days:
            congratulation_date_str = date_to_string(birthday_this_year)
            upcoming_birthdays.append({"name": user["name"], "congratulation_date": congratulation_date_str})

    return upcoming_birthdays

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Enter user name."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Invalid input format."

    return inner

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

@input_error
def add_contact(args, book):
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
def change_contact(args, book):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record:
        record.change_phone(old_phone, new_phone)
        return "Phone number updated."
    return "Contact not found."

@input_error
def your_number(args, book):
    name = args[0]
    record = book.find(name)
    if record:
        return ", ".join(phone.value for phone in record.phones)
    return "Contact not found."

@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    return "Contact not found."

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return record.birthday.value.strftime("%d.%m.%Y")
    return "Birthday not found."

@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays."

    result = []
    for user in upcoming_birthdays:
        result.append(f"{user['name']}: {user['congratulation_date']}")

    return "\n".join(result)

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

class UserInterface(ABC):
    @abstractmethod
    def display_message(self, message):
        pass

    @abstractmethod
    def display_contacts(self, contacts):
        pass

    @abstractmethod
    def get_user_input(self, prompt):
        pass

class ConsoleInterface(UserInterface):
    def display_message(self, message):
        print(message)

    def display_contacts(self, contacts):
        for contact in contacts:
            print(f"Name: {contact['name']}, Phones: {', '.join(contact['phones'])}, Birthday: {contact['birthday']}")

    def get_user_input(self, prompt):
        return input(prompt)

def main():
    book = load_data()
    ui = ConsoleInterface()
    ui.display_message("Welcome to the assistant bot!")
    while True:
        user_input = ui.get_user_input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            ui.display_message("Good bye!")
            break

        elif command == "hello":
            ui.display_message("How can I help you?")

        elif command == "add":
            ui.display_message(add_contact(args, book))

        elif command == "change":
            ui.display_message(change_contact(args, book))

        elif command == "phone":
            ui.display_message(your_number(args, book))

        elif command == "all":
            contacts = [{"name": name, "phones": [phone.value for phone in record.phones], "birthday": record.birthday.value.strftime("%d.%m.%Y") if record.birthday else "N/A"} for name, record in book.records.items()]
            ui.display_contacts(contacts)

        elif command == "add-birthday":
            ui.display_message(add_birthday(args, book))

        elif command == "show-birthday":
            ui.display_message(show_birthday(args, book))

        elif command == "birthdays":
            ui.display_message(birthdays(args, book))

        else:
            ui.display_message("Invalid command.")

if __name__ == "__main__":
    main()

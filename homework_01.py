from abc import ABC, abstractmethod
from collections import UserDict
import re
import pickle
from datetime import datetime, timedelta


class Field:
    """Base class for entry fields."""

    def __init__(self, value):
        self.value = value


class Name(Field):
    pass


class PhoneNumber(Field):
    def __init__(self, value):
        if not self.validate_phone(value):
            raise ValueError("Niepoprawny numer telefonu")
        super().__init__(value)

    @staticmethod
    def validate_phone(value):
        pattern = re.compile(r"^\d{9}$")
        return pattern.match(value) is not None


class EmailAddress(Field):
    def __init__(self, value):
        if not self.validate_email(value):
            raise ValueError("Niepoprawny adres email")
        super().__init__(value)

    @staticmethod
    def validate_email(value):
        pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        return pattern.match(value) is not None


class BirthDate(Field):
    def __init__(self, value):
        if not self.validate_birthdate(value):
            raise ValueError("Niepoprawna data urodzenia")
        super().__init__(value)

    @staticmethod
    def validate_birthdate(value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False


class Address(Field):
    def __init__(self, street, city, postal_code, country):
        self.street = street
        self.city = city
        self.postal_code = postal_code
        self.country = country
        super().__init__(value=f"{street}, {city}, {postal_code}, {country}")


class Record:
    def __init__(self, name: Name, birthdate: BirthDate = None):
        self.id = None  # The ID will be assigned by AddressBook
        self.name = name
        self.phone_numbers = []
        self.email_addresses = []
        self.birthdate = birthdate
        self.address = None  # Add a new property to store the address

    def add_address(self, address: Address):
        """Adds an address."""
        self.address = address

    def add_phone_number(self, phone_number: PhoneNumber):
        """Adds a phone number."""
        self.phone_numbers.append(phone_number)

    def remove_phone_number(self, phone_number: PhoneNumber):
        """Removes a phone number."""
        self.phone_numbers.remove(phone_number)

    def edit_phone_number(
        self, old_phone_number: PhoneNumber, new_phone_number: PhoneNumber
    ):
        """Changes a phone number."""
        self.remove_phone_number(old_phone_number)
        self.add_phone_number(new_phone_number)

    def add_email_address(self, email_address: EmailAddress):
        """Adds an email address."""
        self.email_addresses.append(email_address)

    def remove_email_address(self, email_address: EmailAddress):
        """Removes an email address."""
        self.email_addresses.remove(email_address)

    def edit_email_address(
        self, old_email_address: EmailAddress, new_email_address: EmailAddress
    ):
        """Changes an email address."""
        self.remove_email_address(old_email_address)
        self.add_email_address(new_email_address)

    def edit_name(self, new_name: Name):
        """Changes the first and last name."""
        self.name = new_name

    def days_to_birthdate(self):
        """Returns the number of days to the next birthdate."""
        if not self.birthdate or not self.birthdate.value:
            return "Brak daty urodzenia"
        today = datetime.now()
        bday = datetime.strptime(self.birthdate.value, "%Y-%m-%d")
        next_birthday = bday.replace(year=today.year)
        if today > next_birthday:
            next_birthday = next_birthday.replace(year=today.year + 1)
        return (next_birthday - today).days

    def __str__(self):
        """Returns a string representation of the entry, including the ID."""
        phone_numbers = ", ".join(
            phone_number.value for phone_number in self.phone_numbers
        )
        email_addresses = ", ".join(
            email_address.value for email_address in self.email_addresses
        )
        birthdate_str = f", Urodziny: {self.birthdate.value}" if self.birthdate else ""
        days_to_birthdate_str = (
            f", Dni do urodzin: {self.days_to_birthdate()}" if self.birthdate else ""
        )
        address_str = f"\nAdres: {self.address.value}" if self.address else ""
        return (
            f"ID: {self.id}, Imię i nazwisko: {self.name.value}, "
            f"Numery telefonów: {phone_numbers}, Adresy email: {email_addresses}{birthdate_str}{days_to_birthdate_str}{address_str}"
        )


class AddressBook(UserDict):
    def __init__(self):
        super().__init__()
        self.next_id = 1
        self.free_ids = set()

    def add_record(self, record: Record):
        """Adds an entry to the address book with ID management."""
        while self.next_id in self.data or self.next_id in self.free_ids:
            self.next_id += 1
        if self.free_ids:
            record.id = min(self.free_ids)
            self.free_ids.remove(record.id)
        else:
            record.id = self.next_id
            self.next_id += 1
        self.data[record.id] = record
        print(f"Dodano wpis z ID: {record.id}.")

    def delete_record_by_id(self):
        """Deletes a record based on ID."""
        user_input = input("Podaj ID rekordu, który chcesz usunąć: ").strip()
        record_id_str = user_input.replace("ID: ", "").strip()

        try:
            record_id = int(record_id_str)
            if record_id in self.data:
                del self.data[record_id]
                self.free_ids.add(record_id)
                print(f"Usunięto rekord o ID: {record_id}.")
            else:
                print("Nie znaleziono rekordu o podanym ID.")
        except ValueError:
            print("Nieprawidłowe ID. Proszę podać liczbę.")

    def find_record(self, search_term):
        """Finds entries containing the exact phrase provided."""
        found_records = []
        for record in self.data.values():
            if search_term.lower() in record.name.value.lower():
                found_records.append(record)
                continue
            for phone_number in record.phone_numbers:
                if search_term in phone_number.value:
                    found_records.append(record)
                    break
            for email_address in record.email_addresses:
                if search_term in email_address.value:
                    found_records.append(record)
                    break
        return found_records

    def find_records_by_name(self, name):
        """Finds records that match the given name and surname."""
        matching_records = []
        for record_id, record in self.data.items():
            if name.lower() in record.name.value.lower():
                matching_records.append((record_id, record))
        return matching_records

    def load(self, file_path="address_book.pickle"):
        """Loads data from a file."""
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
                self.data.update(data)
                if self.data:
                    self.next_id = max(self.data) + 1
        except FileNotFoundError:
            print("Plik nie istnieje. Początkowe załadowanie zakończone.")

    def save(self, file_path="address_book.pickle"):
        """Saves data to a file."""
        with open(file_path, "wb") as f:
            pickle.dump(self.data, f)


class Notebook(UserDict):
    """A class representing a collection of notes."""

    def __init__(self):
        super().__init__()

    def add_note(self, note_title, note_content):
        """Add a new note to the notebook."""
        self.data[note_title] = note_content

    def modify_note_content(self, note_title, new_content):
        """Modify the content of a note."""
        if note_title in self.data:
            self.data[note_title] = new_content
            print("Zaktualizowano notatkę.")
        else:
            print("Nie znaleziono notatki o podanym tytule.")

    def delete_note(self, note_title):
        """Delete a note from the notebook."""
        if note_title in self.data:
            del self.data[note_title]
            print("Usunięto notatkę.")
        else:
            print("Nie znaleziono notatki o podanym tytule.")

    def list_notes(self):
        """List all notes."""
        if not self.data:
            print("Brak notatek.")
        else:
            print("Lista notatek:")
            for title, content in self.data.items():
                print(f"Tytuł: {title}")
                print(f"Treść: {content}")
                print("--------------------------")

    def load_notes(self, file_path="notes.pickle"):
        """Load notes from a file."""
        try:
            with open(file_path, "rb") as f:
                self.data.update(pickle.load(f))
        except FileNotFoundError:
            print("Plik notatek nie istnieje.")


class Tag:
    """A class representing a tag."""

    def __init__(self, notebook):
        self.notebook = notebook

    def tag_note(self, note_title, tag):
        """Add a tag to a note."""
        if note_title in self.notebook.data:
            if "tags" in self.notebook.data[note_title]:
                self.notebook.data[note_title]["tags"].append(tag)
            else:
                self.notebook.data[note_title]["tags"] = [tag]
            print("Dodano tag do notatki.")
        else:
            print("Nie znaleziono notatki o podanym tytule.")

    def find_notes_by_tag(self, tag):
        """Find notes by tag."""
        found_notes = []
        for title, content in self.notebook.data.items():
            if "tags" in content and tag in content["tags"]:
                found_notes.append((title, content))
        return found_notes

    def sort_notes_by_tags(self):
        """Sort notes by tags."""
        sorted_notes = sorted(
            self.notebook.data.items(), key=lambda x: x[1].get("tags", [])
        )
        return sorted_notes


class UserInterface(ABC):
    """Abstract base class for user interface."""

    @abstractmethod
    def display_contacts(self, contacts):
        """Display contacts."""
        pass

    @abstractmethod
    def display_notes(self, notes):
        """Display notes."""
        pass

    @abstractmethod
    def display_commands(self):
        """Display available commands."""
        pass


class ConsoleInterface(UserInterface):
    """Console-based user interface implementation."""

    def display_contacts(self, contacts):
        """Display contacts in console."""
        if not contacts:
            print("Brak kontaktów.")
            return
        for contact in contacts:
            print(contact)

    def display_notes(self, notes):
        """Display notes in console."""
        if not notes:
            print("Brak notatek.")
            return
        for note in notes:
            print(note)

    def display_commands(self):
        """Display available commands in console."""
        print("Dostępne polecenia:")
        print("1. Dodaj kontakt")
        print("2. Znajdź kontakt")
        print("3. Usuń kontakt")
        print("4. Edytuj kontakt")
        print("5. Pokaż wszystkie kontakty")
        print("6. Wyświetl kontakty z najbliższymi urodzinami")
        print("7. Dodaj notatkę")
        print("8. Wyświetl notatki")
        print("9. Edytuj notatkę")
        print("10. Usuń notatkę")
        print("11. Zapisz notatki")
        print("12. Wczytaj notatki")
        print("13. Dodaj tag do notatki")
        print("14. Znajdź notatki po tagu")
        print("15. Posortuj notatki według tagów")
        print("16. Wyjście")


def load_address_book(filename="address_book.pkl"):
    try:
        with open(filename, "rb") as file:
            data = pickle.load(file)
        book = AddressBook()
        book.data = data
        return book
    except FileNotFoundError:
        print("Plik nie istnieje, tworzenie nowej książki adresowej.")
        return AddressBook()
    except Exception as e:
        print(f"Błąd przy ładowaniu książki adresowej: {e}")
        return AddressBook()


class AssistantBot:
    def __init__(self, user_interface):
        self.notebook = Notebook()
        self.notebook.load_notes()
        self.book = load_address_book()
        self.tag_manager = Tag(self.notebook)
        self.user_interface = user_interface

    def main(self):
        while True:
            self.user_interface.display_commands()
            action = input("Wybierz akcję: ")
            if action == "1":
                self.add_contact()
            elif action == "2":
                self.find_contact()
            elif action == "3":
                self.delete_contact()
            elif action == "4":
                self.edit_contact()
            elif action == "5":
                self.display_all_contacts()
            elif action == "6":
                self.display_contacts_with_birthdays()
            elif action == "7":
                self.add_note()
            elif action == "8":
                self.display_all_notes()
            elif action == "9":
                self.edit_note()
            elif action == "10":
                self.delete_note()
            elif action == "11":
                self.save_notes()
            elif action == "12":
                self.load_notes()
            elif action == "13":
                self.add_tag_to_note()
            elif action == "14":
                self.find_notes_by_tag()
            elif action == "15":
                self.sort_notes_by_tags()
            elif action == "16":
                break
            else:
                print("Nieprawidłowa komenda.")

    def add_contact(self):
        name = input("Podaj imię i nazwisko: ")
        birthdate = input("Podaj datę urodzenia w formacie RRRR-MM-DD (opcjonalnie): ")
        if birthdate:
            birthdate = BirthDate(birthdate)
        record = Record(Name(name), birthdate)
        phone_numbers = input("Podaj numery telefonów oddzielone przecinkami: ").split(
            ","
        )
        for number in phone_numbers:
            number = number.strip()
            if number:
                try:
                    phone = PhoneNumber(number)
                    record.add_phone_number(phone)
                except ValueError as e:
                    print(e)
        email_addresses = input("Podaj adresy email oddzielone przecinkami: ").split(
            ","
        )
        for email in email_addresses:
            email = email.strip()
            if email:
                try:
                    email_address = EmailAddress(email)
                    record.add_email_address(email_address)
                except ValueError as e:
                    print(e)
        street = input("Podaj ulicę: ")
        city = input("Podaj miasto: ")
        postal_code = input("Podaj kod pocztowy: ")
        country = input("Podaj kraj: ")
        address = Address(street, city, postal_code, country)
        record.add_address(address)
        self.book.add_record(record)
        print("Kontakt został dodany.")

    def find_contact(self):
        search_term = input(
            "Podaj imię lub nazwisko lub fragment tekstu do wyszukania: "
        )
        found_contacts = self.book.find_record(search_term)
        if found_contacts:
            self.user_interface.display_contacts(found_contacts)
        else:
            print(
                "Nie znaleziono żadnych kontaktów pasujących do podanego wyszukiwania."
            )

    def delete_contact(self):
        self.book.delete_record_by_id()

    def edit_contact(self):
        record_id_str = input("Podaj ID rekordu, który chcesz edytować: ").strip()
        try:
            record_id = int(record_id_str)
            if record_id in self.book.data:
                record = self.book.data[record_id]
                print(f"Aktualne dane kontaktu:\n{record}")
                name = input("Podaj nowe imię i/lub nazwisko (jeśli chcesz zmienić): ")
                if name:
                    record.edit_name(Name(name))
                birthdate = input(
                    "Podaj nową datę urodzenia w formacie RRRR-MM-DD (jeśli chcesz zmienić): "
                )
                if birthdate:
                    try:
                        birthdate = BirthDate(birthdate)
                        record.birthdate = birthdate
                    except ValueError as e:
                        print(e)
                phone_numbers = input(
                    "Podaj nowe numery telefonów oddzielone przecinkami (jeśli chcesz zmienić): "
                ).split(",")
                record.phone_numbers = []
                for number in phone_numbers:
                    number = number.strip()
                    if number:
                        try:
                            phone = PhoneNumber(number)
                            record.add_phone_number(phone)
                        except ValueError as e:
                            print(e)
                email_addresses = input(
                    "Podaj nowe adresy email oddzielone przecinkami (jeśli chcesz zmienić): "
                ).split(",")
                record.email_addresses = []
                for email in email_addresses:
                    email = email.strip()
                    if email:
                        try:
                            email_address = EmailAddress(email)
                            record.add_email_address(email_address)
                        except ValueError as e:
                            print(e)
                street = input("Podaj nową ulicę (jeśli chcesz zmienić): ")
                city = input("Podaj nowe miasto (jeśli chcesz zmienić): ")
                postal_code = input("Podaj nowy kod pocztowy (jeśli chcesz zmienić): ")
                country = input("Podaj nowy kraj (jeśli chcesz zmienić): ")
                if street or city or postal_code or country:
                    address = Address(street, city, postal_code, country)
                    record.address = address
                print("Dane kontaktu zostały zaktualizowane.")
            else:
                print("Nie znaleziono rekordu o podanym ID.")
        except ValueError:
            print("Nieprawidłowe ID. Proszę podać liczbę.")

    def display_all_contacts(self):
        self.user_interface.display_contacts(self.book.data.values())

    def display_contacts_with_birthdays(self):
        today = datetime.now()
        contacts_with_birthdays = [
            record
            for record in self.book.data.values()
            if record.birthdate and record.days_to_birthdate() < 7
        ]
        self.user_interface.display_contacts(contacts_with_birthdays)

    def add_note(self):
        title = input("Podaj tytuł notatki: ")
        content = input("Podaj treść notatki: ")
        self.notebook.add_note(title, content)
        print("Notatka została dodana.")

    def display_all_notes(self):
        self.user_interface.display_notes(self.notebook.data.items())

    def edit_note(self):
        title = input("Podaj tytuł notatki, którą chcesz edytować: ")
        if title in self.notebook.data:
            new_content = input("Podaj nową treść notatki: ")
            self.notebook.modify_note_content(title, new_content)
        else:
            print("Nie znaleziono notatki o podanym tytule.")

    def delete_note(self):
        title = input("Podaj tytuł notatki, którą chcesz usunąć: ")
        if title in self.notebook.data:
            self.notebook.delete_note(title)
            print("Notatka została usunięta.")
        else:
            print("Nie znaleziono notatki o podanym tytule.")

    def save_notes(self):
        self.notebook.save()
        print("Notatki zostały zapisane.")

    def load_notes(self):
        self.notebook.load()
        print("Notatki zostały wczytane.")

    def add_tag_to_note(self):
        title = input("Podaj tytuł notatki, do której chcesz dodać tag: ")
        if title in self.notebook.data:
            tag = input("Podaj tag: ")
            self.tag_manager.tag_note(title, tag)
        else:
            print("Nie znaleziono notatki o podanym tytule.")

    def find_notes_by_tag(self):
        tag = input("Podaj tag, którego notatki chcesz znaleźć: ")
        found_notes = self.tag_manager.find_notes_by_tag(tag)
        self.user_interface.display_notes(found_notes)

    def sort_notes_by_tags(self):
        sorted_notes = self.tag_manager.sort_notes_by_tags()
        self.user_interface.display_notes(sorted_notes)


if __name__ == "__main__":
    user_interface = ConsoleInterface()
    bot = AssistantBot(user_interface)
    bot.main()

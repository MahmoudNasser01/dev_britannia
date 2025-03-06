import requests
from datetime import date
import logging

from .models import Student


logger = logging.getLogger(__name__)


def fetch_google_data(backend, user, response, *args, **kwargs):
    """Fetch gender, phone number, and birthday from Google People API."""

    if backend.name == "google-oauth2":
        access_token = response.get("access_token")

        if not access_token:
            logger.error("Access token missing in response")
            return

        url = "https://people.googleapis.com/v1/people/me?personFields=genders,birthdays,phoneNumbers"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            google_response = requests.get(url, headers=headers).json()

            # Extract Gender
            gender = None
            genders = google_response.get("genders", [])
            if genders and isinstance(genders, list):
                gender = genders[0].get("value")

            # Extract Birthday
            birthday = None
            birthdays = google_response.get("birthdays", [])
            if birthdays and isinstance(birthdays, list):
                for b in birthdays:
                    date_info = b.get("date", {})
                    year = date_info.get("year")
                    month = date_info.get("month")
                    day = date_info.get("day")

                    if month and day:
                        if year:
                            birthday = date(year, month, day)
                        else:
                            birthday = f"XXXX-{month:02d}-{day:02d}"
                        break

            # Extract Phone Number
            phone_number = None
            phone_numbers = google_response.get("phoneNumbers", [])
            if phone_numbers and isinstance(phone_numbers, list):
                for phone in phone_numbers:
                    phone_number = phone.get("value")
                    if phone_number:
                        break

            user.extra_data = {
                "gender": gender,
                "birthday": birthday,
                "phone_number": phone_number,
            }
            user.save()

            logger.info(f"Google data successfully fetched for user: {user.email}")

        except requests.RequestException as e:
            logger.error(f"Request error while fetching Google data: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in Google data processing: {e}")


def create_student_if_not_exist(strategy, details, backend, user=None, *args, **kwargs):
    """Create a Student profile if it does not exist"""

    if not user:
        logger.error("User object is missing.")
        return

    if not getattr(user, "student_profile", None):
        birthday = user.extra_data.get("birthday")

        parsed_birthday = None
        if birthday:
            if isinstance(birthday, date):
                parsed_birthday = birthday

        gender = user.extra_data.get("gender")
        if gender:
            gender = gender.capitalize()
        valid_genders = ["Male", "Female"]
        if gender not in valid_genders:
            gender = None
        phone_number = user.extra_data.get("phone_number")

        full_name = details.get("fullname")

        try:
            Student.objects.create(
                user=user,
                full_name=full_name,
                phone_number=phone_number,
                gender=gender,
                date_of_birth=parsed_birthday,
                is_approved=False,
            )
            logger.info(f"Student profile created for user: {user.email}")
        except Exception as e:
            logger.error(f"Error creating Student profile for {user.email}: {e}")

    else:
        logger.debug(f"Student profile already exists for user: {user.email}")

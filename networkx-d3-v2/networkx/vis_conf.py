from django.conf import settings

MAX_IMPORTANCE = getattr(settings, 'MAX_IMPORTANCE', 30)
MIN_IMPORTANCE = getattr(settings, 'MAX_IMPORTANCE', 1)

ERROR_MESSAGES = {
    'required': 'This field is required.',
    'max_value': 'Ensure this value is less than or equal to %(limit_value)s.',
    'min_value': 'Ensure this value is greater than or equal to %(limit_value)s.',
    'invalid_url': 'Enter a valid URL.',
    'invalid_integer': 'Enter a whole number.',
    'invalid_choice': 'Select a valid choice. %(value)s is not one of the available choices.',
}
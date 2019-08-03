import re
# from https://github.com/seanpianka/Zipcodes
import zipcodes
from emergency_app.models.relation import Relation
from emergency_app.models.nation import Nation
from emergency_app.models.state import State

def validate_email(email):
    """
    Validates that chars are alphaneumeric, there is one '@', and there is a '.' in
    the post-@ string.
    Args:
            email (String): The email to be validated in String format.
    Returns:
            boolean: True if valid, False otherwise.
    """
    if not email:
        return False
    at_count = email.count('@')
    if at_count != 1:
        return False
    # at this point, we know there is only 1 '@'
    split_email = re.split("@", email)
    # now we have validated the pre-@. we need to validate that there is only one . in the post-@
    dot_count = split_email[1].count('.')
    if dot_count != 1:
        return False

    return True


def validate_phone_num_usa(phone_num):
    """
    Validates a phone number in USA by ensuring that there are 10 digits present, the entire input
    is numeric, the first digit is not a 0 or a 1, and the last two digits are not both 1s.
    Args:
            phone_num (String): The phone number to validate in String format.
    Returns:
            boolean: True if valid, False otherwise.
    """
    if not phone_num:
        return False
    # number has a length of 10
    if len(phone_num) != 10:
        return False
    # string consists of all numbers
    for c in phone_num:
        if c.isdigit() == False:
            return False
    # the first digit cannot be a 0 or a 1
    if phone_num[0] == '0' or phone_num[0] == '1':
        return False

    # and the last two digits cannot both be 1s.
    if phone_num[-1] == '1':
        if phone_num[-2] == '1':
            return False

    return True


def validate_zip_usa(zip):
    """
    Validates a zip code in USA
    Args:
            zip code (String): The zip code number to validate in String format
    Returns:
            boolean: True if valid, False otherwise.
    """
    if not zip:
        return False
    if not zipcodes.is_real(zip):
        return False

    return True

# implementing foreign key for relation, state and nation tables would eliminate the need to validate all
def validate_relation(relt_code):
    """
    Validates a relation code
    Args:
            relation code (String): The relation code to validate in String format
    Returns:
            boolean: True if valid, False otherwise.
    """
    try:
        Relation.objects.get(code=relt_code)
    except Relation.DoesNotExist:
        return False

    return True


def validate_state_usa(stat_code):
    """
    Validates a state code in USA
    Args:
            state code (String): The state code to validate in String format
    Returns:
            boolean: True if valid, False otherwise.
    """
    try:
        State.objects.get(id=stat_code)
    except State.DoesNotExist:
        return False

    return True

def validate_nation_code(natn_code):
    """
    Validates a nation code
    Args:
            nation code (String): The nation code to validate in String format
    Returns:
            boolean: True if valid, False otherwise.
    """
    try:
        Nation.objects.get(id=natn_code)
    except Nation.DoesNotExist:
        return False

    return True

def validate_username(username):
    """
    Validates a username by ensuring that it is at least 6 characters length and is entirely
    alphaneumeric with the exception of '_'
    Args:
            username (String): The username to validate in String format.
    Returns:
            boolean: True if valid, False otherwise.
    """
    if not username:
        return False
    if len(username) < 6:
        return False
    for c in username:
        if c.isalnum() == False and c != '_':
            return False

    return True


def validate_checkbox(checkbox):
    """
    Validates a checkbox input by ensuring whether it's 'Y' or 'N' values
    Args:
            checkbox(String): checkbox to validate in String format.
    Returns:
            boolean: True if valid, False otherwise.
    """
    if checkbox == 'Y' or checkbox == 'N':
        return True
    else:
        return False

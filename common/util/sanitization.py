import re

# Validates that chars are alphaneumeric, there is one '@', and there is a '.' in
# the post-@ string.
def validate_email(email):
    at_count = email.count('@')
    if at_count != 1:
        return False
    # at this point, we know there is only 1 '@'
    split_email = re.split("@", email)
    # for the pre-at, we want to make sure that it is alphaneumeric
    if split_email[0].isalnum() == False:
        return False
    # now we have validated the pre-@. we need to validate that there is only one . in the post-@
    dot_count = split_email[1].count('.')
    if dot_count != 1:
        return False

    return True

# unsure what else other than, 10 length, to validate to?
# Wanted to speak to front end guys to see if we can auto populate dashes.
def validate_phone_num(phone_num):
    if len(phone_num) != 10:
        return False

# this enforces that a username be at least 6 characters, only alphaneumeric and _ allowed.
def validate_username(username):
    if len(username) < 6:
        return False
    for c in username:
        if c.isalnum() == False and c != '_':
            return False

    return True

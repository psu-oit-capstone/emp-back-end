from django.test import TestCase
from common.util import sanitization #The file that contains the code for sanitization logic


class SanitizationTests(TestCase):
    """
    Testing for sanitization API calls.
    """
    good_emails = ["dfsg@pdx.edu", "george@gmail.com", "jeff@yahoo.com", "fluffy_flower@instant.com"]
    

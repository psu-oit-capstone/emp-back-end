from django.test import TestCase
from common.util import sanitization #The file that contains the code for sanitization logic


class SanitizationTests(TestCase):
    """
    Testing for sanitization API calls.
    """

    # data stored within lists split among inputs we know to be valid, and invalid.
    # I believe that these examples cover all edge cases of testing.
    good_emails_list = ["dfsg@pdx.edu", "george@gmail.com", "jeff@yahoo.com", "fluffy_flower@instant.com"]
    bad_emails_list = ["df.sd@podf@gmail.com", "george@gmail", "too@many@ampersands@gmail.com"]

    # phone number test lists
    good_phone_list = ["5035552345", "2438574938", "5860385454", "4829304958"]
    bad_phone_list = ["1453456754", "50350350350", "0234523942", "5035035011"]

    # username lists
    good_usernames_list = ["georgeheffley", "super_batman", "extra_25", "gx23mf"]
    bad_usernames_list = ["dfs", "ch@d_heff", "i_can_fly_27&", "after_rise(*)"]

    def test_email_validation(self):
        """
        Testing the email validation algorithm implemented into the validation API.
        Valid inputs return a true, whereas invalid inputs return false. Test only confirms
        that this behavior is as expected.
        """

        """Testing valid email addresses"""
        for data in self.good_emails_list:
            result = sanitization.validate_email(data)
            self.assertTrue(result)

        """Testing invalid email addresses"""
        for data in self.bad_emails_list:
            result = sanitization.validate_email(data)
            self.assertFalse(result)

    def test_phone_validation(self):
        """
        Testing the phone number validation algorithm implemented into the validation API.
        Inputs that are accepted by the API return True, whereas rejected inputs return False.
        This test confirms that this behavior is as expected.
        """

        """Testing valid numbers"""
        for data in self.good_phone_list:
            result = sanitization.validate_phone_num(data)
            self.assertTrue(result)

        """Testing invalid numbers"""
        for data in self.bad_phone_list:
            result = sanitization.validate_phone_num(data)
            self.assertFalse(result)

    def test_username_validation(self):
        """
        Testing the username validation algorithm implemented into the validation API.
        Inputs that are accepted by the API return True, rejected inputs return False.
        This test confirms that this behavior is as expected.
        """

        """Testing valid usernames"""
        for data in self.good_usernames_list:
            result = sanitization.validate_username(data)
            self.assertTrue(result)

        """Testing invalid usernames"""
        for data in self.bad_usernames_list:
            result = sanitization.validate_username(data)
            self.assertFalse(result)

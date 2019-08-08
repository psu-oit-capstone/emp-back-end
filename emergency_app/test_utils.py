from django.test import TestCase
from common.util import jwt_placeholder # JWT generating/authenticating
from common.util import sanitization #The file that contains the code for sanitization logic
import base64 # For checking JWT data
import jwt as jwt_lib # For creating our own JWTs to tamper with

# Need to store this in case of failure during the expiration tests, as new tests will require the original timeout values
original_expiration_time = jwt_placeholder.token_expiration_time

class JWTTests(TestCase):
    """
    Testing out the place-holder JWT generating and validating
    """

    # Data formatted into a json (Python Dictionary)
    good_data_list = [
        { "username":"bob01","Admin":"True" },
        { "username" :"Jimmy09", "Admin" :"False"},
        { "blah" :"blah", "email" :"blah@gmail.com", "username" :"user_name67", "more_filler_data" :"blah blah" }
    ]
    # List of unformatted data
    bad_data_list = [[1,2,3], "This is data!", 0xFF]
    
    # tearDown() gets called after every unit test in this class
    # Reset our jwt_placeholder module's original expiration time NO MATTER WHAT after each test
    def tearDown(self):
        jwt_placeholder.token_expiration_time = original_expiration_time
    
    def test_generate_token(self):
        """
        Testing the generating of JWTs

        Good data should return a formatted plain-text string in the form:
            xxx.yyy.zzz
            where x is header information, y is json payload, and z is a signature
        Bad data should raise a TypeError in jwt_placeholder
        Test only confirms the payload is valid on good data, or that a TypeError is raised on bad data
        """

        """Testing json objects"""
        for data in self.good_data_list:
            jwt = jwt_placeholder.generate_token(data)
            header, payload, signature = str(jwt).split('.')
            self.assertTrue(base64_to_json_compare(payload, data))

        """Testing non-json objects"""
        for data in self.bad_data_list:
            with self.assertRaises(TypeError):
                jwt = jwt_placeholder.generate_token(data)

    def test_validate_token(self):
        """
        Testing the validation of JWTs

        A legitimate JWT should return True
        An illegitimate/tampered JWT should raise an InvalidSignatureError
        An improperly formatted token should raise a DecodeError
        """

        # Grab a JWT and confirm that jwt_placeholder can successfully validate it
        data = self.good_data_list[0]
        jwt = jwt_placeholder.generate_token(data)

        """Testing a valid token"""
        self.assertTrue(jwt_placeholder.validate_token(jwt))

        # Create our own token to try and pass off on the server
        local_key = 'secret'
        wrong_key_jwt = jwt_lib.encode(data, local_key, algorithm='HS256')

        """Testing a token signed with the wrong secret key"""
        with self.assertRaises(jwt_lib.exceptions.InvalidSignatureError):
            ret_val = jwt_placeholder.validate_token(wrong_key_jwt)

        # Tamper with a valid token and try and validate it
        # We'll reuse the jwt from before since it is already vetted
        header, payload, signature = jwt.decode('utf-8').split('.')

        # We'll add additional data to the payload and re-encode it
        tampered_jwt = (header + '.' + payload + "ExtraData" + '.' + signature).encode('utf-8')

        """Testing a token with tampered data"""
        with self.assertRaises(jwt_lib.exceptions.InvalidSignatureError):
            ret_val = jwt_placeholder.validate_token(tampered_jwt)

        """Testing malformed token"""
        with self.assertRaises(jwt_lib.exceptions.DecodeError):
            ret_val = jwt_placeholder.validate_token("Just a regular, unencoded string!")

    def test_grab_token_payload(self):
        """
        Testing the payload-grabbing of JWTs

        The payload/claims used to generate a JWT should matche the output
        from the grab_token_payload function
        """

        """Testing valid and invalid comparisons"""
        for data in self.good_data_list:
            jwt = jwt_placeholder.generate_token(data)
            data_from_JWT = jwt_placeholder.grab_token_payload(jwt)
            """Valid comparison - should be True"""
            self.assertTrue(data == data_from_JWT)
            """Invalid comparison - should be False"""
            for bad_data in self.bad_data_list:
                self.assertFalse(bad_data == data_from_JWT)
    
    def test_token_expiration(self):
        """
        Testing that the JWT's expiration wokrs as expected
        
        Since this unit test exists with the backend, it can manually overide the expiration times
        Will test that a token validates as expected within an expiration period
        Will test that a token is invalid after the expiration period
        """
        # Grab the first good piece of data
        data = self.good_data_list[0]
        
        jwt = jwt_placeholder.generate_token(data)
        
        """ Confirm that our token validates as expected """
        self.assertTrue(jwt_placeholder.validate_token(jwt))
        
        # We'll modify the expiration time, but teardown() will set it back to the original time
        # Set the expiration time to 1 second in the past
        jwt_placeholder.token_expiration_time = -1
        
        # This token, while signed properly, has an expiration date of 1 second ago
        jwt = jwt_placeholder.generate_token(data)

        """ Confirm that our token validation raises an exception """
        with self.assertRaises(jwt_lib.exceptions.ExpiredSignatureError):
            ret_val = jwt_placeholder.validate_token(jwt)


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
    bad_usernames_list = ["d", "ch@d_heff", "i_can_fly_27&", "after_rise(*)"]

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
            result = sanitization.validate_phone_num_usa(data)
            self.assertTrue(result)

        """Testing invalid numbers"""
        for data in self.bad_phone_list:
            result = sanitization.validate_phone_num_usa(data)
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

def base64_to_json_compare(payload, expected):
    """
    Compares a payload received from the JWT generation process
        and the original data which is expected.
        original expected data is formatted to drop spacing between entries
        and change single quotes (') to double quotes (")
    Args:
        payload (base64 str) : the payload portion of our JWT
        expected (dict) : Our original data in dictionary/json format
    Returns:
        True if the formatted 'expected' data matches our 'payload' data
    """
    # base64 decoding requires the payload to be a multiple of 4
    # '=' is the padding char. a maximum padding of 3 '=' is needed.
    base64_padding = '==='

    # The JWT generation formats the string:
    #   Single quotes (') are replaced with double quotes (")
    #   No Spaces between Keys and Values, and no spaces between pairs
    #   e.g. {'key': 'value', 'keyTwo': 'valueTwo'} -> {"key":"value","keyTwo":"valueTwo"}
    # Our expected data should be formatted similarly
    expected = str(expected).replace("'", '"').replace(', ', ',').replace(': ', ':')

    # Our payload is encoded in url-safe base64, we'll decode it for easier comparison
    decoded_payload = base64.urlsafe_b64decode(payload + base64_padding).decode('utf-8')

    return decoded_payload == expected

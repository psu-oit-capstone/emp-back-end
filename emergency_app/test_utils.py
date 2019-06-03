from django.test import TestCase
from common.util import jwt_placeholder # JWT generating/authenticating
import base64 # For checking JWT data
import jwt as jwt_lib # For creating our own JWTs to tamper with


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
		

def base64_to_json_compare(payload, expected):
	"""
	Compares a payload received from the JWT generation process
		and the original data which is expected
		original expected data is formatted to drop spacing between entries
		and change single quotes (') to double quotes (")
	Args:
		payload (base64 str) : the payload portion of our JWT
		expected (dict) : Our original data in dictionary/json format
	Returns:
		True if the formatted 'expected' data matches our 'payload' data
	"""
	# base64 decoding requires the payload to be a multiple of 4
	# '=' is the padding char, which is only consumed until we hit a multiple of 4
	base64_padding = '==='
	
	# The JWT generation formats the string with double-quotes and no spaces after ',' and ':'
	#	Our expected data should be formatted similarly
	expected = str(expected).replace("'", '"').replace(', ', ',').replace(': ', ':')

	# Our payload is encoded in url-safe base64, we'll decode it for easier comparison
	decoded_payload = base64.urlsafe_b64decode(payload + base64_padding).decode('utf-8')

	return decoded_payload == expected

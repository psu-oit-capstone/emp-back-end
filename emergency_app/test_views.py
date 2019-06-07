from django.test import TestCase, Client
from emergency_app import views
from emergency_app.models import identity

import base64 # For checking JWT data
import json # For checking JWT return data

# During testing, localhost:8000 is the base to any URL
base_url = 'http://localhost:8000/'


class AuthorizationTests(TestCase):
	"""
	Testing out the authorization views
	NOTE: Django tests can't interact with the actual database
		Therefore the 'good' and 'bad' value are just hard-coded
		if the database changes then these tests could improperly fail
	"""
	def setUp(self):
		""" Sets up some useful data for Authorization testing """
		self.auth_url = '/login/'
		# Login attempts with invalid usernames results in a 401
		self.unauthorized_code = 401
		# Attempting a GET request on a POST-only method results in a 405
		self.disallowed_method_code = 405
		# Generate some lists of known good and bad usernames
		identity.Identity.objects.create(pidm=1, username='fooBar', first_name='Foo', last_name='Bar', email='fooBar@pdx.edu')
		identity.Identity.objects.create(pidm=2, username='BobbyB', first_name='Bobby', last_name='Baratheon', email='BobbyB@pdx.edu')
		identity.Identity.objects.create(pidm=3, username='GPete', first_name='Gumbo', last_name='Pete', email='Gumby.Petey@pdx.edu')
		self.valid_usernames = ['fooBar', 'BobbyB', 'GPete']
		self.invalid_usernames = ['INVALID_NAME21', 'NOT_A_USERNAME']
		# base64 decoding requires the payload to be a multiple of 4
		# '=' is the padding char. a maximum padding of 3 '=' is needed
		self.base64_padding = '==='
	
	def test_POST_login(self):
		"""
		Testing the backend's view for authrorization of JWTs
		
		Given a valid username in a POST, the backend should return a JWT (str)
		Given an invalid username in a POST, the backend should return a 401 with 'Unauthorized' as text
		"""
		c = Client()
		
		"""Testing valid names via POST"""
		for username in self.valid_usernames:
			response = c.post(self.auth_url, {'username': username})
			self.assertFalse(response.status_code == self.unauthorized_code)
		"""Testing invalid names via POST"""
		for username in self.invalid_usernames:
			response = c.post(self.auth_url, {'username': username})
			self.assertTrue(response.status_code == self.unauthorized_code)
	
	def test_JWT_payload(self):
		"""
		Testing if the returned JWT contains the payload we expect:
			Payload:
				{
					first_name (str)
					last_name (str)
					username (str)
					email (str)
				}
		We won't examine the actual values, just check that the key-value pairs are there
		"""
		c = Client()
		jwts = []
		
		# Gathering the jwts
		for username in self.valid_usernames:
			response = c.post(self.auth_url, {'username': username})
			# Response.content is the byte-version of our JWT. We want it as a string, so decode it first
			jwts.append(response.content.decode('utf-8'))
		
		for jwt in jwts:
			# Grab payload - this will fail the test if we didn't get a token
			header, payload, signature = jwt.split('.')
			decoded_payload = base64.urlsafe_b64decode(payload + self.base64_padding).decode('utf-8')
			payload_json = json.loads(decoded_payload)
			"""Testing for our 4 expected keys - Will raise KeyError on failure"""
			retval = payload_json['first_name']
			retval = payload_json['last_name']
			retval = payload_json['username']
			retval = payload_json['email']

	def test_GET_login(self):
		"""
		Testing the backend's refusal of GET requests
		
		Given any GET request for authenticating, the backend should respond with an error status 405 (disallowed method)
		"""
		c = Client()

		# We won't even load this with data, as any GET request for authentication should receive error 405
		response = c.get(self.auth_url)

		self.assertTrue(response.status_code == self.disallowed_method_code)
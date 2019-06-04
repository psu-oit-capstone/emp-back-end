from django.test import TestCase
from emergency_app import views

import base64 # For checking JWT data
import json # For checking JWT return data
import requests # requests allows us to make GET/POST requests. Required for testing Django views

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
		self.auth_url = base_url + 'login/'
		# Login attempts with invalid usernames results in a 401
		self.unauthorized_code = 401
		# Attempting a GET request on a POST-only method results in a 405
		self.disallowed_method = 405
		# Generate some lists of known good and bad usernames
		self.valid_usernames = ['aaarse', 'faatif', 'caba', 'kabboo']
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
		POST_body = {}
		"""Testing valid names via POST"""
		for username in self.valid_usernames:
			# The only thing our SSO placeholder looks for is the username
			POST_body['username'] = username
			response = requests.post(url=self.auth_url, data=POST_body)
			self.assertFalse(response.status_code == self.unauthorized_code)
		"""Testing invalid names via POST"""
		for username in self.invalid_usernames:
			POST_body['username'] = username
			response = requests.post(url=self.auth_url, data=POST_body)
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
		jwts = []
		POST_body = {}
		# Gathering the jwts
		for username in self.valid_usernames:
			POST_body['username'] = username
			response = requests.post(url=self.auth_url, data=POST_body)
			# JWTS are returned as http response text
			jwts.append(response.text)
		
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
		get_params = {'username':self.valid_usernames[0]}
		
		get_response = requests.get(url=self.auth_url, data=get_params)
		
		self.assertTrue(get_response.status_code == self.disallowed_method)
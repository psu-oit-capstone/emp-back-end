from django.test import TestCase, Client
from emergency_app import views
from emergency_app.models import identity, contact

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
		self.disallowed_method_code = 405
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
		
		self.assertTrue(get_response.status_code == self.disallowed_method_code)

class DataRequestTests(TestCase):
	"""
	Testing out the data request views
	
	Testing uses an empty temp data base - so it must be filled prior to any queries
	"""
	
	def setUp(self):
		self.get_contacts_url = '/getEmergencyContacts/'
		self.auth_url = '/login/'
		# Data requests for users that lack any entries in the database result in No Content (204) return
		self.success_code = 200
		self.no_content_code = 204
		self.unauthorized_code = 401
		
		# Create a user who will have data in the (test) contact database
		identity.Identity.objects.create(pidm=123, username='fooBar', first_name='Foo', last_name='Bar', email='fooBar@pdx.edu')
		self.username_with_data = 'fooBar'
		self.pidm_with_data = 123
		# Add two contacts for 'user_with_data' - no need to populate every field
		contact.Contact.objects.create(surrogate_id=1, pidm=123, first_name="Debby", last_name='Bar')
		contact.Contact.objects.create(surrogate_id=2, pidm=123, first_name="Jim", last_name='Bar')
		
		# Create a user who won't have data in the (test) contact database
		identity.Identity.objects.create(pidm=456, username='TommyZ', first_name='Tom', last_name='Zero-friends', email='TomZ@pdx.edu')
		self.username_without_data = 'TommyZ'
		
		# Create a Contact entry that isn't linked to either user
		contact.Contact.objects.create(surrogate_id=3, pidm=789, first_name="Billy", last_name='Kid')

		
	def test_get_emergency_contacts(self):
		"""
		Testing that get_emergency_contacts returns expected values and status codes
		
		One user will have contact data and test his request (200 response code)
		One user will have no contact data and test his request (204 response code)
		One user will have an invalid JWT and test his request (401 response code)
		"""
		# Using Django's Client means our views will access the test database
		c = Client()
				
		# First, generate a token for our users
		# User with data's JWT
		response = c.post(self.auth_url, {'username': self.username_with_data})
		user_with_data_jwt = response.content.decode('utf-8')
		# User without data's JWT
		response = c.post(self.auth_url, {'username': self.username_without_data})
		user_without_data_jwt = response.content.decode('utf-8')
		
		# Request the contact info for the user with data
		response = c.post(self.get_contacts_url, {'jwt': user_with_data_jwt})
		"""Testing that we received a 200 success response"""
		self.assertTrue(response.status_code == self.success_code)
		# Load the contacts in dictionary/JSON format
		contacts = json.loads(response.content)
		"""Testing that the contacts returned are linked to our user with data"""
		for contact in contacts:
			self.assertTrue(contact['pidm'] == self.pidm_with_data)
		
		# Now to test that users without data receive a No Content (204) response
		response = c.post(self.get_contacts_url, {'jwt': user_without_data_jwt})
		"""Testing that we received a 204 No Content response"""
		self.assertTrue(response.status_code == self.no_content_code)
		"""Testing that there's no contacts returned"""
		self.assertTrue(len(response.content) == 0)

		# Now test a user who doesn't supply a valid JWT
		response = c.post(self.get_contacts_url, {'jwt': 'No token here!'})
		"""Testing that back-end reports a 401 Unauthorized"""
		self.assertTrue(response.status_code == self.unauthorized_code)
		

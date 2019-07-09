from django.test import TestCase, Client
from django.utils import timezone	# For timestamp verification
from emergency_app import views
from emergency_app.models import identity, contact, emergency

import base64 # For checking JWT data
import json # For checking JWT return data

# During testing, localhost:8000 is the base to any URL
base_url = 'http://localhost:8000/'


class AuthorizationTests(TestCase):
	"""
	Testing out the authorization views
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
			self.assertNotEqual(response.status_code, self.unauthorized_code)
		"""Testing invalid names via POST"""
		for username in self.invalid_usernames:
			response = c.post(self.auth_url, {'username': username})
			self.assertEqual(response.status_code, self.unauthorized_code)
	
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

		self.assertEqual(response.status_code, self.disallowed_method_code)

class DataRequestTests(TestCase):
	"""
	Testing out the data request views
	
	Testing uses an empty temp data base - so it must be filled prior to any queries
	"""
	
	def setUp(self):
		self.get_contacts_url = '/getEmergencyContacts/'
		self.get_alert_info_url = '/getAlertInfo/'
		self.auth_url = '/login/'
		
		# Expected response codes from the back-end
		self.success_code = 200 # Successful request, with return data
		self.no_content_code = 204 # Successful request, but no data found
		self.unauthorized_code = 401 # Unauthorized user, either no JWT, malformed JWT, or a non server-signed JWT
		
		""" Our user entry with contacts and alert info set up """ 
		# Create a user who will have data in the (test) contact database
		identity.Identity.objects.create(pidm=123, username='fooBar', first_name='Foo', last_name='Bar', email='fooBar@pdx.edu')
		self.username_with_data = 'fooBar'
		self.pidm_with_data = 123
		# Create a user who won't have data in the (test) contact database
		""" Our user entry without contacts or alert info set up """
		identity.Identity.objects.create(pidm=456, username='TommyZ', first_name='Tom', last_name='Zero-friends', email='TomZ@pdx.edu')
		self.username_without_data = 'TommyZ'
		
		""" Contact information entries """
		# Add two contacts for 'user_with_data' - no need to populate every field
		contact.Contact.objects.create(surrogate_id=1, pidm=123, first_name="Debby", last_name='Bar')
		contact.Contact.objects.create(surrogate_id=2, pidm=123, first_name="Jim", last_name='Bar')	
		# Create a Contact entry that isn't linked to either user
		contact.Contact.objects.create(surrogate_id=3, pidm=789, first_name="Billy", last_name='Kid')

		""" Emergency information entry """
		self.external_email = "fooMaster77@hotmail.com"
		self.campus_email="fooBar@pdx.edu"
		self.primary_phone='5031234567'
		self.alternate_phone='9979876543'
		self.sms_status_ind='Y'
		self.sms_device='5030102929'
		self.timestamp= timezone.now()
		# Add data for 'fooBar'/pidm 123 user into the alert info (emergency) database
		emergency.Emergency.objects.create(pidm=123, external_email=self.external_email,
											campus_email=self.campus_email, primary_phone=self.primary_phone,
											alternate_phone=self.alternate_phone, sms_status_ind = self.sms_status_ind,
											sms_device=self.sms_device)#, activity_date=self.activity_date)
		
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
		# Decode the JWT from json to string format (which is what the API expects)
		user_with_data_jwt = response.content.decode('utf-8')
		# User without data's JWT
		response = c.post(self.auth_url, {'username': self.username_without_data})
		user_without_data_jwt = response.content.decode('utf-8')
		
		# Request the contact info for the user with data
		response = c.post(self.get_contacts_url, HTTP_AUTHORIZATION=user_with_data_jwt)
		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, self.success_code)
		# Load the contacts in dictionary/JSON format
		contacts = json.loads(response.content)
		"""Testing that the contacts returned are linked to our user with data"""
		for contact in contacts:
			self.assertEqual(contact['pidm'], self.pidm_with_data)
		
		# Now to test that users without data receive a No Content (204) response
		response = c.post(self.get_contacts_url, HTTP_AUTHORIZATION=user_without_data_jwt)
		"""Testing that we received a 204 No Content response"""
		self.assertEqual(response.status_code, self.no_content_code)
		"""Testing that there's no contacts returned"""
		self.assertEqual(len(response.content), 0)

		# # Now test a user who doesn't supply a valid JWT
		response = c.post(self.get_contacts_url, HTTP_AUTHORIZATION="No Token Here!")
		"""Testing that back-end reports a 401 Unauthorized"""
		self.assertEqual(response.status_code, self.unauthorized_code)
		
	def test_get_alert_info(self):
		"""
		Testing that get_alert_info returns expected values and status codes
		
		One user will have alert info and test his request (200 response code and meaningful data returned)
		One user will have no alert info and test his request (204 response code)
		One user will have an invalid JWT and test his request (401 response code)
		"""
		# Using Django's client to access the temporary test database
		c = Client()
		
		# Generate our JWTs
		response = c.post(self.auth_url, {'username': self.username_with_data})
		# Decode the JWT from json to string format (which is what the API expects)
		user_with_data_jwt = response.content.decode('utf-8')
		# Grab our user without any alert info's JWT
		response = c.post(self.auth_url, {'username': self.username_without_data})
		user_without_data_jwt = response.content.decode('utf-8')
		
		# Request the alert info for our user with data
		response = c.post(self.get_alert_info_url, HTTP_AUTHORIZATION=user_with_data_jwt)
		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, self.success_code)
		# Load the alert info list into a dictionary/JSON format
		alert_info = json.loads(response.content)[0]
		
		"""Testing that the alert info returned is as expected"""
		self.assertEqual(alert_info['external_email'], self.external_email)
		self.assertEqual(alert_info['primary_phone'], self.primary_phone)
		self.assertEqual(alert_info['alternate_phone'], self.alternate_phone)
		self.assertEqual(alert_info['sms_status_ind'], self.sms_status_ind)
		self.assertEqual(alert_info['sms_device'], self.sms_device)
		# Rather than try and validate down to the millisecond, we'll just validate that the year-month-day match expected values
		# database timestamp format: YYYY-MM-DDTHH:MM:SS.(Milliseconds)Z
		truncated_database_timestamp = alert_info['activity_date'].split('T')[0]
		#local timestamp format: YYYY-MM-DD HH:MM:SS.(Milliseconds)+00:00
		truncated_local_timestamp = str(self.timestamp).split(' ')[0]
		self.assertEqual(truncated_database_timestamp, truncated_local_timestamp)
		
		"""We didn't provide evacuation_assistance info, so we'll confirm that it is null"""
		self.assertEqual(alert_info['evacuation_assistance'], None)
		
		# Request the alert info for our user without data
		response = c.post(self.get_alert_info_url, HTTP_AUTHORIZATION=user_without_data_jwt)
		"""Testing that we received a 204 No Content response"""
		self.assertEqual(response.status_code, self.no_content_code)
		"""Testing taht there's no data returned"""
		self.assertEqual(len(response.content), 0)
		
		# Test a user who doesn't supply a valid JWT
		response = c.post(self.get_contacts_url, HTTP_AUTHORIZATION="No Token Here!")
		"""Testing that back-end reports a 401 Unauthorized"""
		self.assertEqual(response.status_code, self.unauthorized_code)

class DataWriteTests(TestCase):
	"""
	Testing out views that change the database
	
	Tests adding data and removing data from the database via Django views
	"""
	
	def setUp(self):
		self.set_alert_info_url = '/setRequestAssistance/'
		self.auth_url = '/login/'
		
		# Expected response codes from the back-end
		self.success_code = 200 # Successful request, with return data
		self.unauthorized_code = 401 # Unauthorized user, either no JWT, malformed JWT, or a non server-signed JWT
		self.unprocessable_entity = 422 # Arguments were provided correctly, but were semantically incorrect (such as invalid email/phone number)
		
		""" Our dummy-data user """ 
		# Create a user who will update their data in the (test) alert-info database
		identity.Identity.objects.create(pidm=123, username='fooBar', first_name='Foo', last_name='Bar', email='fooBar@pdx.edu')
		self.username_with_valid_data = 'fooBar'
		self.user_pidm_with_valid_data = 123

		identity.Identity.objects.create(pidm=456, username='badData', first_name='Bad', last_name='Data', email='badData@pdx.edu')
		self.username_with_invalid_data = 'badData'
		self.user_pidm_with_invalid_data = 456

		""" Valid Emergency information we'll use as the user data """
		self.good_evacuation_assistance = 'Y'
		self.good_external_email = "fooMaster77@hotmail.com"
		self.good_primary_phone = '5031234567'
		self.good_alternate_phone = '9979876543'
		self.good_sms_status_ind = 'Y'
		self.good_sms_device = '5030102929'
		
		""" Additional valid email and phone number to update database with """
		self.additional_good_external_email = "barKing200@yahoo.com"
		self.additional_good_alternate_phone = "5039876543"
		
		""" Invalid Emergency information we'll user as the invalid user data """
		self.bad_evacuation_assistance = '?'
		self.bad_external_email = "BadEmail!"
		self.bad_primary_phone='123'
		self.bad_alternate_phone='456'
		self.bad_sms_status_ind='Nope!'
		self.bad_sms_device='No-Phone!'
	
	def test_set_alert_info(self):
		"""
		Testing that set_alert_info returns expected status codes and changes are made to the database
		
		One user will attempt to create an entry into the database with valid data
		One user will attempt to create an entry into the database with invalid data
		One user will attempt to update their database entry with valid data
		One user will attempt to update their database entry with invalid data
		
		One user will have an invalid JWT and test his request (401 response code)
		"""
		# Using Django's client to access the temporary test database
		c = Client()
		
		# Generate our JWTs
		response = c.post(self.auth_url, {'username': self.username_with_valid_data})
		# Decode the JWT from json to string format (which is what the API expects)
		user_with_valid_data_jwt = response.content.decode('utf-8')
		# Grab our user without any alert info's JWT
		response = c.post(self.auth_url, {'username': self.username_with_invalid_data})
		user_without_invalid_data_jwt = response.content.decode('utf-8')
		
		# Attempt to enter in a new entry with valid data
		response = c.post(self.set_alert_info_url,
		# POST body
		{
			'evacuation_assistance':self.good_evacuation_assistance,
			'external_email':self.good_external_email,
			'primary_phone':self.good_primary_phone,
			'alternate_phone':self.good_alternate_phone,
			'sms_status_ind':self.good_sms_status_ind,
			'sms_device':self.good_sms_device
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)
		
		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, self.success_code)
		
		# Grab the valid user's Emergency alert info
		user_entry = emergency.Emergency.objects.get(pidm=self.user_pidm_with_valid_data)
		
		"""Testing that the data is uploaded to the registry correctly"""
		# Now compare each value, asserting their equivalence
		self.assertEqual(user_entry.evacuation_assistance, self.good_evacuation_assistance)
		self.assertEqual(user_entry.external_email, self.good_external_email)
		self.assertEqual(user_entry.primary_phone, self.good_primary_phone)
		self.assertEqual(user_entry.alternate_phone, self.good_alternate_phone)
		self.assertEqual(user_entry.sms_status_ind, self.good_sms_status_ind)
		self.assertEqual(user_entry.sms_device, self.good_sms_device)
		
		# Attempt to update our valid database entry with more valid data
		response = c.post(self.set_alert_info_url,
		# POST body
		{
			'evacuation_assistance':self.good_evacuation_assistance,
			'external_email':self.additional_good_external_email,
			'primary_phone':self.good_primary_phone,
			'alternate_phone':self.additional_good_alternate_phone,
			'sms_status_ind':self.good_sms_status_ind,
			'sms_device':self.good_sms_device
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)
		
		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, self.success_code)
		
		# Grab the valid user's Emergency alert info
		user_entry = emergency.Emergency.objects.get(pidm=self.user_pidm_with_valid_data)
		
		"""Testing that the data is updated correctly"""
		self.assertEqual(user_entry.evacuation_assistance, self.good_evacuation_assistance)
		self.assertEqual(user_entry.external_email, self.additional_good_external_email)
		self.assertEqual(user_entry.primary_phone, self.good_primary_phone)
		self.assertEqual(user_entry.alternate_phone, self.additional_good_alternate_phone)
		self.assertEqual(user_entry.sms_status_ind, self.good_sms_status_ind)
		self.assertEqual(user_entry.sms_device, self.good_sms_device)
		
		# Bad data testing #
		# Attempt to enter in a new entry with invalid data
		response = c.post(self.set_alert_info_url,
		# POST body
		{
			'evacuation_assistance':self.bad_evacuation_assistance,
			'external_email':self.bad_external_email,
			'primary_phone':self.bad_primary_phone,
			'alternate_phone':self.bad_alternate_phone,
			'sms_status_ind':self.bad_sms_status_ind,
			'sms_device':self.bad_sms_device
		},
		# POST headers
		HTTP_AUTHORIZATION=user_without_invalid_data_jwt
		)
		
		"""Testing that we received a 422 unprocessable entity failure response"""
		self.assertEqual(response.status_code, self.unprocessable_entity)
		
		# Attempt to grab data for the invalid entry - should return an empty list
		user_entry = emergency.Emergency.objects.filter(pidm=self.user_pidm_with_invalid_data)
		
		"""Testing that the database did NOT update with this invalid data, returning nothing"""
		self.assertEqual(len(user_entry), 0)
		
		# Attempt to update our already-validated database entry with new, invalid data
		response = c.post(self.set_alert_info_url,
		# POST body
		{
			'evacuation_assistance':self.bad_evacuation_assistance,
			'external_email':self.bad_external_email,
			'primary_phone':self.bad_primary_phone,
			'alternate_phone':self.bad_alternate_phone,
			'sms_status_ind':self.bad_sms_status_ind,
			'sms_device':self.bad_sms_device
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)
		
		"""Testing that we received a 422 unprocessable entity failure response"""
		self.assertEqual(response.status_code, self.unprocessable_entity)
		
		# Grab the valid user's Emergency alert info
		user_entry = emergency.Emergency.objects.get(pidm=self.user_pidm_with_valid_data)
		
		"""Testing that the database did NOT update our old entry with the new invalid data"""
		self.assertEqual(user_entry.evacuation_assistance, self.good_evacuation_assistance)
		self.assertEqual(user_entry.external_email, self.additional_good_external_email)
		self.assertEqual(user_entry.primary_phone, self.good_primary_phone)
		self.assertEqual(user_entry.alternate_phone, self.additional_good_alternate_phone)
		self.assertEqual(user_entry.sms_status_ind, self.good_sms_status_ind)
		self.assertEqual(user_entry.sms_device, self.good_sms_device)
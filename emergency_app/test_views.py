from django.test import TestCase, Client
from django.utils import timezone	# For timestamp verification
from emergency_app import views
from emergency_app.models import identity, contact, emergency

import base64 # For checking JWT data
import json # For checking JWT return data

# During testing, localhost:8000 is the base to any URL
base_url = 'http://localhost:8000/'
# Backend API URLs
# Authentication Url
auth_url = '/login/'
# Emergency Notification Urls
get_emergency_notifications_url = '/getEmergencyNotifications/'
set_emergency_notifications_url = '/setEmergencyNotifications/'
# Evacuation Assistance Urls
get_evacuation_assistance_url = '/getEvacuationAssistance/'
set_evacuation_assistance_url = '/setEvacuationAssistance/'
# Emergency Contacts Urls
get_contacts_url = '/getEmergencyContacts/'
set_contacts_url = '/updateEmergencyContact/'
# Common HTTP Return statuses
success_code = 200 # Successful request, with return data
no_content_code = 204 # Successful request, but no data to return
unauthorized_code = 401 # Authorization failed
disallowed_method_code = 405 # Attempting to access this API call with the incorrect request type
unprocessable_entity = 422 # Required fields were provided, but are semantically incorrect (e.g. garbage email)

class AuthorizationTests(TestCase):
	"""
	Testing out the authorization views
	"""
	def setUp(self):
		""" Sets up some useful data for Authorization testing """
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
			response = c.post(auth_url, {'username': username})
			self.assertNotEqual(response.status_code, unauthorized_code)
		"""Testing invalid names via POST"""
		for username in self.invalid_usernames:
			response = c.post(auth_url, {'username': username})
			self.assertEqual(response.status_code, unauthorized_code)

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
			response = c.post(auth_url, {'username': username})
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
		response = c.get(auth_url)

		self.assertEqual(response.status_code, disallowed_method_code)

class EmergencyNotificationTests(TestCase):
	"""
	Testing out the setting and getting of Alert Info
	"""

	def setUp(self):
		""" Our user entry with emergency notifications info set up """
		# Create a user who will have data in the (test) contact database
		identity.Identity.objects.create(pidm=123, username='fooBar', first_name='Foo', last_name='Bar', email='fooBar@pdx.edu')
		self.username_with_data = 'fooBar'
		self.pidm_with_data = 123

		# Create a user who won't have data in the (test) contact database
		""" Our user entry without emergency notifications info set up """
		identity.Identity.objects.create(pidm=456, username='TommyZ', first_name='Tom', last_name='Zero-friends', email='TomZ@pdx.edu')
		self.username_without_data = 'TommyZ'
		self.pidm_without_data = 456

		# Create a user who will have bad values to upload to the database
		""" Our user entry with invalid data for the emergency notifications """
		identity.Identity.objects.create(pidm=789, username='badData', first_name='Bad', last_name='Data', email='badData@pdx.edu')
		self.username_with_invalid_data = 'badData'
		self.user_pidm_with_invalid_data = 789

		""" Emergency information entry """
		""" Valid Emergency information we'll use as the user data """
		self.campus_email = 'fooBar@pdx.edu'
		self.good_external_email = "fooMaster77@hotmail.com"
		self.good_primary_phone = '5031234567'
		self.good_alternate_phone = '9979876543'
		self.good_sms_status_ind = 'Y'
		self.good_sms_device = '5030102929'
		self.timestamp= timezone.now()
		# Add data for 'fooBar'/pidm 123 user into the emergency notifications info (emergency) database
		emergency.Emergency.objects.create(pidm=self.pidm_with_data, external_email=self.good_external_email,
											campus_email=self.campus_email, primary_phone=self.good_primary_phone,
											alternate_phone=self.good_alternate_phone, sms_status_ind = self.good_sms_status_ind,
											sms_device=self.good_sms_device)

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

	def test_get_emergency_notifications(self):
		"""
		Testing that get_emergency_notifications returns expected values and status codes

		One user will have emergency notifications info info and test his request (200 response code and meaningful data returned)
		One user will have no emergency notifications info and test his request (204 response code)
		One user will have an invalid JWT and test his request (401 response code)
		"""
		# Using Django's client to access the temporary test database
		c = Client()

		# Generate our JWTs
		response = c.post(auth_url, {'username': self.username_with_data})
		# Decode the JWT from json to string format (which is what the API expects)
		user_with_data_jwt = response.content.decode('utf-8')
		# Grab our user without any emergency notifications info's JWT
		response = c.post(auth_url, {'username': self.username_without_data})
		user_without_data_jwt = response.content.decode('utf-8')

		# Request the emergency notifications info for our user with data
		response = c.post(get_emergency_notifications_url, HTTP_AUTHORIZATION=user_with_data_jwt)
		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, success_code)
		# Load the emergency notifications info list into a dictionary/JSON format
		emergency_notifications = json.loads(response.content)[0]

		"""Testing that the emergency notifications info returned is as expected"""
		self.assertEqual(emergency_notifications['external_email'], self.good_external_email)
		self.assertEqual(emergency_notifications['primary_phone'], self.good_primary_phone)
		self.assertEqual(emergency_notifications['alternate_phone'], self.good_alternate_phone)
		self.assertEqual(emergency_notifications['sms_status_ind'], self.good_sms_status_ind)
		self.assertEqual(emergency_notifications['sms_device'], self.good_sms_device)
		# Rather than try and validate down to the millisecond, we'll just validate that the year-month-day match expected values
		# database timestamp format: YYYY-MM-DDTHH:MM:SS.(Milliseconds)Z
		truncated_database_timestamp = emergency_notifications['activity_date'].split('T')[0]
		#local timestamp format: YYYY-MM-DD HH:MM:SS.(Milliseconds)+00:00
		truncated_local_timestamp = str(self.timestamp).split(' ')[0]
		self.assertEqual(truncated_database_timestamp, truncated_local_timestamp)

		# Request the emergency notifications info for our user without data
		response = c.post(get_emergency_notifications_url, HTTP_AUTHORIZATION=user_without_data_jwt)
		"""Testing that we received a 204 No Content response"""
		self.assertEqual(response.status_code, no_content_code)
		"""Testing taht there's no data returned"""
		self.assertEqual(len(response.content), 0)

		# Test a user who doesn't supply a valid JWT
		response = c.post(get_emergency_notifications_url, HTTP_AUTHORIZATION="No Token Here!")
		"""Testing that back-end reports a 401 Unauthorized"""
		self.assertEqual(response.status_code, unauthorized_code)

	def test_set_emergency_notifications(self):
		"""
		Testing that set_emergency_notifications returns expected status codes and changes are made to the database

		One user will attempt to create an entry into the database with valid data
		One user will attempt to create an entry into the database with invalid data
		One user will attempt to update their database entry with valid data
		One user will attempt to update their database entry with invalid data

		One user will have an invalid JWT and test his request (401 response code)
		"""
		# Using Django's client to access the temporary test database
		c = Client()

		# Generate our JWTs
		response = c.post(auth_url, {'username': self.username_with_data})
		# Decode the JWT from json to string format (which is what the API expects)
		user_with_valid_data_jwt = response.content.decode('utf-8')
		# Grab our user without any emergency notifications info's JWT
		response = c.post(auth_url, {'username': self.username_with_invalid_data})
		user_without_invalid_data_jwt = response.content.decode('utf-8')

		# Attempt to enter in a new entry with valid data
		response = c.post(set_emergency_notifications_url,
		# POST body
		{
			# 'evacuation_assistance':self.good_evacuation_assistance,
			'external_email':self.good_external_email,
			'primary_phone':self.good_primary_phone,
			'alternate_phone':self.good_alternate_phone,
			'sms_status_ind':self.good_sms_status_ind,
			# 'sms_device':self.good_sms_device
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)

		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, success_code)

		# Grab the valid user's Emergency emergency notifications info
		user_entry = emergency.Emergency.objects.get(pidm=self.pidm_with_data)

		"""Testing that the data is uploaded to the registry correctly"""
		# Now compare each value, asserting their equivalence
		# self.assertEqual(user_entry.evacuation_assistance, self.good_evacuation_assistance)
		self.assertEqual(user_entry.external_email, self.good_external_email)
		self.assertEqual(user_entry.primary_phone, self.good_primary_phone)
		self.assertEqual(user_entry.alternate_phone, self.good_alternate_phone)
		self.assertEqual(user_entry.sms_status_ind, self.good_sms_status_ind)
		# self.assertEqual(user_entry.sms_device, self.good_sms_device)

		# Attempt to update our valid database entry with more valid data - this time opting in for sms service
		response = c.post(set_emergency_notifications_url,
		# POST body
		{
			# 'evacuation_assistance':self.good_evacuation_assistance,
			'external_email':self.additional_good_external_email,
			'primary_phone':self.good_primary_phone,
			'alternate_phone':self.additional_good_alternate_phone,
			'sms_device':self.good_sms_device
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)

		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, success_code)

		# Grab the valid user's Emergency emergency notifications info
		user_entry = emergency.Emergency.objects.get(pidm=self.pidm_with_data)

		"""Testing that the data is updated correctly"""
		# self.assertEqual(user_entry.evacuation_assistance, self.good_evacuation_assistance)
		self.assertEqual(user_entry.external_email, self.additional_good_external_email)
		self.assertEqual(user_entry.primary_phone, self.good_primary_phone)
		self.assertEqual(user_entry.alternate_phone, self.additional_good_alternate_phone)
		self.assertEqual(user_entry.sms_status_ind, None)
		self.assertEqual(user_entry.sms_device, self.good_sms_device)

		# Bad data testing #
		# Attempt to enter in a new entry with invalid data
		response = c.post(set_emergency_notifications_url,
		# POST body
		{
			# 'evacuation_assistance':self.bad_evacuation_assistance,
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
		self.assertEqual(response.status_code, unprocessable_entity)

		# Attempt to grab data for the invalid entry - should return an empty list
		user_entry = emergency.Emergency.objects.filter(pidm=self.user_pidm_with_invalid_data)

		"""Testing that the database did NOT update with this invalid data, returning nothing"""
		self.assertEqual(len(user_entry), 0)

		# Attempt to update our already-validated database entry with new, invalid data
		response = c.post(set_emergency_notifications_url,
		# POST body
		{
			# 'evacuation_assistance':self.bad_evacuation_assistance,
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
		self.assertEqual(response.status_code, unprocessable_entity)

		# Grab the valid user's Emergency emergency notifications info
		user_entry = emergency.Emergency.objects.get(pidm=self.pidm_with_data)

		"""Testing that the database did NOT update our old entry with the new invalid data."""
		# self.assertEqual(user_entry.evacuation_assistance, self.good_evacuation_assistance)
		self.assertEqual(user_entry.external_email, self.additional_good_external_email)
		self.assertEqual(user_entry.primary_phone, self.good_primary_phone)
		self.assertEqual(user_entry.alternate_phone, self.additional_good_alternate_phone)
		# self.assertEqual(user_entry.sms_status_ind, self.good_sms_status_ind)
		self.assertEqual(user_entry.sms_device, self.good_sms_device)

class EvacuationAssistanceTests(TestCase):
	"""
	Testing out the setting and getting of Evacuation Assistance Info
	"""

	def setUp(self):
		""" Our user entry with valid info set up """
		identity.Identity.objects.create(pidm=123, username='fooBar', first_name='Foo', last_name='Bar', email='fooBar@pdx.edu')
		self.username_with_data = 'fooBar'
		self.pidm_with_data = 123

		""" Our user without evac assistance info set up """
		identity.Identity.objects.create(pidm=456, username='TommyZ', first_name='Tom', last_name='Zero-friends', email='TomZ@pdx.edu')
		self.username_without_data = 'TommyZ'
		self.pidm_without_data = 456

		""" Our user entry who doesn't exist in the Emergency database yet """
		identity.Identity.objects.create(pidm=789, username='JBob', first_name='Jim', last_name='Bob', email='JBob@pdx.edu')
		self.username_without_emergency_entry = 'JBob'
		self.pidm_without_emergency_entry = 789

		# The only valid status is 'Y' or None
		self.valid_status = 'Y'
		# We'll attempt to update with an invalid status, which shouldn't be accepted by the backend
		self.invalid_status = 'invalid!'

		# The user entry with evacuation_assistance set to 'Y'
		emergency.Emergency.objects.create(pidm=self.pidm_with_data, evacuation_assistance=self.valid_status)
		# The user entry with no evacuation_assistance data set
		emergency.Emergency.objects.create(pidm=self.pidm_without_data)

	def test_get_evacuation_assitance(self):
		"""
		Testing that get_evacuation_assitance returns expected values and status codes

		One user will have evacuation assistance info and test his request (200 response code and meaningful data returned)
		One user will have no emergency assistance info and test his request (204 response code)
		One user will have an invalid JWT and test his request (401 response code)
		"""
		# Using Django's client to access the temporary test database
		c = Client()

		# Generate our JWTs
		response = c.post(auth_url, {'username': self.username_with_data})
		# Decode the JWT from json to string format (which is what the API expects)
		user_with_data_jwt = response.content.decode('utf-8')
		# Grab our user without any emergency notifications info's JWT
		response = c.post(auth_url, {'username': self.username_without_data})
		user_without_data_jwt = response.content.decode('utf-8')

		# Request the emergency notifications info for our user with data
		response = c.post(get_evacuation_assistance_url, HTTP_AUTHORIZATION=user_with_data_jwt)
		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, success_code)
		# Load the emergency notifications info list into a dictionary/JSON format
		evac_assistance_return = json.loads(response.content)[0]

		"""We provided 'Y' as the evacuation_assistance, confirm that's what was returned"""
		self.assertEqual(evac_assistance_return['evacuation_assistance'], self.valid_status)

		# Request the emergency notifications info for our user without data
		response = c.post(get_evacuation_assistance_url, HTTP_AUTHORIZATION=user_without_data_jwt)
		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, success_code)
		# Load the emergency notifications info list into a dictionary/JSON format
		evac_assistance_return = json.loads(response.content)[0]

		"""This user didn't supply a value for evacuation_assistance, so it should be None/Null"""
		self.assertEqual(evac_assistance_return['evacuation_assistance'], None)

		# Test a user who doesn't supply a valid JWT
		response = c.post(get_evacuation_assistance_url, HTTP_AUTHORIZATION="No Token Here!")
		"""Testing that back-end reports a 401 Unauthorized"""
		self.assertEqual(response.status_code, unauthorized_code)

	def test_set_evacuation_assitance(self):
		"""
		Testing that set_emergency_notifications returns expected status codes and changes are made to the database

		One user will attempt to create an entry into the database with valid evac-assistance
		One user will attempt to create an entry into the database with invalid data
		One user will attempt to update their database entry with valid data
		One user will attempt to update their database entry with invalid data

		One user will have an invalid JWT and test his request (401 response code)
		"""

		# Using Django's client to access the temporary test database
		c = Client()

		# Generate our JWT
		# Grab our user without any emergency notifications info's JWT
		response = c.post(auth_url, {'username': self.username_without_emergency_entry})
		user_without_emergency_entry_jwt = response.content.decode('utf-8')

		# First, we'll attempt to create a new entry into the Emergency database with invalid data
		response = c.post(set_evacuation_assistance_url,
		# POST body
		{
			'evacuation_assistance':self.invalid_status
		},
		# POST headers
		HTTP_AUTHORIZATION=user_without_emergency_entry_jwt
		)

		"""Testing that we received a 422 unprocessable entity response"""
		self.assertEqual(response.status_code, unprocessable_entity)

		"""Testing that the Emergency database did not add the user in with incorrect data"""
		user_entry = emergency.Emergency.objects.filter(pidm=self.pidm_without_emergency_entry)
		# Should be 0 returned values
		self.assertEqual(len(user_entry), 0)

		# Now, we'll attempt to create an entry with valid data
		response = c.post(set_evacuation_assistance_url,
		# POST body
		{
			'evacuation_assistance':self.valid_status
		},
		# POST headers
		HTTP_AUTHORIZATION=user_without_emergency_entry_jwt
		)

		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, success_code)

		"""Testing that the user was added to the Emergency registry with the correct value"""
		user_entry = emergency.Emergency.objects.get(pidm=self.pidm_without_emergency_entry)
		self.assertEqual(user_entry.evacuation_assistance, self.valid_status)

		# We'll now update the database status with None
		response = c.post(set_evacuation_assistance_url,
		# POST body
		{
			# Without 'evacuation_assistance' set, it will be deleted in the database
		},
		# POST headers
		HTTP_AUTHORIZATION=user_without_emergency_entry_jwt
		)

		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, success_code)

		"""Testing that the user's data has updated to None"""
		user_entry = emergency.Emergency.objects.get(pidm=self.pidm_without_emergency_entry)
		self.assertEqual(user_entry.evacuation_assistance, None)

		# Now we'll attempt to update the database with an invalid status
		response = c.post(set_evacuation_assistance_url,
		# POST body
		{
			'evacuation_assistance':self.invalid_status
		},
		# POST headers
		HTTP_AUTHORIZATION=user_without_emergency_entry_jwt
		)

		"""Testing that we received a 422 unprocessable entity response"""
		self.assertEqual(response.status_code, unprocessable_entity)

		"""Testing that the user's data remains unchanged and is still None"""
		user_entry = emergency.Emergency.objects.get(pidm=self.pidm_without_emergency_entry)
		self.assertEqual(user_entry.evacuation_assistance, None)


class EmergencyContactsTests(TestCase):
	"""
	Testing out the setting and getting of Emergency Contacts Info
	"""

	def setUp(self):
		""" Our user entry with contact info set up """
		identity.Identity.objects.create(pidm=123, username='fooBar', first_name='Foo', last_name='Bar', email='fooBar@pdx.edu')
		self.username_with_data = 'fooBar'
		self.pidm_with_data = 123

		""" Our user entry without contact info set up """
		identity.Identity.objects.create(pidm=456, username='TommyZ', first_name='Tom', last_name='Zero-friends', email='TomZ@pdx.edu')
		self.username_without_data = 'TommyZ'
		self.pidm_without_data = 456

		""" Our fresh user, for testing the setting of contact info """
		identity.Identity.objects.create(pidm=789, username='JJohn', first_name='Jimmy', last_name='Johnson', email='JimmyJ@pdx.edu')
		self.fresh_username = 'JJohn'
		self.pidm_for_fresh_user = 789

		""" Contact information entries for data retrieval """
		# Add two contacts for 'user_with_data' - no need to populate every field
		contact.Contact.objects.create(surrogate_id=1, pidm=123, first_name="Debby", last_name='Bar')
		contact.Contact.objects.create(surrogate_id=2, pidm=123, first_name="Jim", last_name='Bar')
		# We'll check against how many values are returned on a get-contacts request
		self.user_with_data_contact_count = 2
		# Create a Contact entry that isn't linked to either user
		contact.Contact.objects.create(surrogate_id=3, pidm=987654321, first_name="Billy", last_name='Kid')

		""" Valid emergency contact information to enter into database """
		self.good_emergency_priority = "1"
		self.good_emergency_relt_code = 'S'
		self.good_emergency_last_name = "Bauuer"
		self.good_emergency_first_name = "George"
		self.good_emergency_middle_init = "S"
		self.good_emergency_street_line1 = "345 SW Georgia Ln"
		self.good_emergency_street_line2 = ""
		self.good_emergency_street_line3 = ""
		self.good_emergency_city = "Portland"
		self.good_emergency_stat_code = "OR"
		self.good_emergency_natn_code = "LUS" # Not sure what this denotes but it is present in the existing dataset
		self.good_emergency_zip = "97230"
		self.good_emergency_ctry_code_phone = "01"
		self.good_emergency_phone_area = "503"
		self.good_emergency_phone_number = "2572522"
		self.good_emergency_phone_ext = "34"
		self.surrogate_id_of_contact = 34

		""" Bad data to feed into the emergency contact database """
		self.bad_emergency_relt_code = 'Z'
		self.bad_emergency_phone_area = "5033"
		self.bad_emergency_phone_number = "25725223"
		self.surrogate_id_of_bad_contact = 27

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
		response = c.post(auth_url, {'username': self.username_with_data})
		# Decode the JWT from json to string format (which is what the API expects)
		user_with_data_jwt = response.content.decode('utf-8')
		# User without data's JWT
		response = c.post(auth_url, {'username': self.username_without_data})
		user_without_data_jwt = response.content.decode('utf-8')

		# Request the contact info for the user with data
		response = c.post(get_contacts_url, HTTP_AUTHORIZATION=user_with_data_jwt)
		"""Testing that we received a 200 success response"""
		self.assertEqual(response.status_code, success_code)

		# Load the contacts in dictionary/JSON format
		contacts = json.loads(response.content)

		"""Testing that we got the expected amount of contacts back"""
		self.assertEqual(len(contacts), self.user_with_data_contact_count)

		"""Testing that the contacts returned are linked to our user with data"""
		for contact in contacts:
			self.assertEqual(contact['pidm'], self.pidm_with_data)

		# Now to test that users without data receive a No Content (204) response
		response = c.post(get_contacts_url, HTTP_AUTHORIZATION=user_without_data_jwt)
		"""Testing that we received a 204 No Content response"""
		self.assertEqual(response.status_code, no_content_code)
		"""Testing that there's no contacts returned"""
		self.assertEqual(len(response.content), 0)

		# # Now test a user who doesn't supply a valid JWT
		response = c.post(get_contacts_url, HTTP_AUTHORIZATION="No Token Here!")
		"""Testing that back-end reports a 401 Unauthorized"""
		self.assertEqual(response.status_code, unauthorized_code)

	def test_update_emergency_contacts(self):
		""" Testing will test for the following cases of usage of update_emergency_contact:

			User with invalid JWT (Expected 401)
			User attempts to create entry into database with good_emergency data
			User attempts to create entry in database with bad_emergency data
			User updates database with good_emergency data
			User updates database with bad_emergency data

		"""
		# Much of the code for testing JWTs is exactly the same process as in Daniel's tests.
		# Using Django's client to access the temporary test database
		c = Client()
		# Generate our JWTs
		response = c.post(auth_url, {'username': self.fresh_username})
		# Decode the JWT from json to string format (which is what the API expects)
		user_with_valid_data_jwt = response.content.decode('utf-8')
		# Grab our user without any alert info's JWT
		response = c.post(auth_url, {'username': self.username_without_data})
		user_with_invalid_data_jwt = response.content.decode('utf-8')

		# Test entering new entry with valid data
		response = c.post(set_contacts_url,
		# create the POST Body
		{
			# 'pidm': self.pidm_for_fresh_user,
			'surrogate_id':self.surrogate_id_of_contact,
			'priority':self.good_emergency_priority,
			'relt_code':self.good_emergency_relt_code,
			'last_name':self.good_emergency_last_name,
			'first_name':self.good_emergency_first_name,
			'mi':self.good_emergency_middle_init,
			'street_line1':self.good_emergency_street_line1,
			'street_line2':self.good_emergency_street_line2,
			'street_line3':self.good_emergency_street_line3,
			'city':self.good_emergency_city,
			'stat_code':self.good_emergency_stat_code,
			'natn_code':self.good_emergency_natn_code,
			'zip':self.good_emergency_zip,
			'ctry_code_phone':self.good_emergency_ctry_code_phone,
			'phone_area':self.good_emergency_phone_area,
			'phone_number':self.good_emergency_phone_number,
			'phone_ext':self.good_emergency_phone_ext
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)

		""" Testing to make sure that this returned a 200 status code """
		self.assertEqual(response.status_code, success_code)

		# Grab the valid user's Contact info
		user_entry = contact.Contact.objects.get(pidm=self.pidm_for_fresh_user)

		""" Testing that the data that was uploaded matches the local data """
		# Compare each value using asserts
		self.assertEqual(user_entry.priority, self.good_emergency_priority)
		self.assertEqual(user_entry.relt_code, self.good_emergency_relt_code)
		self.assertEqual(user_entry.last_name, self.good_emergency_last_name)
		self.assertEqual(user_entry.first_name, self.good_emergency_first_name)
		self.assertEqual(user_entry.mi, self.good_emergency_middle_init)
		self.assertEqual(user_entry.street_line1, self.good_emergency_street_line1)
		self.assertEqual(user_entry.street_line2, self.good_emergency_street_line2)
		self.assertEqual(user_entry.street_line3, self.good_emergency_street_line3)
		self.assertEqual(user_entry.city, self.good_emergency_city)
		self.assertEqual(user_entry.stat_code, self.good_emergency_stat_code)
		self.assertEqual(user_entry.natn_code, self.good_emergency_natn_code)
		self.assertEqual(user_entry.zip, self.good_emergency_zip)
		self.assertEqual(user_entry.ctry_code_phone, self.good_emergency_ctry_code_phone)
		self.assertEqual(user_entry.phone_area, self.good_emergency_phone_area)
		self.assertEqual(user_entry.phone_number, self.good_emergency_phone_number)
		self.assertEqual(user_entry.phone_ext, self.good_emergency_phone_ext)

		# Now, update our valid db entries with more valid data
		response = c.post(set_contacts_url,
		# create the POST Body
		{
			'pidm':self.pidm_for_fresh_user,
			'surrogate_id':self.surrogate_id_of_contact,
			'priority':self.good_emergency_priority,
			'relt_code':self.good_emergency_relt_code,
			'last_name':self.good_emergency_last_name,
			'first_name':self.good_emergency_first_name,
			'mi':self.good_emergency_middle_init,
			'street_line1':self.good_emergency_street_line1,
			'street_line2':self.good_emergency_street_line2,
			'street_line3':self.good_emergency_street_line3,
			'city':self.good_emergency_city,
			'stat_code':self.good_emergency_stat_code,
			'natn_code':self.good_emergency_natn_code,
			'zip':self.good_emergency_zip,
			'ctry_code_phone':self.good_emergency_ctry_code_phone,
			'phone_area':self.good_emergency_phone_area,
			'phone_number':self.good_emergency_phone_number,
			'phone_ext':self.good_emergency_phone_ext
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)

		""" Testing to make sure that this returned a 200 status code """
		self.assertEqual(response.status_code, success_code)

		# Grab the valid user's Contact info
		user_entry = contact.Contact.objects.get(pidm=self.pidm_for_fresh_user)

		""" Testing that the data that was uploaded matches the local data """
		# Compare each value using asserts
		self.assertEqual(user_entry.priority, self.good_emergency_priority)
		self.assertEqual(user_entry.relt_code, self.good_emergency_relt_code)
		self.assertEqual(user_entry.last_name, self.good_emergency_last_name)
		self.assertEqual(user_entry.first_name, self.good_emergency_first_name)
		self.assertEqual(user_entry.mi, self.good_emergency_middle_init)
		self.assertEqual(user_entry.street_line1, self.good_emergency_street_line1)
		self.assertEqual(user_entry.street_line2, self.good_emergency_street_line2)
		self.assertEqual(user_entry.street_line3, self.good_emergency_street_line3)
		self.assertEqual(user_entry.city, self.good_emergency_city)
		self.assertEqual(user_entry.stat_code, self.good_emergency_stat_code)
		self.assertEqual(user_entry.natn_code, self.good_emergency_natn_code)
		self.assertEqual(user_entry.zip, self.good_emergency_zip)
		self.assertEqual(user_entry.ctry_code_phone, self.good_emergency_ctry_code_phone)
		self.assertEqual(user_entry.phone_area, self.good_emergency_phone_area)
		self.assertEqual(user_entry.phone_number, self.good_emergency_phone_number)
		self.assertEqual(user_entry.phone_ext, self.good_emergency_phone_ext)

		# Now, test entering bad new data into a database
		response = c.post(set_contacts_url,
		# create the POST Body
		{
			'pidm':self.pidm_without_data,
			'surrogate_id':self.surrogate_id_of_bad_contact,
			'relt_code':self.bad_emergency_relt_code,
			'phone_area':self.bad_emergency_phone_area,
			'phone_number':self.bad_emergency_phone_number,
			# The rest should be None to be invalid.
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_invalid_data_jwt
		)

		""" Testing to make sure that this returned a 422 status code """
		self.assertEqual(response.status_code, unprocessable_entity)

		# Try to grab db data for this entry, should be empty
		user_entry = contact.Contact.objects.filter(surrogate_id=self.surrogate_id_of_bad_contact)

		"""Testing that the database did NOT update with this invalid data, returning nothing"""
		self.assertEqual(len(user_entry), 0)

		# Now attempt to update an already-valid database with invalid data
		response = c.post(set_contacts_url,
		# create the POST Body
		{
			'pidm':self.pidm_for_fresh_user,
			'surrogate_id':self.surrogate_id_of_contact,
			'relt_code':self.bad_emergency_relt_code,
			'phone_area':self.bad_emergency_phone_area,
			'phone_number':self.bad_emergency_phone_number,
			# The rest should be None to be invalid.
		},
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)

		""" Testing to make sure that this returned a 422 status code """
		self.assertEqual(response.status_code, unprocessable_entity)

		# Try to grab db data for this entry, should have stayed the same and not been updated
		user_entry = contact.Contact.objects.get(pidm=self.pidm_for_fresh_user)
		self.assertEqual(user_entry.priority, self.good_emergency_priority)
		self.assertEqual(user_entry.relt_code, self.good_emergency_relt_code)
		self.assertEqual(user_entry.last_name, self.good_emergency_last_name)
		self.assertEqual(user_entry.first_name, self.good_emergency_first_name)
		self.assertEqual(user_entry.mi, self.good_emergency_middle_init)
		self.assertEqual(user_entry.street_line1, self.good_emergency_street_line1)
		self.assertEqual(user_entry.street_line2, self.good_emergency_street_line2)
		self.assertEqual(user_entry.street_line3, self.good_emergency_street_line3)
		self.assertEqual(user_entry.city, self.good_emergency_city)
		self.assertEqual(user_entry.stat_code, self.good_emergency_stat_code)
		self.assertEqual(user_entry.natn_code, self.good_emergency_natn_code)
		self.assertEqual(user_entry.zip, self.good_emergency_zip)
		self.assertEqual(user_entry.ctry_code_phone, self.good_emergency_ctry_code_phone)
		self.assertEqual(user_entry.phone_area, self.good_emergency_phone_area)
		self.assertEqual(user_entry.phone_number, self.good_emergency_phone_number)
		self.assertEqual(user_entry.phone_ext, self.good_emergency_phone_ext)

		""" Testing the delete functionality in the emergency contact interface """
		# Make sure that the valid entry exists.
		user_entry = contact.Contact.objects.filter(surrogate_id=self.surrogate_id_of_contact)
		self.assertEqual(len(user_entry), 1)

		# now, delete it
		# To delete a contact, the API expects the surrogate id to be placed in the url as a parameter, and called with a delete request
		# i.e. set_contacts_url/<surrogate_id>/
		delete_contact_url = set_contacts_url + str(self.surrogate_id_of_contact) + '/'

		response = c.delete(delete_contact_url,
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)

		user_entry = contact.Contact.objects.filter(surrogate_id=self.surrogate_id_of_contact)
		self.assertEqual(len(user_entry), 0)

		# Now, we try to delete a user that does not belong to us. We should receive a 422.

		# make sure that there is an existing entry for surrogate id of 3
		user_entry = contact.Contact.objects.filter(surrogate_id=3)
		self.assertEqual(len(user_entry), 1)

		# now, try to delete it.
		invalid_delete = set_contacts_url + str(3) + '/'

		response = c.delete(invalid_delete,
		# POST headers
		HTTP_AUTHORIZATION=user_with_valid_data_jwt
		)

		# then, process the results.
		self.assertEqual(response.status_code, unprocessable_entity)

		user_entry = contact.Contact.objects.filter(surrogate_id=3)
		self.assertEqual(len(user_entry), 1)

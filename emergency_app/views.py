from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from emergency_app.models import identity, contact, emergency
#TODO - crsf_exempt is only needed when testing on http - REMOVE WHEN DONE TESTING
from django.views.decorators.csrf import csrf_exempt
#require_http_methods allows us to force POST rather then GET
from django.views.decorators.http import require_http_methods

from django.utils import timezone

# jwt_placeholder is a temporary JWT generator and validator
# Will be replaced by Single-Sign-On calls
from common.util import jwt_placeholder as j
from common.util import sanitization

# Common http return codes
http_no_content_response = 204 # Request was valid and authorized, but no content found
http_unauthorized_response = 401 # Request is either missing JWT or provided invalid JWT
http_unprocessable_entity_response = 422 # Request was formatted properly, but had invalid data (e.g. invalid email)

# Database models
Identity = identity.Identity
Contact = contact.Contact
Emergency = emergency.Emergency

# Valid relational codes for contact database info
valid_relational_codes = ['G', 'F', 'O', 'U', 'S', 'A', 'R']

# The key name for our JWT in HTTP request headers
JWT_Headers_Key = "HTTP_AUTHORIZATION"

def test(request, name=None):
	"""
	Test function for returning all usernames
	Useful for testing login that requires a username
	"""
	ret = ["ALL DATABASE USERNAMES: "]
	#Gather the db entries
	usernames = Identity.objects.all().values('username')
	for username in usernames:
		ret.append(username['username'] + ' # ')
	return HttpResponse(ret)

#TODO csrf_exempt is temporary, need this exemption over http
@csrf_exempt
@require_http_methods(["POST"])
def login(request):
	"""
	Only available as a POST request
	Body:
		{
			usr (str): username as it shows in the database
		}
	Return:
		Return a JWT (plain-string) on success with the following header and payload
			Header:
				{
					typ (str): "JWT"
					alg (str): "HS256"
				}
			Payload:
				{
					first_name (str)
					last_name (str)
					username (str)
					email (str)
				}
			Return Unauthorized Error(401) otherwise
	Raises:
		TODO - is it good practice to raise in Django views?
	"""
	# Grab the username within the POST body
	requested_username = request.POST.get('username')

	# Attempt to grab first/last name, username, and email from the database
	# SQL equivilent: SELECT first_name, last_name, username, email FROM Identity WHERE Identity.username = requested_username
	user_data = Identity.objects.filter(username=requested_username).values('first_name', 'last_name', 'username', 'email')

	# If the query returned nothing, then the username isn't in the database
	if len(user_data) < 1:
		return HttpResponse('Unauthorized', status=http_unauthorized_response)

	# Otherwise, return a JWT containing the first/last name, username, and email
	token = j.generate_token(user_data[0])
	return HttpResponse(token)

@csrf_exempt
@require_http_methods(["POST", "GET"])
def get_emergency_contacts(request):
	"""
	Validates the jwt issued, then returns relevent emergency contact info
		if jwt fails to validate, then return Unauthorized Error(401)
		if user has no contacts, return No Content(204)
	Body:
		{
			first_name (str)
			last_name (str)
			username (str)
			email (str)
		}
	returns a json on success with the following data
	{
		{
			surrogate_id: xxxx
			contact info...
		},
		{
			surrogate_id: xxxx
			contact info...
		},
		...
	}
	If the user has no contacts, returns a No Content(204)
	if JWT fails to validate return Unauthorized Error(401)
	"""
	# Pull the jwt from the POST request
	jwt = request.META.get(JWT_Headers_Key)
	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=http_unauthorized_response)

	payload = j.grab_token_payload(jwt)

	# With a valid jwt, we can query the Identity table for the user's primary key (pidm)
	# SELECT pidm FROM Identity WHERE Identity.username = jwt['username']
	user_pidm = Identity.objects.get(username=payload['username']).pidm

	# Now we can query the contact table for any contacts that this user has listed
	contacts = Contact.objects.filter(pidm=user_pidm)

	# No contacts for this user's valid request results in a 204, No Content
	if len(contacts) < 1:
		return HttpResponse("No contacts found", status=http_no_content_response)

	# Otherwise return all contacts in their json form
	contact_list = list(contacts.values())
	return JsonResponse(contact_list, safe=False)

# Update (mutate) emergency contact information
@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def update_emergency_contact(request, surrogate_id=None):
	"""
	Update the database information regarding the emergency contact information.
	This could imply either submitting a new emergency contact, or deleting the
	existing emergency contact.
	"""
	# extract JWT from post request in uniform fashion to above JWT code
	jwt = request.META.get(JWT_Headers_Key)

	# Validate JWT
	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=401)

	# Extract jwt payload
	payload = j.grab_token_payload(jwt)

	# First, we extract the checkbox data and determine if we need to branch
	if request.method == "DELETE":
		if surrogate_id == None:
			print("surrogate_id can't be none!")
			return HttpResponse("No Surrogate ID given!", status=422)
		user_entry = Contact.objects.filter(surrogate_id=surrogate_id)
		if len(user_entry) < 1:
			# The user does not exist
			return HttpResponse("No contact found.")
		else:
			user_pidm = Identity.objects.get(username=payload['username']).pidm
			if user_entry[0].pidm != user_pidm:
				return HttpResponse("No contact found", status=422)
			else:
				user_entry.delete()
				return HttpResponse("Successfully deleted emergency contact.", status=200)

	else:
		# Grab the additional data from the POST request
		surrogate_id = request.POST.get('surrogate_id')
		priority = request.POST.get('priority')
		# sanitize
		if priority == None:
			return HttpResponse("Missing priority.", status=422)

		relt_code = request.POST.get('relt_code')
		# sanitize

		# Relational codes are defined in their own database
		# The only valid ones are: G, F, O, U, S, A, and R
		if relt_code not in valid_relational_codes:
			return HttpResponse("Invalid relation.", status=422)

		last_name = request.POST.get('last_name')
		first_name = request.POST.get('first_name')
		mi = request.POST.get('mi')
		street_line1 = request.POST.get('street_line1')
		#sanitize
		if last_name == None:
			return HttpResponse("Invalid last name.", status=422)
		if first_name == None:
			return HttpResponse("Invalid first name.", status=422)
		if street_line1 == None:
			return HttpResponse("Invalid address line 1.", status=422)

		street_line2 = request.POST.get('street_line2')
		street_line3 = request.POST.get('street_line3')
		city = request.POST.get('city')
		# sanitize
		if city == None:
			return HttpResponse("Invalid city.", status=422)

		stat_code = request.POST.get('stat_code')
		natn_code = request.POST.get('natn_code')
		zip = request.POST.get('zip')
		# sanitize
		if stat_code == None:
			return HttpResponse("Invalid state.", status=422)
		if natn_code == None:
			return HttpResponse("Invalid nation code.", status=422)
		if zip == None:
			return HttpResponse("Invalid zip.", status=422)

		ctry_code_phone = request.POST.get('ctry_code_phone')
		phone_area = request.POST.get('phone_area')
		phone_number = request.POST.get('phone_number')
		phone_ext = request.POST.get('phone_ext')

		# SANITIZATION
		number_to_sanitize = phone_area + phone_number
		result = sanitization.validate_phone_num(number_to_sanitize)
		if result == False:
			return HttpResponse("Invalid phone number provided.", status=422) #Make sure to note 422=sanitization to front end
		# Grab the pidm from the JWT
		user_pidm = Identity.objects.get(username=payload['username']).pidm
		# grab the surrogate_id
		sur_id = Contact.objects.filter(surrogate_id=surrogate_id)
		# Check if the query returned anything
		if len(sur_id) < 1:
			user_exists = False
		else:
			entry = sur_id[0] # Save it for use later
			user_exists = True

		# Use the user_exists flag to add to the database
		if user_exists:
			# print("user exists")
			entry.pidm = user_pidm
			entry.priority = priority
			entry.relt_code = relt_code
			entry.last_name = last_name
			entry.first_name = first_name
			entry.mi = mi
			entry.street_line1 = street_line1
			entry.street_line2 = street_line2
			entry.street_line3 = street_line3
			entry.city = city
			entry.stat_code = stat_code
			entry.natn_code = natn_code
			entry.zip = zip
			entry.ctry_code_phone = ctry_code_phone
			entry.phone_area = phone_area
			entry.phone_number = phone_number
			entry.phone_ext = phone_ext
			# Save after writing to database
			entry.save()
			return HttpResponse("Emergency Contact Updated")
		else:
			# Add the user (questions regarding usage of PIDM vs Surrogate)
			# print("Adding new user")
			n_entry = Contact(
						surrogate_id=surrogate_id,
						pidm=user_pidm,
						priority=priority,
						relt_code=relt_code,
						last_name=last_name,
						first_name=first_name,
						mi=mi,
						street_line1=street_line1,
						street_line2=street_line2,
						street_line3=street_line3,
						city=city,
						stat_code=stat_code,
						natn_code=natn_code,
						zip=zip,
						ctry_code_phone=ctry_code_phone,
						phone_area=phone_area,
						phone_number=phone_number,
						phone_ext=phone_ext)
			n_entry.save()

			return HttpResponse("New user added")

@csrf_exempt
@require_http_methods(["POST", "GET"])
def get_emergency_notifications(request):
	"""
	Only available as a POST request
	expects 'jwt': JWT
	JWT Body:
		{
			first_name (str)
			last_name (str)
			username (str)
			email (str)
		}
	returns a json on success with the following data
	{
	  "alternate_phone":  "XXXXXXXXXX", <- no dashes
      "primary_phone":  "XXXXXXXXXX",  <- no dashes
      "sms_device":  "XXXXXXXXXX",  <- no dashes
      "external_email":  "aaa.bbb@email.com",
      "campus_email":  "ccc.ddd@pdx.edu",
      "activity_date": "YYYY-MM-DDTHH:MM:SS", <- YearMonthDayTHour:MinuteSecond
      "sms_status_ind": "Y" <- Or null
	}
	NOTE: Any of these values can be null, make sure to check in front-end
	"""
	# Pull the jwt from the POST request
	jwt = request.META.get(JWT_Headers_Key)
	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=http_unauthorized_response)

	# Grab username from the token
	payload = j.grab_token_payload(jwt)

	# With a valid jwt, we can query the Identity table for the user's primary key (pidm)
	# SELECT pidm FROM Identity WHERE Identity.usrname = payload['username']
	user_pidm = Identity.objects.get(username=payload['username']).pidm

	# Now we query the emergency table for any info the user has listed
	# SELECT * FROM Emergency WHERE Emergency.pidm = user_pidm
	user_entry = Emergency.objects.filter(pidm=user_pidm)

	# No info found for this user's valid request results in a 204, No Content
	if len(user_entry) < 1:
		return HttpResponse("No emergency info found", status=http_no_content_response)

	# Otherwise return all emergency info in their json format
	# We want every field except for the pidm, as there is no need to expose front-end to database specifics
	emergency_info = list(user_entry.values('external_email', 'campus_email',
											'primary_phone', 'alternate_phone',
											'sms_status_ind', 'sms_device',
											'activity_date'))

	# Return the list of user's emergency info, safe=false means we can return non-dictionary items
	return JsonResponse(emergency_info, safe=False)


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def set_emergency_notifications(request):
	"""
	Updates the user's status on the Emergency assistance table
	"""

	jwt = request.META.get(JWT_Headers_Key)

	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=http_unauthorized_response)

	payload = j.grab_token_payload(jwt)

	# Grab the user's pidm from Identity table
	user_pidm = Identity.objects.get(username=payload['username']).pidm

	# Delete doesn't make sense in this request
	# DELETE request - delete this user from the database
	# if request.method == "DELETE":
		# print("DELETE Request!")
		# # TODO set their op-out to Y
		# Emergency.objects.filter(pidm=user_pidm).delete()
		# return HttpResponse("User info deleted")

	# POST requests - adding data into the registry database

	# Grab all additional data - POST.get(...) returns None if front-end didn't load the POST request with it
	# also sanitize the data, returns invalid http response if the data has invalid format
	external_email = request.POST.get('external_email')
	if not (sanitization.validate_email(external_email) or external_email == None):
		return HttpResponse("Invalid Email!", status=http_unprocessable_entity_response)

	primary_phone = request.POST.get('primary_phone')
	if not (sanitization.validate_phone_num(primary_phone) or primary_phone == None):
		return HttpResponse("Invalid Phone Number!", status=http_unprocessable_entity_response)

	alternate_phone = request.POST.get('alternate_phone')
	if not (sanitization.validate_phone_num(alternate_phone) or primary_phone == None):
		return HttpResponse("Invalid Phone Number!", status=http_unprocessable_entity_response)

	sms_status_ind = request.POST.get('sms_status_ind')
	if not sanitization.validate_checkbox(sms_status_ind):
		return HttpResponse("Invalid Checkbox Value!", status=http_unprocessable_entity_response)

	if sms_status_ind == 'Y':
		sms_device = None
	else:
		sms_device = request.POST.get('sms_device')
		if not (sanitization.validate_phone_num(sms_device) or sms_device == None):
			return HttpResponse("Invalid Phone Number!", status=http_unprocessable_entity_response)

	# Campus email is included in jwt
	campus_email = payload['email']

	# Determine if the user is already in the emergency registry
	query = Emergency.objects.filter(pidm=user_pidm)
	if len(query) < 1:
		user_exists = False
	else:
		# Might as well grab the Emergency entry here
		user_entry = query[0]
		user_exists = True

	# If the user exists, update all information (any blank fields from front-end result in no data for that field here)
	if user_exists:
		user_entry.external_email = external_email
		user_entry.campus_email = campus_email
		user_entry.primary_phone = primary_phone
		user_entry.alternate_phone = alternate_phone
		user_entry.sms_status_ind = sms_status_ind
		user_entry.sms_device = sms_device
		# user_entry.campus_email = campus_email # campus email should not be modified
		user_entry.save()

		return HttpResponse("User info updated")
	else:
		print("Adding in user")
		new_entry = Emergency(pidm=user_pidm, external_email=external_email,
								campus_email=campus_email, primary_phone=primary_phone,
								alternate_phone=alternate_phone, sms_status_ind=sms_status_ind,
								sms_device=sms_device)
		new_entry.save()

		return HttpResponse("User info added")


@csrf_exempt
@require_http_methods(["POST"])
def get_evacuation_assistance(request):
	"""
	returns a json on success with the following data
	{
      "evacuation_assistance": "Y" <- Or null
	}
	"""
	# Pull the jwt from the POST request
	jwt = request.META.get(JWT_Headers_Key)
	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=http_unauthorized_response)

	# Grab username from the token
	payload = j.grab_token_payload(jwt)

	# With a valid jwt, we can query the Identity table for the user's primary key (pidm)
	# SELECT pidm FROM Identity WHERE Identity.usrname = payload['username']
	user_pidm = Identity.objects.get(username=payload['username']).pidm

	# Now we query the emergency table for any info the user has listed
	# SELECT * FROM Emergency WHERE Emergency.pidm = user_pidm
	user_entry = Emergency.objects.filter(pidm=user_pidm)

	# No info found for this user's valid request results in a 204, No Content
	if len(user_entry) < 1:
		return HttpResponse("No emergency info found", status=http_no_content_response)

	# Otherwise return evacuation assistance status in their json format
	emergency_info = list(user_entry.values('evacuation_assistance'))

	return JsonResponse(emergency_info, safe=False)


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def set_evacuation_assistance(request):
	"""
	Updates the user's evacuation assitance status on the Emergency table
	"""

	jwt = request.META.get(JWT_Headers_Key)

	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=http_unauthorized_response)

	payload = j.grab_token_payload(jwt)

	# Grab the user's pidm from Identity table
	user_pidm = Identity.objects.get(username=payload['username']).pidm

	# Grab the evacuation status data - POST.get(...) returns None if front-end didn't load the POST request with it
	# also sanitize the data, returns invalid http response if the data has invalid format
	evacuation_assistance = request.POST.get('evacuation_assistance')
	if not sanitization.validate_checkbox(evacuation_assistance):
		return HttpResponse("Invalid Checkbox Value!", status=http_unprocessable_entity_response)

	# Determine if the user is already in the emergency registry
	query = Emergency.objects.filter(pidm=user_pidm)
	if len(query) < 1:
		user_exists = False
	else:
		# Might as well grab the Emergency entry here
		user_entry = query[0]
		user_exists = True

	# If the user exists, update all information (any blank fields from front-end result in no data for that field here)
	if user_exists:
		user_entry.evacuation_assistance = evacuation_assistance
		user_entry.save()
		return HttpResponse("User info updated")
	else:
		print("Adding in user")
		new_entry = Emergency(pidm=user_pidm, evacuation_assistance=evacuation_assistance)
		new_entry.save()
		return HttpResponse("User info added")

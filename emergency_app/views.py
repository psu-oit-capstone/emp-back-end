from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from emergency_app.models import identity, contact, emergency
#TODO - crsf_exempt is only needed when testing on http - REMOVE WHEN DONE TESTING
from django.views.decorators.csrf import csrf_exempt
#require_http_methods allows us to force POST rather then GET
from django.views.decorators.http import require_http_methods

from django.utils import timezone
from .forms import UpdateEmergencyContactForm, SetEvacuationAssistanceForm, SetEmergencyNotificationsForm

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
	user_data = Identity.objects.filter(username=requested_username).values()

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

	user_pidm = payload['pidm']

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
			user_pidm = payload['pidm']
			if user_entry[0].pidm != user_pidm:
				return HttpResponse("No contact found", status=422)
			else:
				user_entry.delete()
				return HttpResponse("Successfully deleted emergency contact.", status=200)
	# End of deletion branch ==============================================================
	else:
		# first, decide if we are updating or creating
		# based upon if the surrogate_id already exists
		surrogate_id = surrogate_id = request.POST.get('surrogate_id')
		sur_id = Contact.objects.filter(surrogate_id=surrogate_id)
		if len(sur_id) < 1:
			entry = None
			user_exists = False
		else:
			entry = sur_id[0] # Save it for use later in form instances
			user_exists = True

		# Grab the pidm from the JWT
		jwt_pidm = payload['pidm']

		# Create a copy of the POST request to modify the Pidm
		temp_body = request.POST.copy()
		temp_body['pidm'] = jwt_pidm

		# Perform form logic, passing temp_body instead of original body
		form = UpdateEmergencyContactForm(temp_body, instance=entry) # If instance=None, it creates table. else, updates
		if form.is_valid():
			form.save()
			form = UpdateEmergencyContactForm()
			if user_exists == True:
				return HttpResponse("Updated successfully.")
			else:
				return HttpResponse("Created successfully.")
		else:
			return HttpResponse("Invalid form data.", status=http_unprocessable_entity_response)

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

	user_pidm = payload['pidm']

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

	user_pidm = payload['pidm']

	# Delete doesn't make sense in this request
	# DELETE request - delete this user from the database
	# if request.method == "DELETE":
		# print("DELETE Request!")
		# # TODO set their op-out to Y
		# Emergency.objects.filter(pidm=user_pidm).delete()
		# return HttpResponse("User info deleted")

	# POST requests - adding data into the registry database

	"""
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
		new_entry = Emergency(pidm=user_pidm, external_email=external_email,
								campus_email=campus_email, primary_phone=primary_phone,
								alternate_phone=alternate_phone, sms_status_ind=sms_status_ind,
								sms_device=sms_device)
		new_entry.save()

		return HttpResponse("User info added")
	"""
	query = Emergency.objects.filter(pidm=user_pidm)
	if len(query) < 1:
		entry = None
		user_exists = False
	else:
		# Might as well grab the Emergency entry here
		entry = query[0]
		user_exists = True

	form = SetEmergencyNotificationsForm(request.POST.copy())
	if form.is_valid():
		hmm = form.save()
		hmm.pidm = user_pidm
		hmm.save()
		if user_exists == True:
			return HttpResponse("Updated successfully.")
		else:
			return HttpResponse("Created successfully.")
	else:
		return HttpResponse("Invalid form data.", status=http_unprocessable_entity_response)



@csrf_exempt
@require_http_methods(["POST", "GET"])
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

	user_pidm = payload['pidm']

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
@require_http_methods(["POST"])
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

	user_pidm = payload['pidm']

	# Determine if the user is already in the emergency registry
	query = Emergency.objects.filter(pidm=user_pidm)
	if len(query) < 1:
		entry = None
		user_exists = False
	else:
		# Might as well grab the Emergency entry here
		entry = query[0]
		user_exists = True

	form = SetEvacuationAssistanceForm(request.POST, instance=entry)
	if form.is_valid():
		temp = form.save(commit=False) # Commit=false so it does not save
		temp.pidm = user_pidm
		temp.save()
		if user_exists == True:
			return HttpResponse("Updated successfully.")
		else:
			return HttpResponse("Created successfully.")
	else:
		return HttpResponse("Invalid form data.", status=http_unprocessable_entity_response)

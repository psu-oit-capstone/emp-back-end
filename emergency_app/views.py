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

Identity = identity.Identity
Contact = contact.Contact
Emergency = emergency.Emergency

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
		return HttpResponse('Unauthorized', status=401)
	
	# Otherwise, return a JWT containing the first/last name, username, and email
	token = j.generate_token(user_data[0])
	return HttpResponse(token)

@csrf_exempt
@require_http_methods(["POST"])
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
	jwt = request.POST.get('jwt')
	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=401)
		
	payload = j.grab_token_payload(jwt)
	
	# With a valid jwt, we can query the Identity table for the user's primary key (pidm)
	# SELECT pidm FROM Identity WHERE Identity.username = jwt['username']
	user_pidm = Identity.objects.get(username=payload['username']).pidm
	
	# Now we can query the contact table for any contacts that this user has listed
	contacts = Contact.objects.filter(pidm=user_pidm)
	
	# No contacts for this user's valid request results in a 204, No Content
	if len(contacts) < 1:
		return HttpResponse("No contacts found", status=204)	
	
	# Otherwise return all contacts in their json form
	contact_list = list(contacts.values())
	return JsonResponse(contact_list, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def get_alert_info(request):
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
	jwt = request.POST.get('jwt')
	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=401)
	
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
		return HttpResponse("No emergency info found", status=204)
	
	# Otherwise return all emergency info in their json format
	# We want every field except for the pidm, as there is no need to expose front-end to database specifics
	emergency_info = list(user_entry.values('evacuation_assistance', 'external_email',
											'campus_email', 'primary_phone',
											'alternate_phone', 'sms_status_ind',
											'sms_device', 'activity_date'))
											
	# Return the list of user's emergency info, safe=false means we can return non-dictionary items
	return JsonResponse(emergency_info, safe=False)


# For Sam
@csrf_exempt
def set_request_assistance(request):
	"""
	Updates the user's status on the Emergency assistance table
	If the user has the checkbox 'ticked' then attempt to add their info in
	otherwise, delete the user's input.
	"""

	# Pull the jwt from the POST request
	jwt = request.POST.get('jwt')
	# Check if the request is to add, otherwise it is to delete
	add_to_registry = request.POST.get('addToRegistry') == 'True'

	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=401)
	
	# Extract the JWT payload
	payload = j.grab_token_payload(jwt)

	# Grab the user's pidm from Identity table
	user_pidm = Identity.objects.get(username=payload['username']).pidm
	
	# Determine if the user is already in the emergency registry
	query = Emergency.objects.filter(pidm=user_pidm)
	if len(query) < 1:
		user_exists = False
	else:
		# Might as well grab the Emergency entry here
		user_entry = query[0]
		user_exists = True

	# If the user wants to add themselves to the emergency registry
	if add_to_registry:
		# Confirm that the user isn't already in the registry
		if not user_exists:
			# Grab the user's email from their JWT payload
			email = payload['email']
			# The database needs to add an entirely new entry and set sms_status_ind to 'Y'
			# 
			new_entry = Emergency(pidm=user_pidm, campus_email=email, activity_date=timezone.now(), sms_status_ind='Y')
			new_entry.save()
			return HttpResponse("User successfully added to registry", status=200)
		# The user already exists in the emergency contact database, but they want to update their status to 'yes'/'Y'
		else:
			# Update the existing user entry sms_status_ind to 'Y'
			user_entry.sms_status_ind = 'Y'
			user_entry.save()
			return HttpResponse("User registry status has been set to 'Y'")

	# Otherwise, user wants to 'delete' their entry into the registry
	# Rather than delete, we'll just set the user's sms_status_ind to 'N'
	else:
		# If the user doesn't exist, we don't have to do anything, just report back
		if not user_exists:
			return HttpResponse("User registry status has been set to 'No'")
		# Otherwise, if the user exists in the database, we'll just change the sms_status_ind to 'N'
		else:
			user_entry.sms_status_ind = 'N'
			return HttpResponse("User registry status has been set to 'No'")




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
	jwt = request.META.get(JWT_Headers_Key)
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

# For Sam
@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def set_request_assistance(request):
	"""
	Updates the user's status on the Emergency assistance table
	If the user has the checkbox 'ticked' then attempt to add their info in
	otherwise, delete the user's input.
	"""

	jwt = request.META.get(JWT_Headers_Key)

	try:
		j.validate_token(jwt)
	except Exception as e:
		return HttpResponse(str(e), status=401)
	
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
	evacuation_assistance = request.POST.get('evacuation_assistance')
	external_email = request.POST.get('external_email')
	campus_email = request.POST.get('campus_email')
	primary_phone = request.POST.get('primary_phone')
	alternate_phone = request.POST.get('alternate_phone')
	sms_status_ind = request.POST.get('sms_status_ind')
	sms_device = request.POST.get('sms_device')
	# Campus email is included in jwt
	campus_email = payload['email']
	
	if not sanitization.validate_email(external_email):
		external_email = None
	else:
		print("Great email!")
	# Validate data here
	#...
	#...
	#...
	
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
		user_entry.external_email = external_email
		user_entry.campus_email = campus_email
		user_entry.primary_phone = primary_phone
		user_entry.alternate_phone = alternate_phone
		user_entry.sms_status_ind = sms_status_ind
		user_entry.sms_device = sms_device
		user_entry.campus_email = campus_email
		user_entry.save()
		
		return HttpResponse("User info updated")
	else:
		print("Adding in user")
		new_entry = Emergency(pidm=user_pidm,
								evacuation_assistance=evacuation_assistance, external_email=external_email,
								campus_email=campus_email, primary_phone=primary_phone,
								alternate_phone=alternate_phone, sms_status_ind=sms_status_ind,
								sms_device=sms_device)
		new_entry.save()
		
		return HttpResponse("User info added")
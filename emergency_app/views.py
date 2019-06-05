from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from emergency_app.models import identity, contact
#TODO - crsf_exempt is only needed when testing on http - REMOVE WHEN DONE TESTING
from django.views.decorators.csrf import csrf_exempt
#require_http_methods allows us to force POST rather then GET
from django.views.decorators.http import require_http_methods

# jwt_placeholder is a temporary JWT generator and validator
# Will be replaced by Single-Sign-On calls
from common.util import jwt_placeholder as j

Identity = identity.Identity
Contact = contact.Contact

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

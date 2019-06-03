from django.shortcuts import render
from django.http import HttpResponse
from emergency_app.models import identity
#TODO - crsf_exempt is only needed when testing on http - REMOVE WHEN DONE TESTING
from django.views.decorators.csrf import csrf_exempt
#require_http_methods allows us to force POST rather then GET
from django.views.decorators.http import require_http_methods

# jwt_test is a temporary JWT generator and validator
# Will be replaced by Single-Sign-On calls
# Need better name convention
from common.util import jwt_test as j

Identity = identity.Identity

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
	username = request.POST.get('username')
	
	# Attempt to grab first/last name, username, and email from the database
	user_data = Identity.objects.filter(username=username).values('first_name', 'last_name', 'username', 'email')
	
	# If the query returned nothing, then the username isn't in the database
	if len(user_data) < 1:
		return HttpResponse('Unauthorized', status=401)
	
	# Otherwise, return a JWT containing the first/last name, username, and email
	token = j.generate_token(user_data[0])
	return HttpResponse(token)

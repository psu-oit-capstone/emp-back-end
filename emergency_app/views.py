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

	ret = []
	#Gather the db entries
	entries = Identity.objects.all()
	for object in entries:
		field_object = Identity._meta.get_field('username')
		field_value = field_object.value_from_object(object)
		ret.append(str(field_value) + ' # ')
	return HttpResponse(ret)

#TODO csrf_exempt is temporary, need this exemption over http
@csrf_exempt
@require_http_methods(["POST"])
def login(request):
	"""
	Only available as a POST request
	Body:
		{
			username: (str)
		}
	Return:
		Return a JWT (plain-string) on success
			Return Unauthorized Error(401) otherwise
	Raises:
		TODO - is it good practice to raise in Django views?
	"""
	
	# if request.method == 'POST':
	username = request.POST.get('username')
	
	username_field = Identity._meta.get_field('username')
	
	objects = Identity.objects.all()	
	
	for object in objects:
		value = username_field.value_from_object(object)
		if username == value:
			json = {'usr': value, 'other_info': 'blah'}
			token = j.generate_token(json)
			return HttpResponse(token)
			# return HttpResponse("Found your username!")
	#Getting here implies we didn't find the username
	return HttpResponse('Unauthorized', status=401)

# Only needed for testing - no reason the front-end should ever validate their token
# def validate_token(request, token=None):
	# """
	# Validates the token passed in
	# Args:
		# token (str): The JWT that was (if valid) signed by this server
	# Return:
		# ???
		# Currently returns a webpage telling the user it's valid
			# TODO - return JUST a value
	# """
	# if(j.validate_token(token)):
		# return HttpResponse("You've a valid token!")
	# return HttpResponse("You've an invalid token (possibly tampered with)")
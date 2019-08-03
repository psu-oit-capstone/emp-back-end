"""
	Placeholder for the SSO.
	Generates and validates JWTs
"""
import sys
import jwt
# datetime and timedelta for expiration
from datetime import datetime, timedelta

# The base for our secret - TODO: temporary, replace with better base later (perhaps store it in the database, and allow it to be updated)
# Once set up, this should be used to salt the user password to generate our 
base_secret = "H4ML7sLF51ANTwgFTQa3OXmuc2lIAk6JX"
hash_algorithm = 'HS256'

# Token's expiration time in seconds
# Currently 15 minutes
token_expiration_time = 60 * 15

def generate_token(json):
	"""
	Generates a JWT based on the given payload
	Args:
		json (dict): The payload that we are turning into a JWT
			should be in the format of {'name': 'bob', 'admin': 'True'}
	Returns:
		String: The encoded JWT as a string
	"""
	
	json['exp'] = datetime.utcnow() + timedelta(seconds=token_expiration_time)
	
	try:
		token = jwt.encode(json, base_secret, algorithm=hash_algorithm)
	except(TypeError):
		# print("Invalid json object passed in to jwt_placeholder.generate_token()!")
		# Re-throw the exception
		raise
		
	return token

def validate_token(token):
	"""
	Validates a JWT against the base_secret
	Args:
		token (str): The JWT to be validated
	Returns:
		Bool: True if the JWT hashes successfully, False if it has been tampered with
	"""
	try:
		jwt.decode(token, base_secret, algorithms=hash_algorithm)
	except(jwt.exceptions.InvalidSignatureError):
		# print("Invalid signature in jwt_placeholder.validate_token()!")
		raise
	except(jwt.exceptions.DecodeError):
		# print("Malformed JWT passed to jwt_placeholder.validate_token()!")
		raise
	except(jwt.exceptions.ExpiredSignatureError):
		# print("Expired token!")
		raise
	except Exception as e:
		print(e)
		raise
	return True

def grab_token_payload(token):
	"""
	Decodes the payload of the JWT - Only call after a token has been validated
	Args:
		token (str): The JWT containing the desired payload to decode
	Returns:
		Dictionary/json : returns the json representation of the JWT payload
	"""
	payload = jwt.decode(token, verify=False)
	return payload

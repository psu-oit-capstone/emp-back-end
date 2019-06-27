"""
	Placeholder for the SSO.
	Generates and validates JWTs
"""
import sys
import jwt
import ast # For CLI args string->dict eval

# The base for our secret - TODO: temporary, replace with better base later (perhaps store it in the database, and allow it to be updated)
# Once set up, this should be used to salt the user password to generate our 
base_secret = "H4ML7sLF51ANTwgFTQa3OXmuc2lIAk6J"
hash_algorithm = 'HS256'

def generate_token(json):
	"""
	Generates a JWT based on the given payload
	Args:
		json (dict): The payload that we are turning into a JWT
			should be in the format of {'name': 'bob', 'admin': 'True'}
	Returns:
		String: The encoded JWT as a string
	"""
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
	except(e):
		print(e)
		return False
	return True
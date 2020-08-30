import json
import boto3
import media_api
import summarisation
import database

def lambda_handler(event, context):
	lambdaResponse = {}
	responseObject = {}
	responseObject['headers'] = {}
	responseObject['headers']['Content-Type'] = 'application/json'
	
	try:
		#fetch the contents from the event json passed by api call
		user_name = event['user_name']
		ocr_text = event['key']
		image_path = event['image_path']
		
		lambdaResponse['user_name'] = user_name
		lambdaResponse['key'] = ocr_text
		lambdaResponse['image_path'] = image_path
		lambdaResponse['message'] = 'Request Successful'
		responseObject['statusCode'] = 200
		responseObject['headers'] = {}
		
		try:
			#Scrape for information for the keyword passed
			wiki_content = media_api.scrape(ocr_text)
			try:
				#summarise the content returned from media_api
				summarised_content = summarisation.run_summarisation(wiki_content)
				#write a new entry into dynamodb
				database.write_db(user_name,ocr_text,summarised_content,image_path)
				lambdaResponse['result'] = summarised_content
			except:
				lambdaResponse['message'] = 'An error occured while processing and storing the content. Please try again' 
				responseObject['statusCode'] = 500	
		except:
			lambdaResponse['message'] = 'Information for the requested keyword was not found on wikipedia. Please try again with a different keyword.' 
			responseObject['statusCode'] = 500	
			
	except KeyError:
		lambdaResponse['message'] = 'Request failed due to missing parameters.'
		responseObject['statusCode'] = 502

	responseObject['body'] = json.dumps(lambdaResponse)		
	return responseObject
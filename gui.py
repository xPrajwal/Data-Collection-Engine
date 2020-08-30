from tkinter import *
from time import strftime 
from tkinter.filedialog import askopenfilename
from pprint import pprint
from PIL import Image  
import PIL
import os
import hashlib
import datetime
import boto3 
from boto3 import dynamodb 
from boto3.session import Session
from boto3.dynamodb.conditions import Key, Attr
import OCR
import json
import requests

#Configuring connection to DynamoDB
dynamodb_session = Session(aws_access_key_id='AKIARSDWX2GVK4H5YQU2',
		  aws_secret_access_key='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',
		  region_name='ap-southeast-1')
dynamodb = dynamodb_session.resource('dynamodb')

def delete_user(usr_name):
	#Delete operation for the user login credentials entry in the "dce_db.user_info" table
	table = connect_db('dce_db.user_info')
	response = table.delete_item(
    	Key={
        	'user_name': usr_name
    	}
	)

	#Delete operation for the user's contents in the "dce_db.contents" table
	table = connect_db("dce_db.content")
	response = table.query(
		IndexName="user_content",
		KeyConditionExpression=Key('user_name').eq(usr_name),
	)
	i=0
	for items in response['Items']:
		entry = response['Items'][i]
		i = i+1
		table.delete_item(
    		Key={
        	'uuid': entry['uuid']
    		}
		)

	Label(edit_window, text = 'User profile successfully deleted!', fg='green').pack()

def edit_profile(usr_name):

	global edit_window
	
	#Entry boxes
	global email_change_entry
	global username_change_entry
	global password_change_entry
	
	edit_window = Tk()
	edit_window.title("User HomePage")
	width, height = edit_window.winfo_screenwidth(), edit_window.winfo_screenheight()
	edit_window.geometry('%dx%d+0+0' % (width,height))

	close_window(user_w)

	#Variables
	email_change = StringVar()
	username_change = StringVar()
	password_change = StringVar()

	#Existing emails and names list
	names = []
	emails = []
	table = connect_db("dce_db.user_info")	
	response = table.scan()
	i=0
	for items in (response['Items']):
		entry = response['Items'][i]
		i = i+1
		names.append(entry['user_name'])
		emails.append(entry['email'])

	#Window Contents
	Label(edit_window, text = "Data Collection Engine", bg = "blue",
	width="600", height = "2", font = ("Arial 50 bold")).pack()

	delete_button = Button(edit_window, text = "Delete Profile", font = "30", command = lambda : [delete_user(usr_name)]).pack()


	Label(edit_window, text = "Change Email", font = "30").pack()
	email_change_entry = Entry(edit_window, textvariable = email_change)
	email_change_entry.pack()
	Button(edit_window, text = "Submit", font = "30", command = lambda : [edit_email()] ).pack()

	Label(edit_window, text = "Change Password", font = "30").pack()
	password_change_entry = Entry(edit_window, show = '*', textvariable = password_change)
	password_change_entry.pack()
	Button(edit_window, text = "Submit", font = "30", command = lambda : [edit_password()] ).pack()

	#Function to change email
	def edit_email():
		
		new_email = email_change_entry.get()
		current_time = str(datetime.datetime.now())
		regex = "^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
		
		if new_email and (re.search(regex,new_email)) and (new_email not in emails):
			query = table.update_item(
				Key = {
				'user_name':usr_name
				}, 
				UpdateExpression = "SET email = :value1, updated_time = :value2",
				ExpressionAttributeValues = {
					":value1": new_email,
					":value2": current_time
				}
			)
			success_label = Label(edit_window, text = "Email changed.", font = (100), fg="green").pack()
		else:
			failure_label = Label(edit_window, text = "Please enter a valid email. If valid, try a different email.", font = (100), fg="red").pack()
	
	#Function to change password
	def edit_password():
		new_password = usr_name+password_change_entry.get()
		new_hashed_password = hash_str(new_password)
		current_time = str(datetime.datetime.now())
		print(current_time, new_password, new_hashed_password)
		
		if new_password:
			query = table.update_item(
				Key = {
				'user_name':usr_name
				}, 
				UpdateExpression = "SET password = :value1, updated_time = :value2",
				ExpressionAttributeValues = {
					":value1": new_hashed_password,
					":value2": current_time
				}
			)
			success_label = Label(edit_window, text = "Password changed.", font = (100), fg="green").pack()
		else:
			failure_label = Label(edit_window, text = "Please enter a valid password.", font = (100), fg="red").pack()

	
	Button(edit_window, text = "Back", font = "30", command = lambda : [close_window(edit_window), homepage()]).pack()

#Perform hashing on the string
def hash_str(string):
	hashed_str = hashlib.md5(str(string).encode('utf-8'))
	return hashed_str.hexdigest()

#Page to view exisiting contetnt of a user
def view_content(usr_name):

	global view_window
	view_window = Tk()
	view_window.title("User HomePage")
	width, height = view_window.winfo_screenwidth(), view_window.winfo_screenheight()
	view_window.geometry('%dx%d+0+0' % (width,height))

	close_window(user_w)

	Label(view_window, text = "Data Collection Engine", bg = "blue",
	width="600", height = "2", font = ("Arial 50 bold")).pack()
	
	table = connect_db("dce_db.content")
	response = table.query(
	IndexName="user_content",
	KeyConditionExpression=Key('user_name').eq(usr_name),
	)
	i=0
	options = []
	for items in response['Items']:
		entry = response['Items'][i]
		i = i+1
		user_name = entry['key']
		options.append(user_name)

	if not (options):
		empty_label = Label(view_window, text = "No content to display! Please upload an image to dispay content", font = (100), fg="red")
		empty_label.pack()
		Button(view_window, text = "Back", font = "30", command = lambda : [user_homepage(usr_name), close_window(view_window)]).pack()
	else:
		selected_option = StringVar(view_window)
		selected_option.set(options[0]) # default value

		#Dropdown list for the keyword options
		options_list = OptionMenu(view_window, selected_option, *options)
		options_list.pack()

		def get_content_db(sel_key):  
			global content_label
			response = table.query(
			IndexName="key_content",
			KeyConditionExpression = Key('key').eq(sel_key)	
			)
			content = (response['Items'][0]['content'])
			content_label = Label(view_window, text = content, wraplength=800, anchor="e")
			content_label.pack()

		def clear_label():
			try:
				content_label.destroy()
			except:
				pass
		
		def ok():
			selected_option_value = selected_option.get()
			get_content_db(selected_option_value)	

		ok_button = Button(view_window, text="OK", font = "30", command= lambda : [clear_label(), ok()] )
		ok_button.pack()

		view_window.resizable(True, True) 
		Button(view_window, text = "Back", font = "30", command = lambda : [user_homepage(usr_name), close_window(view_window)]).pack()

#Function to accept the image from the user and perform ocr and perform api request on the output of OCR
def upload_file(usr_name): 
  
	#Accepting the image file
	file = askopenfilename(parent = user_w, filetypes = [("Image File", "*.jpg"),("Image File", "*.png"),("Image File", "*.jpeg")])
	
	if(file):
		table = connect_db("dce_db.content")
		response = table.query(
		IndexName="user_content",
		KeyConditionExpression=Key('user_name').eq(usr_name),
		)
		i=0
		options = []
		for items in response['Items']:
			entry = response['Items'][i]
			i = i+1
			user_name = entry['key']
			options.append(user_name)


		file_extension = os.path.splitext(file)
		file_name = os.path.basename(file)
		(file_name1, file_extension1)  = os.path.splitext(file_name)
		#Opening the accepted image file using PIL and saving it to local folder
		img = Image.open(file)
		save_folder = '/home/prajwal/Documents/Codes/DataScience/dce-aws/uploaded_images/'

		dest_add = save_folder + file_name
		#Convert Image file to .PNG if its JPG 
		if( file_extension[1]==".jpg" ):
			img = img.convert('RGBA')
			dest_add = save_folder + file_name1 + '.png'
		#save file 
		img = img.save(dest_add)

		#Recognise the charachters in the image
		OCR_text = OCR.recognise(dest_add)

		if OCR_text in options:
			empty_label = Label(user_w, text = "Content already exists for this keyword! Try a different keyword.", font = (100), fg="red")
			empty_label.pack()

		else:	
			try:
				#Fetch content from wikipedia using the keyword from OCR
				lambda_input = {
				'user_name': usr_name,
				'key': OCR_text,
				'image_path': dest_add
				}
				url = "https://6dtradfkv3.execute-api.ap-southeast-1.amazonaws.com/dce/content-management"
				response = requests.post(url, data = json.dumps(lambda_input))
				response_return = response.json()
				return_body = json.loads(response_return['body'])
				Label(user_w, text = return_body['message'], fg = "green" ,font = ("calibri", 11)).pack()
			except:
				Label(user_w, text = "An error occured while requesting service! Please try again.", fg = "red" ,
					font = ("calibri", 11)).pack()
	else:
		Label(user_w, text = "An error occured while processing the image. Please try again or use another image.", fg = "red" ,
					font = ("calibri", 11)).pack()
	
#user's personal page
def user_homepage(usr_name):
	
	global user_w
	user_w = Tk()
	user_w.title("User HomePage")
	width, height = user_w.winfo_screenwidth(), user_w.winfo_screenheight()
	user_w.geometry('%dx%d+0+0' % (width,height))

	Label(user_w, text = "Data Collection Engine", bg = "blue",
	width="600", height = "2", font = ("Arial 50 bold")).pack()

	Label(user_w, text = "").pack()
	welcome_message = 'Welcome back ' + usr_name
	Label(user_w, text = welcome_message, font = "30").pack()

	edit_button = Button(user_w, text = 'Edit Profile', font = "15", command = lambda : edit_profile(usr_name))
	edit_button.pack() 

	upload_button = Button(user_w, text = 'Upload', font = "30", command = lambda : upload_file(usr_name))
	upload_button.pack()
	
	view_button = Button(user_w, text = 'View Content', font = "30", command = lambda : view_content(usr_name))
	view_button.pack() 
	
	Button(user_w, text = "Back", font = "30", command = lambda : [close_window(user_w), homepage()]).pack()

#Function to validate user login
def verify_user():
	usr_name = username.get()
	usr_password = password.get()
	hashed_password = hash_str(usr_name+usr_password)

	table = connect_db("dce_db.user_info")	

	try:
		response = table.get_item(
			Key={
			'user_name': usr_name,
			}
		)
		if(response['Item']['user_name'] == usr_name):
			actual_password = (response['Item']['password'])
			if (actual_password == hashed_password):
				user_homepage(usr_name)
				close_window(main_window)
			else:
				pswd_error = Label(main_window, text = "Login not authenticated. Please try again", fg = "red" ,font = ("calibri", 11))
				pswd_error.pack()
	except:
		pswd_error = Label(main_window, text = "Login not authenticated. Please try again", fg = "red" ,font = ("calibri", 11))
		pswd_error.pack()

#Function to create a new user entry in DynamoDB
def create_user():
	usr_name = username_entry1.get()	
	usr_password = password_entry1.get()
	usr_email = email_entry1.get()
	hashed_password = hash_str(usr_name + usr_password)
	current_time = str(datetime.datetime.now())

	names = []
	emails = []

	table = connect_db("dce_db.user_info")	
	response = table.scan()
	i=0
	for items in (response['Items']):
		entry = response['Items'][i]
		i = i+1
		names.append(entry['user_name'])
		emails.append(entry['email'])
	
	flag=0

	if usr_name in names:
		flag = 1
	
	regex = "^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
	if not(re.search(regex,usr_email)):
		flag = 2
	
	if usr_email in emails:
		flag = 3
			
	
	if(flag == 1):
		Label(register_w, text = "Username already exists. Try a different username", fg = "red" ,font = ("calibri", 11)).pack()
	if(flag == 2):
		Label(register_w, text = "Enter a valid email", fg = "red" ,font = ("calibri", 11)).pack()
	if(flag == 3):
		Label(register_w, text = "Email already exists. Try a different email", fg = "red" ,font = ("calibri", 11)).pack()
	if(flag==0):
		insert_query = table.put_item( 
			Item={ 
			"email":usr_email, 
			"user_name":usr_name, 
			"password":hashed_password, 
			"created_date":current_time, 
			"updated_time":current_time } 
			)
		Label(register_w, text = "Registration Sucessful, Please go back to the Login Page", fg = "green" ,font = ("calibri", 11)).pack()
	
	email_entry1.delete(0, END)	
	username_entry1.delete(0, END)
	password_entry1.delete(0, END)	
	
#Function to esablish connection to the DynamoDB table mentioned as 'table_name'
def connect_db(table_name):
	table = dynamodb.Table(table_name)
	return table

#User Registration page
def register_user():
	global register_w
	register_w = Tk()
	register_w.title("New Registration")
	width, height = register_w.winfo_screenwidth(), register_w.winfo_screenheight()
	register_w.geometry('%dx%d+0+0' % (width,height))

	global username_entry
	global password_entry
	global email_entry
	global username_entry1
	global password_entry1
	global email_entry1
	username_entry = StringVar() 
	password_entry  = StringVar()
	email_entry = StringVar()
	
	Label(register_w, text = "Data Collection Engine", bg = "blue",
	width="600", height = "2", font = ("Arial 50 bold")).pack()

	Label(register_w, text = "").pack()
	Label(register_w, text = "Please enter your details", font = "30").pack()
	Label(register_w, text = "").pack()
	
	Label(register_w, text = "Email", font = "30").pack()
	email_entry1 = Entry(register_w, textvariable = email_entry)
	email_entry1.pack()
	
	Label(register_w, text = "Username", font = "30").pack()
	username_entry1 = Entry(register_w, textvariable = username_entry)
	username_entry1.pack()
	
	Label(register_w, text = "Password", font = "30").pack()
	password_entry1 = Entry(register_w, show="*", textvariable = password_entry)
	password_entry1.pack()
	
	Button(register_w, text = "Submit", font = "30", command = create_user).pack()
	Button(register_w, text = "Back", font = "30", command = lambda : [close_window(register_w), homepage()]).pack()

#Function to destroy a window
def close_window(window_name):
	window_name.destroy()

#Login oage or the homepage
def homepage():
	global main_window
	main_window = Tk()
	main_window.title("Data Collection Engine")
	width, height = main_window.winfo_screenwidth(), main_window.winfo_screenheight()
	main_window.geometry('%dx%d+0+0' % (width,height))
	global username
	global password
	global username1
	global password1
	username = StringVar()
	password  = StringVar()

	Label(text = "Data Collection Engine", bg = "blue",
	width="600", height = "2", font = ("Arial 50 bold")).pack()

	Label(text = "").pack()
	Label(text = "Login / Register", font = "30").pack()	

	Label(text = "").pack()
	Label(text = "Username", font = "30").pack()
	username1 = Entry(main_window, textvariable = username)
	username1.pack()

	Label(text = "Password", font = "30").pack()
	password1 = Entry(main_window, show="*", textvariable = password)
	password1.pack()

	Label(text = "").pack()

	Button(text = "Login", font = "30", command = verify_user).pack()
	Button(text = "Create a new account", font = "30", command = lambda : [register_user(), close_window(main_window)]).pack()
	Button(text = "Exit", font = "30", command = lambda : close_window(main_window)).pack()

	main_window.mainloop()

if __name__ == '__main__':
	homepage()

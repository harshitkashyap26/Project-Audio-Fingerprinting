# import required module 
import speech_recognition as sr 
from PIL import Image


# explicit function to take input commands 
# and recognize them 
def takeCommandHindi(): 
		
	r = sr.Recognizer() 
	with sr.Microphone() as source: 
		
		# seconds of non-speaking audio before 
		# a phrase is considered complete 
		print('Listening') 
		r.pause_threshold = 0.7
		audio = r.listen(source) 
		try: 
			print("Recognizing") 
			Query = r.recognize_google(audio) 
			
			# for listening the command in indian english 
			print("the query is printed='", Query, "'") 
		
		# handling the exception, so that assistant can 
		# ask for telling again the command 
		except Exception as e: 
			print(e) 
			print("Say that again sir") 
			return "None"
		return Query

# Driver Code 
		
# call the function 
sound = takeCommandHindi()
if sound.strip() == 'ka':
    im = Image.open(r"ka.png")  
    im.show() 
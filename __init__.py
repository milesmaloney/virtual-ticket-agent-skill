from mycroft import MycroftSkill, intent_file_handler
import sqlite3
import googlemaps, geocoder
from datetime import datetime
import random
import time
import requests
from requests.exceptions import HTTPError
import json

class VirtualTicketAgent(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.serverURL = "https://my-json-server.typicode.com/ajplaza31/end-to-end-demo/Customer"
    
    #this intent handler is the default intent handler given by msk create
    @intent_file_handler('agent.ticket.virtual.intent')
    def handle_agent_ticket_virtual(self, message):
        self.speak_dialog('agent.ticket.virtual')

        
    #this intent handler is called when the user is asking to see all available tickets
    @intent_file_handler('tickets.list.intent')
    def handle_tickets_list(self, message):
        database1 = "cubic.sql"

        # create a database connection
        conn = sqlite3.connect(database1)
        cur = conn.cursor()
    
        cur.execute("SELECT * FROM PassData")
        rows = cur.fetchall()
        i=1
        self.speak('Here are the available tickets.')
        for row in rows:
            cur.execute("SELECT * FROM TransitLine WHERE LineID = ?", (row[3],))
            idrow = cur.fetchone()
            self.speak('Ticket {} starts at {}, ends at {}, has an E.T.A of {}, and costs ${}.'.format(i, row[4], row[5], idrow[3], row[6]))
            i += 1
        conn.close()

        
    #this intent handler is called when the user asks about available tickets
    @intent_file_handler('info.ticket.show.intent')
    def handle_info_ticket_show(self, message):
        conn = sqlite3.connect("cubic.sql") 
        cur = conn.cursor()
    
        cur.execute("SELECT * FROM PassData")
        rows = cur.fetchall()

        
        i=1
        answer = "yes"
        while (answer == "yes"):
            i = 1
            self.speak('Here are the available tickets: ')
            for row in rows:
                cur.execute("SELECT * FROM TransitLine WHERE LineID = ?", (row[3],))
                idrow = cur.fetchone()
                self.speak('Ticket number {} : starts at {}, ends at {}, has an E.T.A of {}, and costs ${}.'.format(i, row[4], row[5], idrow[3], row[6]))
                i += 1

            n = int(self.get_response('These are all the tickets available. Which ticket would you like to select?'))
            m = n
            n = n - 1

            cur.execute("SELECT * FROM PassData LIMIT 1 OFFSET ?", (n,))
            ticket = cur.fetchone()

            cur.execute("SELECT * FROM TransitLine WHERE LineID = ?", (ticket[3],))

            idrow = cur.fetchone()

            self.speak('You have chosen to view following ticket: \n')
            self.speak(' Ticket: {}. Start: {},  End: {},  ETA: {},  Cost: ${}.'.format(m, ticket[4], ticket[5], idrow[3], ticket[6]))
            #ask user what to do after ticket info is displayed
            answer = self.ask_yesno('Would you like to choose another ticket to view? Please say yes or no: ')
            if answer == "yes":
                self.speak('Fetching ticket information...')

        self.speak('Thank you. Closing the ticket viewer...')
        conn.close()
        
    #This intent handler is called when the user asks for a route to a destination
    @intent_file_handler('routing.intent')
    def handle_routing_transit(self, message):
        #retrieves key from hidden file and initializes/retrieves client
        keyFile = self.file_system.open(".key.txt", "r")
        key = keyFile.read()
        gmaps = mapsClient.getClient(key)

        #gets the keyword values from the utterance
        departure = message.data.get('departure')
        destination = message.data.get('destination')

        #sets departure as here when there is no departure keyword as specified in mapsClient
        if departure is None:
            departure = "here"

        #receives directions in the format of a response string from Google Maps API through the client
        response = gmaps.getMycroftResponse(departure, destination)

        #responds to the user with directions to where they want to go
        self.speak(response)

    @intent_file_handler('purchaseticket.intent')
    def handle_purchaseticket(self, message):
        conn = sqlite3.connect("cubic.sql") 
        cur = conn.cursor()
    
        cur.execute("SELECT * FROM PassData")
        rows = cur.fetchall()

        self.speak('Here are the available tickets.')
        
        i=1

        for row in rows:
            cur.execute("SELECT * FROM TransitLine WHERE LineID = ?", (row[3],))
            idrow = cur.fetchone()
            self.speak('Ticket {} starts at {}, ends at {}, has an E.T.A of {}, and costs ${}.'.format(i, row[4], row[5], idrow[3], row[6]))
            i += 1
        
        answer = "no"
        while (answer == "no"):
            n = (int)(self.get_response('Which ticket would you like to select? '))
            m = n
            n = n - 1

            cur.execute("SELECT * FROM PassData LIMIT 1 OFFSET ?", (n,))
            ticket = cur.fetchone()

            cur.execute("SELECT * FROM TransitLine WHERE LineID = ?", (ticket[3],))

            idrow = cur.fetchone()

            self.speak('You are about to purchase the following ticket: \n')
            self.speak(' {}. Start: {},  End: {},  ETA: {},  Cost: ${}.'.format(m, ticket[4], ticket[5], idrow[3], ticket[6]))
            answer = self.ask_yesno("Would you like to proceed? ")
    
            idNumber = 0
            isValid = 0
            if (answer == "yes"):
                while (isValid == 0):
                    idNumber = (int)(self.get_response('What is your Customer ID? ').replace(" ", ""))
                   
                    cur.execute("SELECT * FROM Customer WHERE CustomerID = ?", (idNumber,))
                    customer = cur.fetchone()

                    if (customer != None):
                        self.speak('Purchasing ticket from {} to {} for ${}'.format(ticket[4], ticket[5], ticket[6]))
                        newBalance = customer[3] - ticket[6]
                        self.speak('Your new account balance is ${}'.format(newBalance))
                        cur.execute('UPDATE Customer SET Balance = ? WHERE CustomerID =?', (newBalance, idNumber))
                        conn.commit()
                        payload = {'Balance': newBalance}
                        r = requests.post(self.serverURL, data = json.dumps(payload))
                        isValid = 1
                        break
                    elif (customer == None):
                        self.speak('That ID is not in the system. Please try again')
                
                self.speak('Thank you for purchasing! ')
                break
            
        conn.close()
        #self.speak_dialog('purchaseticket')
       
    
    @intent_file_handler('balance.check.intent')
    def handle_balance_check(self, message):
        database1 = "cubic.sql"

        # create a database connection
        conn = sqlite3.connect(database1)
        
        cur = conn.cursor()
        
        answer = "no"
        while (answer == "no"):
            cust = []

            validId = 0
            while (validId == 0):
                n = int(self.get_response('What is your Customer I.D?').replace(" ", ""))

                cur.execute("SELECT * FROM Customer WHERE CustomerID = ?", (n,))
                cust = cur.fetchone()

                if(cust != None):
                    validId = 1
                else:
                    proceed = self.ask_yesno("Customer I.D. is not valid. Would you like to try again? Please say yes or no.")

                    if proceed == "no":
                        self.speak("Have a great day!")
                        return

            answer = self.ask_yesno('You are requesting the account balance for {}. Is this you? Please say yes or no.'.format(cust[2]))
    
        
        self.speak('Your balance is ${}.'.format(cust[3]))
        addmoney = self.ask_yesno('Would you like to add money to your account? Please say yes or no.')

        if addmoney == "yes": 
            amount = round((float(self.get_response("How much money would you like to add?")[1:])),2)
            
            balance = round((amount + cust[3]), 2)

            cur.execute("UPDATE Customer SET Balance = ? WHERE CustomerID = ?", (balance, n,))
            conn.commit()
            payload = {'Balance': balance}
            r = requests.post(self.serverURL, data = json.dumps(payload))
            self.speak('Your balance is now ${}.'.format(balance))

        self.speak("Have a great day!")

        conn.close()

        
def create_skill():
    return VirtualTicketAgent()




#code that the above intent handlers rely on:
#Google Maps routing API client
#Maps client class (singleton): requires ".key.txt" file containing a Google Maps API key
class mapsClient:
    __instance = None
    client = None
    #creates or returns the single instance of the maps client: use this as the constructor
    @staticmethod
    def getClient(key):
        if mapsClient.__instance == None:
            mapsClient.__instance = mapsClient(key)
        return mapsClient.__instance

    #initializes (only called when there is no instance)
    def __init__(self, key):
        if mapsClient.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            mapsClient.__instance = self
            mapsClient.client = googlemaps.Client(key)

    
    #gets the intended route directions
    def getRoute(self, departure, destination):
        #gets the latitude/longitude of the current location for default departure (doesn't affect the string)
        if departure == "here":
            departureLatLng = geocoder.ip('me').latlng
            departure = str(departureLatLng[0]) + "," + str(departureLatLng[1])
        now = datetime.now()
        directions_result = self.client.directions(departure, destination, mode="transit", departure_time=now)
        return directions_result

    def getMycroftResponse(self, departure, destination):
        #initializes a mycroft response string to be built while parsing through the data
        mycroftResponse = ""

        #gets the payload containing relevant information
        directions_result = self.getRoute(departure, destination)
        if len(directions_result) == 0:
            mycroftResponse = "Sorry. Something went wrong, and I wasn't able to get the route from " + departure + " to " + destination + ". Please try again or try asking me in a different way."
            return mycroftResponse
        extractedPayload = extractPayload(directions_result)


        #Builds the mycroft response with the data from google maps
        mycroftResponse += formatTimeandDistance(extractedPayload, departure, destination)
        #loops through data in extracted payload to update the html-instructions into a more human-like format
        for data in extractedPayload: 
            if(isinstance(data, str)):
                mycroftResponse += formatInstructions(data)

        mycroftResponse += "You will then have arrived at your destination."

        return mycroftResponse

#extracts information we need from full directions payload
def extractPayload(jsonPayload):
    newPayload = []
    #google maps' json payloads are stored as lists of json data
    for listElement in jsonPayload:
        #an overarching list "legs" contains the json payloads for directions
        legs = listElement.get("legs")

        #within each leg, there is a json payload of travelling directions
        for leg in legs:
            newPayload.append(leg.get("departure_time"))
            newPayload.append(leg.get("arrival_time"))
            newPayload.append(leg.get("duration"))

            #steps has large payloads of data which include html instructions, distance, start, destination, etc. for each step in the process
            steps = leg.get("steps")
            for step in steps:
                newPayload.append(step.get("html_instructions"))

    return newPayload

#reformats the instruction strings into more human instructions (2 cases specified in API request mode field: either walking or taking public transportation)
def formatInstructions(instruction):
    #splits the instruction into individual words
    instructionParts = instruction.split(" ")

    #normally will say "Bus/Train/Subway/etc to {destination}" for transit directions, but we want our VTA not to speak like a computer
    if instructionParts[0] != "Walk": 
        newInstructionStart = "Take the " + instructionParts[0].lower()
        instructionParts.pop(0) #removes the first element of the instruction parts
        instructionParts.insert(0, newInstructionStart)
        instruction = " ".join(instructionParts)
    instruction = instruction + ". "

    return instruction

#reformats the data payloads for time and distance to how they will be read to the user [takes in the full payload for data accuracy]
def formatTimeandDistance(tdData, departure, destination):
    #payload contains the departure time as the first element
    depTime = tdData[0].get("text") + " " + tdData[0].get("time_zone") + " time"
    depTime = depTime.replace("_"," ")

    #payload contains the ETA as the second element
    ETA = tdData[1].get("text") + " " + tdData[1].get("time_zone") + " time"
    ETA = ETA.replace("_"," ")

    #payload contains the duration as the third element and needs reformatting to be read correctly (the time measurement is abbreviated)
    duration = tdData[2].get("text").replace("mins", "minutes")
    duration = duration.replace("hrs", "hours")

    #puts info together in string to be read by TTS
    tdString = "Leaving " + departure + " at " + depTime + ", you will get to " + destination + " at " + ETA + ". The trip will take " + duration + ". "
    return tdString

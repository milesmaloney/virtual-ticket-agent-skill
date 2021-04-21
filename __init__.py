from mycroft import MycroftSkill, intent_file_handler
import sqlite3

class VirtualTicketAgent(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('agent.ticket.virtual.intent')
    def handle_agent_ticket_virtual(self, message):
        self.speak_dialog('agent.ticket.virtual')

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

    @intent_file_handler('info.ticket.show.intent')
    def handle_info_ticket_show(self, message):
        conn = sqlite3.connect("cubic.sql") 
        cur = conn.cursor()
    
        cur.execute("SELECT * FROM PassData")
        rows = cur.fetchall()

        #self.speak('Here are the available tickets.')
        
        i=1
        answer = "yes"
        while (answer == "yes"):
            i = 1
            self.speak('Here are the available tickets.')
            for row in rows:
                cur.execute("SELECT * FROM TransitLine WHERE LineID = ?", (row[3],))
                idrow = cur.fetchone()
                self.speak('Ticket {} starts at {}, ends at {}, has an E.T.A of {}, and costs ${}.'.format(i, row[4], row[5], idrow[3], row[6]))
                i += 1

            n = int(self.get_response('Which ticket would you like to select?'))
            m = n
            n = n - 1

            cur.execute("SELECT * FROM PassData LIMIT 1 OFFSET ?", (n,))
            ticket = cur.fetchone()

            cur.execute("SELECT * FROM TransitLine WHERE LineID = ?", (ticket[3],))

            idrow = cur.fetchone()

            self.speak('You have chosen to view following ticket: \n')
            self.speak(' Ticket: {}. Start: {},  End: {},  ETA: {},  Cost: ${}.'.format(m, ticket[4], ticket[5], idrow[3], ticket[6]))
            #ask what to do after?
            answer = self.ask_yesno('Would you like to choose another ticket to view? (yes/no): ')
            if answer == "yes":
                self.speak('Fetching ticket information...')

        self.speak('Closing the ticket viewer...')
        conn.close()
        #self.speak_dialog('info.ticket.show')

    @intent_file_handler('routing.transit.intent')
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

def create_skill():
    return VirtualTicketAgent()


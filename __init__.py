from mycroft import MycroftSkill, intent_file_handler


class VirtualTicketAgent(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('agent.ticket.virtual.intent')
    def handle_agent_ticket_virtual(self, message):
        self.speak_dialog('agent.ticket.virtual')


def create_skill():
    return VirtualTicketAgent()


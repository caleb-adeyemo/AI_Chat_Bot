import spacy
from spacy.matcher import PhraseMatcher
from experta import *
import re

"""
import requests

# Set the URL of the Node.js server endpoint
url = ''

# Send a GET request to the endpoint
response = requests.get(url)

# Print the response
print(response.json())
"""
"""
print(f""
                  f"start destination: {self.test_ticket.start_location} \n"
                  f"end destination: {self.test_ticket.end_location} \n"
                  f"Leaving(True)/Arriving(False): {self.test_ticket.leaving} \n"
                  f"Date: {self.test_ticket.date.day}/{self.test_ticket.date.month}\n"
                  f"Time: {self.test_ticket.time} \n"
                  )
"""

# load a language model
nlp = spacy.load("en_core_web_sm")

"""Classes"""


class Ticket(Fact):
    start_location = Field(str)
    end_location = Field(str)
    leaving = Field(bool)
    date = Field(str)
    time = Field(int)
    returning = Field(bool)
    return_leaving = Field(bool)
    return_date = Field(str)
    return_time = Field(str)


class Action(Fact):
    pass


class Statement(Fact):
    pass


class ReturnStatement(Fact):
    pass


class Date(Fact):
    day = Field(int)
    month = Field(str)
    year = Field(int)
    pass


"""Knowledge Base"""


def get_date(doc):
    result = [None, None]
    for token in doc:
        # Find month
        if token.text in months:
            result[0] = str(token.text)
        # get the day
        elif re.match(r'\d+th', str(token.text)):  # Look for the "th" in the sentence
            res = re.sub(r"th\b", "", str(token.text))
            result[1] = res
        elif re.match(r'\d{1,2}/\d{1,2}', token.text):  # Look for 12/06 pattern
            date_parts = token.text.split('/')
            day = int(date_parts[0])
            month = int(date_parts[1])
            result[1] = day
            result[0] = month
    return result


def check_y_n(doc):
    for token in doc:
        if token.text in positive_words:
            return True
        elif token.text in negative_words:
            return False


class Pathfinder(KnowledgeEngine):
    def __init__(self):
        super().__init__()
        # Matcher info
        self.time_matcher = None
        self.time_type = None
        self.city_matcher = None
        # Ticket info
        self.test_ticket = Ticket()  # Location info
        self.test_ticket.start_location = ""
        self.test_ticket.end_location = ""

        self.test_ticket.date = Date()  # Date info
        self.test_ticket.date.day = None
        self.test_ticket.date.month = None
        self.test_ticket.date.year = None

        self.test_ticket.time = None  # Time info
        self.test_ticket.leaving = None

        self.test_ticket.returning = False  # Return info
        self.test_ticket.return_date = Date()
        self.test_ticket.return_time = ""
        self.test_ticket.return_leaving = False
        # Return ticket info
        self.return_ticket = Ticket()
        self.return_ticket.start_location = ""
        self.return_ticket.end_location = ""

        self.return_ticket.date = Date()  # Date info
        self.return_ticket.date.day = None
        self.return_ticket.date.month = None
        self.return_ticket.date.year = None

        self.return_ticket.time = None  # Time info
        self.return_ticket.leaving = True

    @DefFacts()
    def set_up(self):
        # Create a City matcher object
        self.city_matcher = spacy.matcher.PhraseMatcher(nlp.vocab, attr="LOWER")
        pattern_city = [nlp(city) for city in cities_rules]
        self.city_matcher.add("CITIES", pattern_city)

        # Create an arrival/departing detector
        self.time_type = spacy.matcher.PhraseMatcher(nlp.vocab, attr="LOWER")
        pattern_time_type = [nlp(phrase) for phrase in time_type_preposition]
        self.time_type.add("TIME_TYPE", pattern_time_type)

        # Create a time detector
        self.time_matcher = spacy.matcher.PhraseMatcher(nlp.vocab, attr="LOWER")
        pattern_time_preps = [nlp(res) for res in time_prepositions]
        self.time_matcher.add("TIME_PREP", pattern_time_preps)

        # Create the ticket for the booking
        yield Ticket()

    @Rule()
    def start_up(self):
        print("Hi! how can I help you today? : ")
        self.declare(Action("get-users-text"))

    @Rule(AS.get_text << Action("get-users-text"))
    def get_users_text(self, get_text):
        # forget the Action
        self.retract(get_text)
        text = input(f"enter: ")
        # Turn the text into lower case
        text = text.lower()
        # Turn the text into NLP objects
        doc = nlp(text)
        # Add to Pathfinder's memory
        self.declare(Statement(doc))

    # If there is a statement declared
    @Rule(Statement(MATCH.info))
    def get_information(self, info):

        # Call the find_city function to populate self.test_ticket start destination and end destination variables
        loc = self.find_city(info)
        if self.test_ticket.start_location == "":
            self.test_ticket.start_location = loc[0]
        if self.test_ticket.end_location == "":
            self.test_ticket.end_location = loc[1]

        # Get the time information
        time_res = self.get_time(info)
        if self.test_ticket.time is None:
            self.test_ticket.time = time_res[0]
        if self.test_ticket.leaving is None:
            self.test_ticket.leaving = time_res[1]

        # Get the Date information
        date_res = get_date(info)
        if self.test_ticket.date.month is None:
            self.test_ticket.date.month = date_res[0]
        if self.test_ticket.date.day is None:
            self.test_ticket.date.day = date_res[1]

        # Find if the person wants a return

        # Check to see if we've got all the information we need
        self.declare(Action("validate-ticket"))

    @Rule(AS.validate << Action("validate-ticket"))
    def validate_location(self, validate):
        self.retract(validate)
        # No start or end location
        if self.test_ticket.start_location == "" and self.test_ticket.end_location == "":
            self.declare(Action("no-destination"))
        # No end location
        elif self.test_ticket.start_location != "" and self.test_ticket.end_location == "":
            self.declare(Action("no-end-destination"))
        # No start location
        elif self.test_ticket.start_location == "" and self.test_ticket.end_location != "":
            self.declare(Action("no-start-destination"))
        # Got both locations
        elif self.test_ticket.start_location != "" and self.test_ticket.end_location != "":
            self.declare(Action("got-all-destinations"))

    @Rule(AS.no_end_dest << Action("no-end-destination"))
    def no_end_destination(self, no_end_dest):
        self.retract(no_end_dest)
        print("Pls provide an End destination")
        self.declare(Action("get-users-text"))

    @Rule(AS.no_start_dest << Action("no-start-destination"))
    def no_start_destination(self, no_start_dest):
        self.retract(no_start_dest)
        print("Pls provide a Start destination")
        self.declare(Action("get-users-text"))

    @Rule(AS.no_dest << Action("no-destination"))
    def no_destination(self, no_dest):
        self.retract(no_dest)
        print("Pls provide a start and end destination")
        self.declare(Action("get-users-text"))

    @Rule(AS.all_dest << Action("got-all-destinations"))
    def validate_time(self, all_dest):
        self.retract(all_dest)
        # No time information
        if self.test_ticket.time is None:
            print("What time are you thinking?")
            self.declare(Action("get-users-text"))
        else:
            self.declare(Action("got-time"))

    @Rule(AS.all_time << Action("got-time"))
    def validate_date(self, all_time):
        self.retract(all_time)
        if self.test_ticket.date.day is None:
            print("What date would you want to go?")
            self.declare(Action("get-users-text"))
        elif self.test_ticket.date.month is None:
            print("What month would you want to go?")
            self.declare(Action("get-users-text"))
        else:
            self.declare(Action("check-return"))

    @Rule(AS.all_info << Action("check-return"))
    def check_returning(self, all_info):
        self.retract(all_info)
        if not self.test_ticket.returning:
            # ask if the user would like a return ticket
            print("I can see you dont have a return ticket")
            res = "would you like to get a return ticket? Y/N: "
            text = input(res)
            # Turn the text into lower case
            text = text.lower()
            # Turn the text into NLP objects
            doc = nlp(text)

            ans = check_y_n(doc)
            self.test_ticket.returning = ans

            # They want a return ticket
            if ans:
                # Start process for new return ticket
                self.declare(Action("same-station"))
            # They don't want a return ticket
            else:
                print("Done")
                print(f"start destination: {self.test_ticket.start_location} \n"
                      f"end destination: {self.test_ticket.end_location} \n"
                      f"Leaving(True)/Arriving(False): {self.test_ticket.leaving} \n"
                      f"Date: {self.test_ticket.date.day}/{self.test_ticket.date.month}\n"
                      f"Time: {self.test_ticket.time} \n"
                      )
                self.declare(Action("done"))

        # they want a return ticket
        else:
            self.declare(Action("same-station"))

    @Rule(AS.same_stat << Action("same-station"))
    def same_station(self, same_stat):
        self.retract(same_stat)
        res = "would you be traveling from the same station? Y/N: "
        text = input(res)
        # Turn the text into lower case
        text = text.lower()
        # Turn the text into NLP objects
        doc = nlp(text)

        ans = check_y_n(doc)

        # same station
        if ans:
            self.return_ticket.start_location = self.test_ticket.end_location
            self.return_ticket.end_location = self.test_ticket.start_location

        print("can you provide me with more return information")
        self.declare(Action("get-user-return-info"))

    @Rule(AS.rand_name << Action("get-user-return-info"))
    def get_user_text(self, rand_name):
        # forget the Action
        self.retract(rand_name)
        text = input(f"enter: ")
        # Turn the text into lower case
        text = text.lower()
        # Turn the text into NLP objects
        doc = nlp(text)
        # Add to Pathfinder's memory
        self.declare(ReturnStatement(doc))

    @Rule(ReturnStatement(MATCH.info))
    def get_return_information(self, info):
        # Call the find_city function to populate self.test_ticket start destination and end destination variables
        loc = self.find_city(info)
        if self.return_ticket.start_location == "":
            self.return_ticket.start_location = loc[0]
        if self.return_ticket.end_location == "":
            self.return_ticket.end_location = loc[1]

        # Get the time information
        time_res = self.get_time(info)
        if self.return_ticket.time is None:
            self.return_ticket.time = time_res[0]
        if self.return_ticket.leaving is None:
            self.return_ticket.leaving = time_res[1]

        # Get the Date information
        date_res = get_date(info)
        if self.return_ticket.date.month is None:
            self.return_ticket.date.month = date_res[0]
        if self.return_ticket.date.day is None:
            self.return_ticket.date.day = date_res[1]

        # Check to see if we've got all the information we need
        self.declare(Action("validate-return-ticket"))

    @Rule(AS.validate << Action("validate-return-ticket"))
    def validate_return_location(self, validate):
        self.retract(validate)
        # No start or end location
        if self.return_ticket.start_location == "" and self.return_ticket.end_location == "":
            self.declare(Action("no-return-destination"))
        # No end location
        elif self.return_ticket.start_location != "" and self.return_ticket.end_location == "":
            self.declare(Action("no-return-end-destination"))
        # No start location
        elif self.return_ticket.start_location == "" and self.return_ticket.end_location != "":
            self.declare(Action("no-return-start-destination"))
        # Got both locations
        elif self.return_ticket.start_location != "" and self.return_ticket.end_location != "":
            self.declare(Action("got-all-return-destinations"))

    @Rule(AS.no_end_dest << Action("no-return-end-destination"))
    def no_return_end_destination(self, no_end_dest):
        self.retract(no_end_dest)
        print("Pls provide an End destination")
        self.declare(Action("get-user-return-info"))

    @Rule(AS.no_start_dest << Action("no-return-start-destination"))
    def no_return_start_destination(self, no_start_dest):
        self.retract(no_start_dest)
        print("Pls provide a Start destination")
        self.declare(Action("get-user-return-info"))

    @Rule(AS.no_dest << Action("no-return-destination"))
    def no_return_destination(self, no_dest):
        self.retract(no_dest)
        print("Pls provide a start and end destination")
        self.declare(Action("get-user-return-info"))

    @Rule(AS.all_dest << Action("got-all-return-destinations"))
    def validate_return_time(self, all_dest):
        self.retract(all_dest)
        # No time information
        if self.return_ticket.time is None:
            print("What time are you thinking?")
            self.declare(Action("get-user-return-info"))
        else:
            self.declare(Action("got-return-time"))

    @Rule(AS.all_time << Action("got-return-time"))
    def validate_return_date(self, all_time):
        self.retract(all_time)
        if self.return_ticket.date.day is None:
            print("What date would you want to go?")
            self.declare(Action("get-user-return-info"))
        elif self.return_ticket.date.month is None:
            print("What month would you want to go?")
            self.declare(Action("get-user-return-info"))
        else:
            print("Departure")
            print(f"start destination: {self.test_ticket.start_location} \n"
                  f"end destination: {self.test_ticket.end_location} \n"
                  f"Leaving(True)/Arriving(False): {self.test_ticket.leaving} \n"
                  f"Date: {self.test_ticket.date.day}/{self.test_ticket.date.month}\n"
                  f"Time: {self.test_ticket.time} \n"
                  )
            print("Return")
            print(f"start destination: {self.return_ticket.start_location} \n"
                  f"end destination: {self.return_ticket.end_location} \n"
                  f"Leaving(True)/Arriving(False): {self.return_ticket.leaving} \n"
                  f"Date: {self.return_ticket.date.day}/{self.return_ticket.date.month}\n"
                  f"Time: {self.return_ticket.time} \n"
                  )
            self.declare(Action("done"))

    def find_city(self, doc):
        # Check to see if a city is found in the text
        city_matches = self.city_matcher(doc)

        # initialise the return variables
        start_loc = ""
        end_loc = ""

        # You find at least one city
        if len(city_matches) > 0:
            # Find all the cities in the sentence, and append their prev word to the city name
            for match_id, start, end in city_matches:
                if str(doc[start - 1]) in departure_prepositions:
                    start_loc = str(doc[start:end])
                elif str(doc[start - 1]) in arrival_prepositions:
                    end_loc = str(doc[start:end])
        ans = [start_loc, end_loc]
        return ans

    def get_time(self, doc):

        matches = self.time_matcher(doc)

        res = [None, None]

        if len(matches) > 0:
            for match_id, start, end in matches:
                if doc[start:end].text in ["am", "pm"]:
                    res[0] = doc[start-1]
                elif doc[start + 1].ent_type_ == "TIME" or doc[start + 1].ent_type_ == "CARDINAL":
                    res[0] = int(str(doc[start + 1]))
                # Leaving(True) or arriving(False) - (Time type)
                res[1] = self.get_time_type(doc)
        return res

    def get_time_type(self, doc):
        # Check to see if a time_type preposition was found in the sentence
        type_matches = self.time_type(doc)

        # You find at least one preposition
        if len(type_matches) > 0:
            return False
        return True


"""INFORMATION --Should be gotten from the database--"""
# Initialize a list of all possible cities the Bot should be able to handle
cities_rules = ["new york", "san francisco", "norwich", "london", "manchester", "birmingham", "bristol", "york",
                "cambridge", "liverpool", "oxford", "newcastle", "brighton", "nottingham", "plymouth", "leeds",
                "southampton", "sheffield", "exeter", "coventry", "hull", "portsmouth"]

# Initialize possible prepositions for the sentences
departure_prepositions = ["from"]
arrival_prepositions = ["to", "in", "at"]
time_prepositions = ["at", "by", "am", "pm"]
time_type_preposition = ["arriving", "arrive", "getting"]
months = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]

# Positive words
positive_words = ["y", "yes", "yeah", "yup", "sure", "absolutely", "definitely",
                  "certainly", "of course", "okay", "ok", "all right", "fine", "great",
                  "excellent", "fantastic", "wonderful", "awesome", "gladly", "no problem"]
# Negative words
negative_words = ["n", 'no', 'nah', 'nope', 'not really', 'sorry', "i'm good", "im good"]

if __name__ == "__main__":
    chatbot = Pathfinder()
    chatbot.reset()
    chatbot.run()

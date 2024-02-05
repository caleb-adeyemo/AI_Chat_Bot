import spacy
from spacy.matcher import PhraseMatcher
from experta import *
import re
import json

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

def get_nearest_valid_mins(time):
    hrs, mins = time.split(":")

    mins_dict = {
        "o_clock": abs(int(mins)),
        "quarter_past": abs(int(mins) - 15),
        "half_past": abs(int(mins) - 30),
        "quarter_to": abs(int(mins) - 45)
    }

    min_val = min(mins_dict, key=mins_dict.get)

    if min_val == "o_clock":
        return hrs, str(0)
    elif min_val == "quarter_past":
        return hrs, str(15)
    elif min_val == "half_past":
        return hrs, str(30)
    else:
        return hrs, str(45)


def print_bot_message(message):
    message_dict = {
        "type": "botMessage",
        "content": message
    }
    print(json.dumps(message_dict))

def print_train_journey(train_journey_dict):
    message_dict = {
        "type": "trainJourney",
        "content": {
            "single": train_journey_dict["single"],
            "return": train_journey_dict["return"]
        }
    }
    print(json.dumps(message_dict))

def get_psql_query(rule):
    message_dict = {
        "type": "pgQuery",
        "content": rule
    }
    print(json.dumps(message_dict))
    values = input()
    return values


        # {
        #     "depStation": train_journey_dict["single"].["depStation"],
        #     "arrStation": train_journey_dict["single"]["arrStation"],
        #     "depDate": train_journey_dict["single"]["depDate"],
        #     "depTimHrs": train_journey_dict["single"]["depTimHrs"],
        #     "depTimMins": train_journey_dict["single"]["depTimMins"],
        #     "arrTimHrs": train_journey_dict.["single"].["arrTimHrs"],
        #     "arrTimMins": train_journey_dict["single"]["arrTimMins"]
        # }

        # {
        #     "depDate": train_journey_dict["return"]["depDate"],
        #     "depTimHrs": train_journey_dict["return"]["depTimHrs"],
        #     "depTimMins": train_journey_dict["return"]["depTimMins"],
        #     "arrTimHrs": train_journey_dict.["return"].["arrTimHrs"],
        #     "arrTimMins": train_journey_dict["return"]["arrTimMins"]
        # }

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
    # Construct regular expression pattern to search for
    pos_pattern = "|".join(["\\b{}\\b".format(word) for word in positive_words])
    neg_pattern = "|".join(["\\b{}\\b".format(word) for word in negative_words])

    # Search for the pattern in the sentence
    match_pos = re.search(pos_pattern, doc.text)
    match_neg = re.search(neg_pattern, doc.text)

    # Check for negative words first cuz of cases like "nah I'm all right"
    if match_neg:
        return False
    elif match_pos:
        return True


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
        pattern_time_type = [nlp(phrase) for phrase in time_type_prepositions]
        self.time_type.add("TIME_TYPE", pattern_time_type)

        # Create a time detector
        self.time_matcher = spacy.matcher.PhraseMatcher(nlp.vocab, attr="LOWER")
        pattern_time_preps = [nlp(res) for res in time_prepositions]
        self.time_matcher.add("TIME_PREP", pattern_time_preps)

        # Create the ticket for the booking
        yield Ticket()

    @Rule()
    def start_up(self):
        print_bot_message("Hi! how can I help you today? : ")
        # print("Hi! how can I help you today? : ")
        self.declare(Action("get-users-text"))

    @Rule(AS.get_text << Action("get-users-text"))
    def get_users_text(self, get_text):
        # forget the Action
        self.retract(get_text)
        text = input()
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
        print_bot_message("Pls provide an End destination")
        # print("Pls provide an End destination")
        self.declare(Action("get-users-text"))

    @Rule(AS.no_start_dest << Action("no-start-destination"))
    def no_start_destination(self, no_start_dest):
        self.retract(no_start_dest)
        print_bot_message("Pls provide a Start destination")
        # print("Pls provide a Start destination")
        self.declare(Action("get-users-text"))

    @Rule(AS.no_dest << Action("no-destination"))
    def no_destination(self, no_dest):
        self.retract(no_dest)
        print_bot_message("Pls provide a start and end destination")
        # print("Pls provide a start and end destination")
        self.declare(Action("get-users-text"))

    @Rule(AS.all_dest << Action("got-all-destinations"))
    def validate_time(self, all_dest):
        self.retract(all_dest)
        # No time information
        if self.test_ticket.time is None:
            print_bot_message("What time are you thinking?")
            # print("What time are you thinking?")
            self.declare(Action("get-users-text"))
        else:
            self.declare(Action("got-time"))

    @Rule(AS.all_time << Action("got-time"))
    def validate_date(self, all_time):
        self.retract(all_time)
        if self.test_ticket.date.day is None:
            print_bot_message("What date would you want to go?")
            # print("What date would you want to go?")
            self.declare(Action("get-users-text"))
        elif self.test_ticket.date.month is None:
            print_bot_message("What month would you want to go?")
            # print("What month would you want to go?")
            self.declare(Action("get-users-text"))
        else:
            self.declare(Action("check-return"))

    @Rule(AS.all_info << Action("check-return"))
    def check_returning(self, all_info):
        self.retract(all_info)
        if not self.test_ticket.returning:
            # ask if the user would like a return ticket
            print_bot_message("I can see you dont have a return ticket")
            # print("I can see you dont have a return ticket")
            print_bot_message("would you like to get a return ticket? Y/N: ")
            text = input()
            # res = "would you like to get a return ticket? Y/N: "
            # text = input(res)
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
                print_bot_message("Done")
                # print("Done")
                train_journey_dict = {
                    "single": {
                        "depStation": self.test_ticket.start_location,
                        "arrStation": self.test_ticket.end_location,
                        "depDate": f"{self.test_ticket.date.day}/{self.test_ticket.date.month}/2023"
                    },
                    "return": None
                }

                ticket_hrs, ticket_mins = get_nearest_valid_mins(self.test_ticket.time)

                if self.test_ticket.leaving == True:
                    train_journey_dict["single"].update({
                        "depTimHrs": ticket_hrs,
                        "depTimMins": ticket_mins,
                        "arrTimHrs": None,
                        "arrTimMins": None
                    })
                else:
                    train_journey_dict["single"].update({
                        "depTimHrs": None,
                        "depTimMins": None,
                        "arrTimHrs": ticket_hrs,
                        "arrTimMins": ticket_mins
                    })
                train_journey_dict["return"] = None
                print_train_journey(train_journey_dict)

                # print(f"start destination: {self.test_ticket.start_location} \n"
                #       f"end destination: {self.test_ticket.end_location} \n"
                #       f"Leaving(True)/Arriving(False): {self.test_ticket.leaving} \n"
                #       f"Date: {self.test_ticket.date.day}/{self.test_ticket.date.month}\n"
                #       f"Time: {self.test_ticket.time} \n"
                #       )
                self.declare(Action("done"))
        # they want a return ticket
        else:
            self.declare(Action("same-station"))

    @Rule(AS.same_stat << Action("same-station"))
    def same_station(self, same_stat):
        self.retract(same_stat)
        print_bot_message("would you be traveling from the same station? Y/N: ")
        text = input()
        # res = "would you be traveling from the same station? Y/N: "
        # text = input(res)
        # Turn the text into lower case
        text = text.lower()
        # Turn the text into NLP objects
        doc = nlp(text)

        ans = check_y_n(doc)

        # same station
        if ans:
            self.return_ticket.start_location = self.test_ticket.end_location
            self.return_ticket.end_location = self.test_ticket.start_location

        print_bot_message("can you provide me with more return information")
        # print("can you provide me with more return information")
        self.declare(Action("get-user-return-info"))

    @Rule(AS.rand_name << Action("get-user-return-info"))
    def get_user_text(self, rand_name):
        # forget the Action
        self.retract(rand_name)
        # text = input(f"enter: ")
        print_bot_message('enter: ')
        text = input()
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
        print_bot_message("Pls provide an End destination")
        # print("Pls provide an End destination")
        self.declare(Action("get-user-return-info"))

    @Rule(AS.no_start_dest << Action("no-return-start-destination"))
    def no_return_start_destination(self, no_start_dest):
        self.retract(no_start_dest)
        print_bot_message("Pls provide a Start destination")
        # print("Pls provide a Start destination")
        self.declare(Action("get-user-return-info"))

    @Rule(AS.no_dest << Action("no-return-destination"))
    def no_return_destination(self, no_dest):
        self.retract(no_dest)
        print_bot_message("Pls provide a start and end destination")
        # print("Pls provide a start and end destination")
        self.declare(Action("get-user-return-info"))

    @Rule(AS.all_dest << Action("got-all-return-destinations"))
    def validate_return_time(self, all_dest):
        self.retract(all_dest)
        # No time information
        if self.return_ticket.time is None:
            print_bot_message("What time are you thinking?")
            # print("What time are you thinking?")
            self.declare(Action("get-user-return-info"))
        else:
            self.declare(Action("got-return-time"))

    @Rule(AS.all_time << Action("got-return-time"))
    def validate_return_date(self, all_time):
        self.retract(all_time)
        if self.return_ticket.date.day is None:
            print_bot_message("What date would you want to go?")
            # print("What date would you want to go?")
            self.declare(Action("get-user-return-info"))
        elif self.return_ticket.date.month is None:
            print_bot_message("What month would you want to go?")
            # print("What month would you want to go?")
            self.declare(Action("get-user-return-info"))
        else:
            train_journey_dict = {
                "single": {
                    "depStation": self.test_ticket.start_location,
                    "arrStation": self.test_ticket.end_location,
                    "depDate": f"{self.test_ticket.date.day}/{self.test_ticket.date.month}/2023"
                },
                "return": {
                    "depDate": f"{self.return_ticket.date.day}/{self.return_ticket.date.month}/2023"
                }
            }

            single_hrs, single_mins = get_nearest_valid_mins(self.test_ticket.time)
            return_hrs, return_mins = get_nearest_valid_mins(self.return_ticket.time)

            if self.test_ticket.leaving == True:
                train_journey_dict["single"].update({
                    "depTimHrs": single_hrs,
                    "depTimMins": single_mins,
                    "arrTimHrs": None,
                    "arrTimMins": None
                })
            else:
                train_journey_dict["single"].update({
                    "depTimHrs": None,
                    "depTimMins": None,
                    "arrTimHrs": single_hrs,
                    "arrTimMins": single_mins
                })

            if self.return_ticket.leaving == True:
                train_journey_dict["return"].update({
                    "depTimHrs": return_hrs,
                    "depTimMins": return_mins,
                    "arrTimHrs": None,
                    "arrTimMins": None
                })
            else:
                train_journey_dict["return"].update({
                    "depTimHrs": None,
                    "depTimMins": None,
                    "arrTimHrs": return_hrs,
                    "arrTimMins": return_mins
                })
            print_train_journey(train_journey_dict)

            # print("Departure")
            # ticket = {
            #     "start destination": self.test_ticket.start_location,
            #     "end destination" : self.test_ticket.end_location,
            #     "Leaving": self.test_ticket.leaving
            # }
            # print(f"start destination: {self.test_ticket.start_location} \n"
            #       f"end destination: {self.test_ticket.end_location} \n"
            #       f"Leaving(True)/Arriving(False): {self.test_ticket.leaving} \n"
            #       f"Date: {self.test_ticket.date.day}/{self.test_ticket.date.month}\n"
            #       f"Time: {self.test_ticket.time} \n"
            #       )
            # print("Return")
            # print(f"start destination: {self.return_ticket.start_location} \n"
            #       f"end destination: {self.return_ticket.end_location} \n"
            #       f"Leaving(True)/Arriving(False): {self.return_ticket.leaving} \n"
            #       f"Date: {self.return_ticket.date.day}/{self.return_ticket.date.month}\n"
            #       f"Time: {self.return_ticket.time} \n"
            #       )
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
        # Regular expression pattern to match time in hh:mm format
        time_pattern = re.search(r'\d{1,2}:\d{2}', doc.text)

        res = [None, None]
        # found a time prep in the sentence
        if len(matches) > 0:
            # Leaving(True) or arriving(False) - (Time type)
            res[1] = self.get_time_type(doc)

            for match_id, start, end in matches:
                # if res[1] is True:
                #     # Find the first occurrence of the time pattern after any departure prep
                #     match = re.search(r'{departure_prepositions}\s+' + time_pattern.pattern, doc.text)
                # elif res[1] is False:
                #     # look for first occurrence of a time after any arrival prep
                #     match = re.search(r'{arrival_prepositions}\s+' + time_pattern.pattern, doc.text)

                if doc[start + 1].ent_type_ == "TIME" or doc[start + 1].ent_type_ == "CARDINAL":
                    if time_pattern:
                        # Regular expression pattern to match time in hh:mm format
                        time_pattern = re.compile(r'\d{1,2}:\d{2}')
                        # Find all occurrences of time pattern in the text
                        times = re.findall(time_pattern, doc.text)
                        res[0] = ' '.join(times)
                    else:
                        res[0] = int(str(doc[start + 1]))
        return res

    def get_time_type(self, doc):
        # Check to see if a time_type preposition was found in the sentence
        type_matches = self.time_type(doc)

        # You find at least one preposition
        if len(type_matches) > 0:
            return False
        return True


"""INFORMATION --Should be gotten from the database--"""
# cities_rules, departure_prepositions, arrival_prepositions, time_prepositions,
# time_type_prepositions, months, positive_words, negative_words

cities_rules = json.loads(get_psql_query("cities_rules"))
departure_prepositions = json.loads(get_psql_query("departure_prepositions"))
arrival_prepositions = json.loads(get_psql_query("arrival_prepositions"))
time_prepositions = json.loads(get_psql_query("time_prepositions"))
time_type_prepositions = json.loads(get_psql_query("time_type_prepositions"))
months = json.loads(get_psql_query("months"))
positive_words = json.loads(get_psql_query("positive_words"))
negative_words = json.loads(get_psql_query("negative_words"))

# # Initialize a list of all possible cities the Bot should be able to handle
# cities_rules = ["new york", "san francisco", "norwich", "london", "manchester", "birmingham", "bristol", "york",
#                 "cambridge", "liverpool", "oxford", "newcastle", "brighton", "nottingham", "plymouth", "leeds",
#                 "southampton", "sheffield", "exeter", "coventry", "hull", "portsmouth", "romford"]
#
# # Initialize possible prepositions for the sentences
# departure_prepositions = ["from"]
# arrival_prepositions = ["to", "in", "at"]
# time_prepositions = ["at", "by"]
# time_type_prepositions = ["arriving", "arrive", "getting", "get"]
# months = ["january", "february", "march", "april", "may", "june",
#           "july", "august", "september", "october", "november", "december"]
#
# # Positive words
# positive_words = ["y", "yes", "yeah", "yup", "sure", "absolutely", "definitely",
#                   "certainly", "of course", "okay", "ok", "all right", "fine", "great",
#                   "excellent", "fantastic", "wonderful", "awesome", "gladly", "no problem", "like to"]
# # Negative words
# negative_words = ["n", 'no', 'nah', 'nope', 'not really', 'sorry', "i'm good", "im good", "don't", "dont"]

if __name__ == "__main__":
    chatbot = Pathfinder()
    chatbot.reset()
    chatbot.run()

import spacy
from spacy.matcher import PhraseMatcher
from experta import *
from dotenv import load_dotenv
import os
import random
import re
import datetime
import psycopg2
import json

load_dotenv()       # Load .env file with PostgreSQL details
# Connect to PostgreSQL database
connect = psycopg2.connect(
    host=os.environ.get("PGHOST"),
    user=os.environ.get("PGUSER"),
    password=os.environ.get("PGPASSWORD"),
    database=os.environ.get("PGDATABASE"),
    port=os.environ.get("PGPORT")
)
cursor = connect.cursor()   # Cursor object for performing SQL queries

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Regular Expressions
greetings = ['hello', 'hey', 'hi', 'yo']
greeting_regex = re.compile(fr'(?i)\b({"|".join(greetings)})\b')

false = ["false", "no", "nah"]
false_regex = re.compile(fr'(?i)\b({"|".join(false)})\b')

true = ["true", "yes", "yeah", "yh"]
true_regex = re.compile(fr'(?i)\b({"|".join(true)})\b')

# Dicts & Lists
time_type_preposition = ["arriving", "arrive", "getting", "get"]

class Ticket(Fact):
    pass


class Greeting(Fact):
    pass


class Delay(Fact):
    pass


# Define Expert System rules
class TravelBot(KnowledgeEngine):
    def __init__(self):
        super().__init__()
        self.brain = {
            'location': {
                'start_loc': None,
                'end_loc': None
            },
            'time': {
                'time_value': None,
                'is_leaving_time': True
            },
            'date': {
                'day': None,
                'month': None,
                '24hrs': ""
            },
            'intent': {
                'book': False,
                'predict': False
            },
            'return_trip': False,
            'return_info': {
                'location': {
                    'start_loc': None,
                    'end_loc': None
                },
                'time': {
                    'time_value': None,
                    'is_leaving_time': True
                },
                'date': {
                    'day': None,
                    'month': None
                }
            }
        }

        self.delay_info = {
            "location": {
                "start_loc": None,
                "end_loc": None
            },
            "og_dep_time": None,
            "og_arr_time": None,
            "delay": None
        }

    @DefFacts()
    def _initial_action(self):
        yield Greeting(greet=True)

    @Rule(Greeting(greet=True))
    def greet(self):
        responses = ["Welcome! I'm your friendly Train Ticket Chatbot. 😊 Need cheap train tickets or predictions on "
                     "delays? I've got you covered! Just tell me where you're leaving from, where you're going, "
                     "the time and date you want to travel, and I'll find the best options for you. Let's make your "
                     "journey smooth and affordable. "]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)
        print_bot_message("What would you like to do, make a delay prediction or book a ticket?")

    # Doesn't matter if anything else is given/not, as long as start location is not received
    @Rule(Ticket(departure=None, arrival=W(), time=W(), isleavingtime=W(), day=W(), month=W(),
                 returnTrip=W(), returnStartLocation=W(), returnEndLocation=W(), returnTime=W(),
                 returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_start_location(self):
        responses = ["What station would you be leaving from?", "Where would you be traveling from?",
                     "What the start Location?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

    # Doesn't matter if anything else is given/not, as long as start location is received but the end location is not
    @Rule(Ticket(departure=~L(None), arrival=None, time=W(), isleavingtime=W(), day=W(), month=W(),
                 returnTrip=W(), returnStartLocation=W(), returnEndLocation=W(), returnTime=W(),
                 returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_end_location(self):
        responses = ["Where would you like to go?", "what is your destination?", "And your end location?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

    # Doesn't matter if anything else is given/not, as long as the start & end location is received but the time is not
    @Rule(Ticket(departure=~L(None), arrival=~L(None), time=None, isleavingtime=W(), day=W(), month=W(),
                 returnTrip=W(), returnStartLocation=W(), returnEndLocation=W(), returnTime=W(),
                 returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_time(self):
        responses = ["What time would you want to leave?", "what time would be convenient for you",
                     "when would you like to leave by?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location and time is received
    # but the date is not
    @Rule(Ticket(departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=None, month=W(), returnTrip=W(), returnStartLocation=W(), returnEndLocation=W(), returnTime=W(),
                 returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_day(self):
        responses = ["What day would you want to leave?", "what day would be convenient for you"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time and day is received
    # but the month is not
    @Rule(Ticket(departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=None, returnTrip=W(), returnStartLocation=W(), returnEndLocation=W(),
                 returnTime=W(), returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_month(self):
        responses = ["What month would you want to leave?", "what month would be convenient for you"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time, day and month is received
    # i.e. all departure info but the return_trip is False, ask if they want a return ticket
    @Rule(Ticket(departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=~L(None), returnTrip=L(False), returnStartLocation=W(), returnEndLocation=W(),
                 returnTime=W(), returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_if_they_want_a_return_ticket(self):
        # convert date to dd/mm/yy
        self.brain["date"]["24hrs"] = format_date(self.brain["date"]["day"], self.brain["date"]["month"])

        responses = ["Got all your Information, but I see you dont have a return ticket. Would you like one?",
                     "I believe that's everything I need to book your trip, but you dont have a return ticket. Would "
                     "you like one?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

        text = input()
        res = check_y_n(text)
        if res:
            self.brain["return_trip"] = True
            self.brain["return_info"]["location"]["start_loc"] = self.brain["location"]["end_loc"]
            self.brain["return_info"]["location"]["end_loc"] = self.brain["location"]["start_loc"]
            self.declare(Ticket(departure="", arrival="", time="",
                                isleavingtime="",
                                day="", month="", returnTrip=True, returnStartLocation="",
                                returnEndLocation="", returnTime=None, returnIsLeavingTime="", returnDay="",
                                returnMonth=""))
        else:
            train_journey_dict = create_train_journey(self.brain)
            print_train_journey(train_journey_dict)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time, day and month is received
    # i.e. all departure info and the return_trip is True, along with the start location and end location but haven't
    # given a return time
    @Rule(Ticket(departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=~L(None), returnTrip=L(True), returnStartLocation=~L(None),
                 returnEndLocation=~L(None), returnTime=None, returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_a_return_time(self):
        responses = ["I've got both destination for you return ticket but i don't know the time you'd like to travel,"
                     "what time you will be travelling? ",
                     "what time would you like to catch the train?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time, day and month is received
    # i.e. all departure info and the return_trip is True, along with the start location, end location and time
    # but haven't given a return date (day)
    @Rule(Ticket(departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=~L(None), returnTrip=L(True), returnStartLocation=~L(None),
                 returnEndLocation=~L(None), returnTime=~L(None), returnIsLeavingTime=W(), returnDay=None,
                 returnMonth=W()))
    def ask_for_a_return_day(self):
        responses = [
            "I've almost got all your information. I just need the day you would be departing?",
            "what day you will be travelling? ",
            "what day would you like to catch the train?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time, day and month is received
    # i.e. all departure info and the return_trip is True, along with the start location, end location and time
    # but haven't given a return date (month)
    @Rule(Ticket(departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=~L(None), returnTrip=L(True), returnStartLocation=~L(None),
                 returnEndLocation=~L(None), returnTime=~L(None), returnIsLeavingTime=W(), returnDay=~L(None),
                 returnMonth=None))
    def ask_for_a_return_month(self):
        responses = [
            "I've almost got all your information. I just need the month you would be departing?",
            "what month you will be travelling? ",
            "And what month were you thinking?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print_bot_message(response)

    @Rule(Delay(startDest=None, endDest=W(), depTime=W(), arrTime=W(), delay=W()))
    def ask_for_delay_start_station(self):
        print_bot_message("What is your current Station?")
        txt = input().lower()
        txt = nlp(txt)
        res = process_location(self.delay_info, txt, "start_loc")
        if res["location"]["start_loc"] is None:
            print_bot_message("Sorry can you rephrase that?")
            self.declare(Delay(startDest=None, endDest=None, depTime=None, arrTime=None, delay=None))
        else:
            self.declare(Delay(startDest="", endDest=None, depTime=None, arrTime=None, delay=None))

    @Rule(Delay(startDest=~L(None), endDest=None, depTime=W(), arrTime=W(), delay=W()))
    def ask_for_delay_end_station(self):
        print_bot_message("What is your planned destination Station?")
        txt = input().lower()
        txt = nlp(txt)
        res = process_location(self.delay_info, txt, "end_loc")
        if res["location"]["end_loc"] is None:
            print_bot_message("Sorry can you rephrase that?")
            self.declare(Delay(startDest=None, endDest=None, depTime=None, arrTime=None, delay=None))
        else:
            self.declare(Delay(startDest="", endDest="", depTime=None, arrTime=None, delay=None))

    @Rule(Delay(startDest=~L(None), endDest=~L(None), depTime=None, arrTime=W(), delay=W()))
    def ask_for_delay_dep_time(self):
        print_bot_message("What was your scheduled departure time?")
        txt = input().lower()
        txt = nlp(txt)
        res = process_delay_time(txt)
        if res is False:
            print_bot_message("Sorry can you rephrase that?")
            self.declare(Delay(startDest="", endDest="", depTime=None, arrTime=None, delay=None))
        else:
            self.delay_info["og_dep_time"] = res
            self.declare(Delay(startDest="", endDest="", depTime="", arrTime=None, delay=None))

    @Rule(Delay(startDest=W(), endDest=W(), depTime=~L(None), arrTime=None, delay=W()))
    def ask_for_delay_arr_time(self):
        print_bot_message("What is your scheduled arrival time?")
        txt = input().lower()
        txt = nlp(txt)
        res = process_delay_time(txt)
        if res is False:
            print_bot_message("Sorry can you rephrase that?")
            self.declare(Delay(startDest="", endDest="", depTime="", arrTime=None, delay=None))
        else:
            self.delay_info["og_arr_time"] = res
            self.declare(Delay(startDest="", endDest="", depTime="", arrTime="", delay=None))

    @Rule(Delay(startDest=W(), endDest=W(), depTime=~L(None), arrTime=~L(None), delay=None))
    def ask_for_delay_delay(self):
        print_bot_message("How long of a delay has there been?")
        txt = input().lower()
        txt = nlp(txt)
        res = process_delay_delay(txt)
        if res is False:
            print_bot_message("Sorry can you rephrase that?")
            self.declare(Delay(startDest="", endDest="", depTime="", arrTime="", delay=None))
        else:
            self.delay_info["delay"] = res
            self.declare(Delay(startDest="", endDest="", depTime="", arrTime="", delay=""))

    @Rule(Delay(startDest=W(), endDest=W(), depTime=~L(None), arrTime=~L(None), delay=~L(None)))
    def got_all_delay_info(self):
        print_bot_message("Got all the information i need to make a prediction.")
        print_delay_info(self.delay_info)

# Convert minutes values to either 0, 15, 30 or 45 for web scraper
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

# Prints to the 'server.js' file as a 'botMessage' object, which is displayed on the UI
def print_bot_message(message):
    message_dict = {
        "type": "botMessage",
        "content": message
    }
    print(json.dumps(message_dict))

def create_train_journey(brain):
    train_journey_dict = {
        "single": {
            "depStation": brain["location"]["start_loc"],
            "arrStation": brain["location"]["end_loc"],
            "depDate": brain["date"]["24hrs"]
        }
    }

    ticket_hrs, ticket_mins = get_nearest_valid_mins(str(brain["time"]["time_value"]))

    if brain["time"]["is_leaving_time"]:
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

    if not(brain["return_trip"]):
        train_journey_dict["return"] = None
    else:
        train_journey_dict["return"] = {
            "depDate": format_date(brain["return_info"]["date"]["day"], brain["return_info"]["date"]["month"])
        }

        return_hrs, return_mins = get_nearest_valid_mins(brain["return_info"]["time"]["time_value"])

        if brain["return_info"]["time"]["is_leaving_time"]:
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

    return train_journey_dict

# Prints to the 'server.js' file as a 'trainJourney' object, which is used as an input for the web scraper
def print_train_journey(train_journey_dict):
    message_dict = {
        "type": "trainJourney",
        "content": {
            "single": train_journey_dict["single"],
            "return": train_journey_dict["return"]
        }
    }
    print(json.dumps(message_dict))

def print_delay_info(delay_info):
    message_dict = {
        "type": "delayInfo",
        "content": {
            "depStation": delay_info["location"]["start_loc"],
            "arrStation": delay_info["location"]["end_loc"],
            "ptd": delay_info["og_dep_time"],
            "pta": delay_info["og_arr_time"],
            "delay": delay_info["delay"]
        }
    }
    print(json.dumps(message_dict))

# Function to extract information using spaCy
def extract_info(text, complete, brain):
    result = {
        'location': {
            'start_loc': None,
            'end_loc': None
        },
        'time': {
            'time_value': None,
            'is_leaving_time': True
        },
        'date': {
            'day': None,
            'month': None
        },
        'intent': {
            'book': False,
            'predict': False
        },
        'return_trip': False,
        'return_info': {
            'location': {
                'start_loc': None,
                'end_loc': None
            },
            'time': {
                'time_value': None,
                'is_leaving_time': True
            },
            'date': {
                'day': None,
                'month': None
            }
        }
    }

    if brain["location"]["start_loc"] is None:
        start_or_end = "start_loc"
    elif brain["location"]["end_loc"] is None:
        start_or_end = "end_loc"
    elif brain["return_info"]["location"]["start_loc"] is None:
        start_or_end = "start_loc"
    elif brain["return_info"]["location"]["end_loc"] is None:
        start_or_end = "end_loc"
    else:
        start_or_end = ""

    if not complete:
        # Check sentence for return phrase and split it
        [departure_sentence, return_sentence] = split_sentence(text, brain)
        # Turn the text into nlp docs
        doc_departure_sentence = nlp(departure_sentence)
        doc_return_sentence = nlp(return_sentence)

        # Process the Departure info
        result = process_dep(result, doc_departure_sentence, start_or_end)
        # Process the Return info
        result = process_return(result, doc_return_sentence, start_or_end)
        # check return
        if check_return(brain):
            if result["location"]["end_loc"] is not None and result["location"]["start_loc"] is not None:
                brain["return_info"]["location"]["start_loc"] = result["location"]["end_loc"]
                brain["return_info"]["location"]["end_loc"] = result["location"]["start_loc"]
    else:
        # Turn the text into nlp docs
        doc_return_sentence = nlp(text)

        # Process the Return info
        result = process_return(result, doc_return_sentence, start_or_end)

    return result

def check_return(brain):
    return brain["return_trip"]

def get_user_input():
    return input().lower()


def check_for_delay(doc):
    for word in ["delay", "predict", "long"]:
        if word in doc:
            return True
        else:
            return False


def split_sentence(doc, brain):
    sentence = doc
    # Check for retuning phrase
    found_word = None
    for word in ["returning", "return", "back"]:
        if word in sentence:
            found_word = word
            brain["return_trip"] = True
            break

    if found_word:
        res = sentence.split(found_word)
    else:
        res = [sentence, '']

    return res


def process_dep(result, doc, start_or_end):
    # Location
    result = process_location(result, doc, start_or_end)

    # Time
    result = process_time(result, doc)

    # Date
    result = process_date(result, doc)

    return result


def process_return(result, doc, start_or_end):
    mini_result = result["return_info"]

    # Location
    mini_result = process_location(mini_result, doc, start_or_end)

    # Time
    mini_result = process_time(mini_result, doc)

    # Date
    mini_result = process_date(mini_result, doc)

    return result


def process_location(result, doc, start_or_end):
    # Initialize a list of all possible cities the Bot should be able to handle
    cities_rules = ["new york", "san francisco", "norwich", "london", "manchester", "birmingham", "bristol", "york",
                    "cambridge", "liverpool", "oxford", "newcastle", "brighton", "nottingham", "plymouth", "leeds",
                    "southampton", "sheffield", "exeter", "coventry", "hull", "portsmouth"]

    departure_prepositions = ["from"]
    arrival_prepositions = ["to", "in", "at"]

    # Create a City matcher object
    city_matcher = spacy.matcher.PhraseMatcher(nlp.vocab, attr="LOWER")
    pattern_city = [nlp(city) for city in cities_rules]
    city_matcher.add("CITIES", pattern_city)

    # Check to see if a city is found in the text
    city_matches = city_matcher(doc)

    # You found only one city
    if len(city_matches) == 1:
        for match_id, start, end in city_matches:
            result['location'][start_or_end] = str(doc[start:end])
    elif len(city_matches) > 0:
        # Find all the cities in the sentence, and append their prev word to the city name
        for match_id, start, end in city_matches:
            if str(doc[start - 1]) in departure_prepositions:
                result['location']['start_loc'] = str(doc[start:end])
            elif str(doc[start - 1]) in arrival_prepositions:
                result['location']['end_loc'] = str(doc[start:end])

    return result

def get_time_type(doc):
    # Create an arrival/departing detector
    time_type = spacy.matcher.PhraseMatcher(nlp.vocab, attr="LOWER")
    pattern_time_type = [nlp(phrase) for phrase in time_type_preposition]
    time_type.add("TIME_TYPE", pattern_time_type)

    # Check to see if a time_type preposition was found in the sentence
    type_matches = time_type(doc)

    # You find at least one preposition
    if len(type_matches) > 0:
        return False
    return True

def process_time(result, doc):
    # Regular expression pattern to match time in hh:mm format
    time_pattern = re.search(r'(\d{1,2}:\d{2})|(\d{1,2}\s?(AM|PM|am|pm))', doc.text)

    if time_pattern is not None:
        res = convert_to_24hr_format(time_pattern.group())
        result["time"]["time_value"] = res
        result["time"]["is_leaving_time"] = get_time_type(doc)


    return result


def convert_to_24hr_format(time_str):
    # print(time_str)
    # Define the regex pattern to capture different time formats
    pattern = r'(\d{1,2})(?::(\d{2}))?\s?(AM|PM|am|pm)?'

    # Extract hour, minute, and period from the time string
    match = re.match(pattern, time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)

        # Adjust hour based on period (AM/PM)
        if period and period.lower() == 'pm' and hour < 12:
            hour += 12
        elif period and period.lower() == 'am' and hour == 12:
            hour = 0

        # Return the time in 24-hour format
        return f"{hour:02d}:{minute:02d}"

    # Return None if the time string doesn't match any format
    return None

def format_date(day, month):
    current_year = datetime.datetime.now().year
    date = datetime.date(int(current_year), int(month), int(day))
    formatted_date = date.strftime("%d/%m/%y")
    return formatted_date
def process_delay_time(doc):
    # Regular expression pattern to match time in hh:mm format
    time_pattern = re.search(r'(\d{1,2}:\d{2})|(\d{1,2}\s?(AM|PM|am|pm))', doc.text)

    if time_pattern is not None:
        res = convert_to_24hr_format(time_pattern.group())
        return res
    else:
        return False

def process_delay_delay(doc):
    # Regular expression pattern to match time in hh:mm format
    time_pattern = re.search(r'\b(\d+)\b', doc.text)

    if time_pattern is not None:
        res = time_pattern.group()
        return res
    else:
        return False


def process_date(result, doc):
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]
    for ent in doc:
        # get the month
        if ent.text in months:
            result["date"]["month"] = months.index(ent.text) + 1
        # get the day
        elif re.match(r'\d+th', str(ent.text)):  # Look for the "th" in the sentence
            day = re.sub(r"th\b", "", str(ent.text))
            result["date"]["day"] = int(day)
        elif re.match(r'\d{1,2}/\d{1,2}', ent.text):  # Look for 12/06 pattern
            date_parts = ent.text.split('/')
            result["date"]["day"] = int(date_parts[0])
            result["date"]["month"] = months[int(date_parts[1]) - 1]
    return result


# Function to validate the date
def is_valid_date(day, month):
    current_date = datetime.date.today()
    try:
        input_date = datetime.date(current_date.year, month, day)
        return input_date >= current_date
    except ValueError:
        return False


def check_departing_info_complete(result):
    if (result['location']['start_loc'] is not None and result['location']['start_loc'] is not None
            and result['time']['time_value'] is not None and result["date"]["day"] is not None
            and result["date"]["month"] is not None):
        return True
    else:
        return False


def check_full_info_complete(result):
    # check departure
    if result["return_trip"]:
        if (result['location']['start_loc'] is not None
                and result['location']['start_loc'] is not None
                and result['time']['time_value'] is not None
                and result["date"]["day"] is not None
                and result["date"]["month"] is not None
                and result["return_info"]['location']['start_loc'] is not None
                and result["return_info"]['location']['end_loc'] is not None
                and result["return_info"]['time']['time_value'] is not None
                and result["return_info"]['date']['day'] is not None
                and result["return_info"]['date']['month'] is not None):
            return True
        else:
            return False
    else:
        if (result['location']['start_loc'] is not None
                and result['location']['start_loc'] is not None
                and result['time']['time_value'] is not None
                and result["date"]["day"] is not None
                and result["date"]["month"] is not None):
            return True
        else:
            return False


# Function to update the final json brain
def update_json(json_var, json_var_):
    for key, value in json_var_.items():
        if value is not None and value is not False:
            if isinstance(value, dict):
                update_json(json_var[key], value)  # Recursively update the nested dictionary
            else:
                json_var[key] = value
    return json_var


def check_y_n(text):
    # Positive words
    positive_words = ["y", "yes", "yeah", "yup", "sure", "absolutely", "definitely",
                      "certainly", "of course", "okay", "ok", "all right", "fine", "great",
                      "excellent", "fantastic", "wonderful", "awesome", "gladly", "no problem", "like to"]
    # Negative words
    negative_words = ["n", 'no', 'nah', 'nope', 'not really', 'sorry', "i'm good", "im good", "don't", "dont"]

    # Construct regular expression pattern to search for
    pos_pattern = "|".join(["\\b{}\\b".format(word) for word in positive_words])
    neg_pattern = "|".join(["\\b{}\\b".format(word) for word in negative_words])

    # Search for the pattern in the sentence
    match_pos = re.search(pos_pattern, text)
    match_neg = re.search(neg_pattern, text)

    # Check for negative words first cuz of cases like "nah I'm all right"
    if match_neg:
        return False
    elif match_pos:
        return True


# Function to handle user input and chat with the bot
def chat_with_bot():
    bot = TravelBot()
    bot.reset()
    brain = bot.brain
    delay_info = bot.delay_info
    bot.run()  # Run before asking for input just to Greet the user and say the Chatbot's functionality
    # Determine if they want to make a prediction or booking

    while True:
        user_input = get_user_input()
        # Check if sentence is for predicting delays
        delay = check_for_delay(user_input)
        # if sentence is not for delay then assume it's for booking
        if not delay:
            # check to see the departure and return ticket has fully been completed
            if not check_full_info_complete(brain):
                # check to see the departure ticket has been completed
                if not check_departing_info_complete(brain):
                    # 'False' indicates the departure is not complete
                    data = extract_info(user_input, False, brain)
                else:
                    # 'True' indicates the departure is complete
                    data = extract_info(user_input, True, brain)

                # Update the parameters in the brain
                brain = update_json(brain, data)

            # indicates that we are done Booking, we should ask the user if they want to predict anything now
            else:
                train_journey_dict = create_train_journey(brain)
                print_train_journey(train_journey_dict)
                break

            # print(data)
            # print(brain)

            # if not is_valid_date(data['date']['day'], data['date']['month']):
            #     print("Invalid date. Please provide a valid date.")
            #     continue

            bot.declare(Ticket(departure=brain['location']['start_loc'],
                               arrival=brain['location']['end_loc'], time=brain['time']['time_value'],
                               isleavingtime=brain['time']['is_leaving_time'], day=brain["date"]["day"],
                               month=brain["date"]["month"],
                               returnTrip=brain["return_trip"],
                               returnStartLocation=brain["return_info"]['location']['start_loc'],
                               returnEndLocation=brain["return_info"]['location']['end_loc'],
                               returnTime=brain["return_info"]['time']['time_value'],
                               returnIsLeavingTime=brain["return_info"]['time']['is_leaving_time'],
                               returnDay=brain["return_info"]['date']['day'],
                               returnMonth=brain["return_info"]['date']['month'],
                               )
                        )

        # Sentence is for Delay predictions
        else:

            print(delay_info)
            bot.declare(Delay(
                startDest=delay_info["location"]["start_loc"],
                endDest=delay_info["location"]["end_loc"],
                depTime=delay_info["og_dep_time"],
                arrTime=delay_info["og_arr_time"],
                delay=delay_info["delay"]
            ))

        bot.run()


if __name__ == "__main__":
    # Start the chat
    chat_with_bot()

# i would like to book a ticket from london to liverpool on the 5th of may by 7pm and return from liverpool to london on the 6th of may by 8pm

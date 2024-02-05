import spacy
from experta import *
import random
import re
import datetime

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
    def __int__(self, greeting, departure, arrival, time, isleavingtime, day, month, returnTrip,
                returnStartLocation, returnEndLocation, returnTime, returnIsLeavingTime, returnDay, returnMonth):
        self.greeting = greeting
        self.departure = departure
        self.arrival = arrival
        self.time = time
        self.isleavingtime = isleavingtime
        self.day = day
        self.month = month
        self.returnTrip = returnTrip
        self.returnStartLocation = returnStartLocation
        self.returnEndLocation = returnEndLocation
        self.returnTime = returnTime
        self.returnIsLeavingTime = returnIsLeavingTime
        self.returnDay = returnDay
        self.returnMonth = returnMonth


class Greeting(Fact):
    pass


# Define Expert System rules
class TravelBot(KnowledgeEngine):
    @DefFacts()
    def _initial_action(self):
        yield Greeting()

    # @Rule(Greeting())
    # def greet(self):
    #     responses = ["Hello!", "Hi there!", "Hey, how can I help you?"]
    #     response = responses[random.randint(0, len(responses) - 1)]
    #     print(response)

    # Doesn't matter if anything else is given/not, as long as start location is received but the end location is not
    @Rule(Ticket(greeting=W(), departure=None, arrival=W(), time=W(), isleavingtime=W(), day=W(), month=W(),
                 return_trip=W(),
                 returnStartLocation=W(), returnEndLocation=W(), returnTime=W(), returnIsLeavingTime=W(), returnDay=W(),
                 returnMonth=W()))
    def ask_for_start_location(self):
        responses = ["What station would you be leaving from?", "Where would you be traveling from?",
                     "What the start Location?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print(response)

    # Doesn't matter if anything else is given/not, as long as start location is not received
    @Rule(Ticket(greeting=W(), departure=~L(None), arrival=None, time=W(), isleavingtime=W(), day=W(), month=W(),
                 return_trip=W(), returnStartLocation=W(), returnEndLocation=W(), returnTime=W(),
                 returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_end_location(self):
        responses = ["Where would you like to go?", "what is your destination?", "And your end location?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print(response)

    # Doesn't matter if anything else is given/not, as long as the start & end location is received but the time is not
    @Rule(Ticket(greeting=W(), departure=~L(None), arrival=~L(None), time=None, isleavingtime=W(), day=W(), month=W(),
                 return_trip=W(), returnStartLocation=W(), returnEndLocation=W(), returnTime=W(),
                 returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_time(self):
        responses = ["What time would you want to leave?", "what time would be convenient for you",
                     "when would you like to leave by?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location and time is received
    # but the date is not
    @Rule(Ticket(greeting=W(), departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=None, month=W(), return_trip=W(), returnStartLocation=W(), returnEndLocation=W(), returnTime=W(),
                 returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_day(self):
        responses = ["What day would you want to leave?", "what day would be convenient for you"]
        response = responses[random.randint(0, len(responses) - 1)]
        print(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time and day is received
    # but the month is not
    @Rule(Ticket(greeting=W(), departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=None, return_trip=W(), returnStartLocation=W(), returnEndLocation=W(),
                 returnTime=W(), returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_month(self):
        responses = ["What month would you want to leave?", "what month would be convenient for you"]
        response = responses[random.randint(0, len(responses) - 1)]
        print(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time, day and month is received
    # i.e. all departure info but the return_trip is False, ask if they want a return ticket
    @Rule(Ticket(greeting=W(), departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=~L(None), returnTrip=L(False), returnStartLocation=W(), returnEndLocation=W(),
                 returnTime=W(), returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_if_they_want_a_return_ticket(self):
        responses = ["Got all your Information, but I see you dont have a return ticket. Would you like one?",
                     "I believe that's everything I need to book your trip, but you dont have a return ticket. Would "
                     "you like one?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time, day and month is received
    # i.e. all departure info and the return_trip is True, but haven't given a start station
    @Rule(Ticket(greeting=W(), departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=~L(None), returnTrip=L(True), returnStartLocation=L(None), returnEndLocation=W(),
                 returnTime=W(), returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_a_return_start_location(self):
        responses = ["I see you want a return ticket but I don't know where you will be departing from? ",
                     "what station would you be returning from?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print(response)

    # Doesn't matter if anything else is given/not, as long as the start, end location, time, day and month is received
    # i.e. all departure info and the return_trip is True, along with the start location but haven't given an
    # end station
    @Rule(Ticket(greeting=W(), departure=~L(None), arrival=~L(None), time=~L(None), isleavingtime=W(),
                 day=~L(None), month=~L(None), returnTrip=L(True), returnStartLocation=~L(None),
                 returnEndLocation=None, returnTime=W(), returnIsLeavingTime=W(), returnDay=W(), returnMonth=W()))
    def ask_for_a_return_end_location(self):
        responses = ["I've got the start destination for you return ticket but i dont have the end destination,"
                     "where you will be returning to? ",
                     "what station would you be returning to?"]
        response = responses[random.randint(0, len(responses) - 1)]
        print(response)


# Function to extract information using spaCy
def extract_info(text, brain):
    result = {
        'greeting': False,
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

    # # Greetings
    # if greeting_regex.search(str(doc)):
    #     result["greeting"] = True

    if not check_departing_info_complete(brain):
        # Check sentence for return phrase and split it
        [departure_sentence, return_sentence] = split_sentence(text, result)
        # Turn the text into nlp docs
        doc_departure_sentence = nlp(departure_sentence)
        doc_return_sentence = nlp(return_sentence)

        # Process the Departure info
        result = process_dep(result, doc_departure_sentence)
        # Process the Return info
        result = process_return(result, doc_return_sentence)
    else:
        # Turn the text into nlp docs
        doc_return_sentence = nlp(text)
        # Process the Return info
        result = process_return(result, doc_return_sentence)

    # # Intent
    # for ent in doc:
    #     if ent.text in ["travel", "travels", "book", "booking", "bookings", "ticket"]:
    #         result["intent"]["book"] = True

    return result


def get_user_input():
    return input(">")


def split_sentence(doc, result):
    sentence = doc
    found_word = None
    for word in ["returning", "return", "back"]:
        if word in sentence:
            found_word = word
            result["return_trip"] = True
            break

    if found_word:
        res = sentence.split(found_word)
    else:
        res = [sentence, '']

    return res


def process_dep(result, doc):
    # Location
    result = process_location(result, doc)

    # Time
    result = process_time(result, doc)

    # Date
    result = process_date(result, doc)

    return result


def process_return(result, doc):
    mini_result = result["return_info"]

    # Location
    mini_result = process_location(mini_result, doc)

    # Time
    mini_result = process_time(mini_result, doc)

    # Date
    mini_result = process_date(mini_result, doc)

    return result


# Function to proces location
def process_location(result, doc):
    for ent in doc:
        if ent.ent_type_ == "GPE":
            ans_list = []
            for ancestor in ent.ancestors:
                ans_list.append(ancestor.text)
            if any("from" in word for word in ans_list):  # Change hard coding of "from" to more departure prepositions
                result['location']['start_loc'] = ent.text
            elif any("to" in word for word in ans_list):  # Change hard coding of "to" to more arrival prepositions
                result['location']['end_loc'] = ent.text
    return result


def process_time(result, doc):
    for ent in doc:
        if ent.ent_type_ == "TIME" and ent.like_num:
            ans_list = []
            for ancestor in ent.ancestors:
                ans_list.append(ancestor.text)
            if any(time == word for word in ans_list for time in time_type_preposition):
                result["time"]["time_value"] = int(ent.text)
                result["time"]["is_leaving_time"] = False
            else:
                result["time"]["time_value"] = int(ent.text)
                result["time"]["is_leaving_time"] = True
    return result


def process_date(result, doc):
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]
    for ent in doc:
        # get the month
        if ent.text in months:
            result["date"]["month"] = ent.text
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


# Function to update the final json brain
def update_json(json_var, json_var_):
    for key, value in json_var_.items():
        if value is not None and value is not False:
            if isinstance(value, dict):
                update_json(json_var[key], value)  # Recursively update the nested dictionary
            else:
                json_var[key] = value
    return json_var


# Function to handle user input and chat with the bot
def chat_with_bot():
    print("creating new memory")
    brain = {
        'greeting': False,
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
    bot = TravelBot()
    bot.reset()
    while True:
        user_input = get_user_input()
        data = extract_info(user_input, brain)

        brain = update_json(brain, data)

        # print(data)
        print(brain)

        # if not is_valid_date(data['date']['day'], data['date']['month']):
        #     print("Invalid date. Please provide a valid date.")
        #     continue

        bot.declare(Ticket(greeting=brain['greeting'], departure=brain['location']['start_loc'],
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

        bot.run()

        bot.reset()


if __name__ == "__main__":
    # Start the chat
    chat_with_bot()

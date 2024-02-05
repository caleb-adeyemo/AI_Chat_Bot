CREATE TYPE sender AS ENUM ('user', 'chatbot');
CREATE TABLE threads
(
	thread_id SERIAL PRIMARY KEY
);

CREATE TABLE messages 
(
	msg_id SERIAL PRIMARY KEY,
	thread_id INT NOT NULL,
	msg_sender SENDER NOT NULL,
	content TEXT,
	CONSTRAINT fk_thread
		FOREIGN KEY(thread_id)
			REFERENCES threads(thread_id)
);

CREATE TABLE stations
(
	name TEXT NOT NULL,
	alias TEXT,
	alpha3 TEXT,
	tiploc VARCHAR(3) UNIQUE NOT NULL,
	tpl TEXT PRIMARY KEY	
);

COPY stations(name, alias, alpha3, tiploc, tpl)
FROM 'C:\Users\mawun\OneDrive\Documents\University\Computing Science\Year 3\Artificial Intelligence\Summative Assessments\Coursework 2\data\stations.csv'
DELIMITER ','
CSV HEADER;

SELECT * FROM messages;

SELECT * FROM threads;

SELECT * FROM stations;

DROP TABLE stations;

INSERT INTO threads(thread_id) VALUES (DEFAULT);

INSERT INTO messages(thread_id, msg_sender, content)
VALUES (1, 'user', 'Hi Chatbot!'),
	   (1, 'chatbot', 'Hi User!'),
	   (2, 'user', 'Second Thread Ey?'),
	   (2, 'chatbot', 'Yes indeed human');

INSERT INTO messages(thread_id, msg_sender, content)
VALUES (1, 'chatbot', 'Hi User!');

DELETE FROM threads;

DELETE FROM messages CASCADE;

ALTER SEQUENCE threads_thread_id_seq RESTART WITH 1;

ALTER SEQUENCE messages_msg_id_seq RESTART WITH 1;
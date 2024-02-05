# artificial-intelligence-group-4
Artificial Intelligence Coursework 2 for Group 4

Change:
```
class frozendict(collections.Mapping)
```

to

```
class frozendict(collections.abc.Mapping)
```

in venv\\Lib\\site-packages\\frozendict\\\_\_init\_\_.py

Then install:
```
python -m spacy download en
```
in venv terminal.

To open venv terminal, write:
```
venv/Scripts/activate
```
and to close type:
```
deactivate
```

To setup the database, download pgAdmin and PostgreSQL, create a new database and in the .env file, fill out the following details:
```
PGHOST=<YOUR_HOST_NAME>
PGUSER=<YOUR_USERNAME>
PGPASSWORD=<YOUR_PASSWORD>
PGDATABASE=<YOUR_DATABASE_NAME>
PGPORT=<YOUR_PORT_NUMBER>
```

Then in your created database, add the following tables:

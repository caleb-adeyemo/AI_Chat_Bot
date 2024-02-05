const getTickets = require('./railwayScraperTest.js');

const trainJourneyObj = {
  "depStation": "Norwich",
  "arrStation": "Romford",
  "depDate": "10/05/2023",
  "depTimHrs": "12",
  "depTimMins": "0"
}

getTickets(trainJourneyObj);

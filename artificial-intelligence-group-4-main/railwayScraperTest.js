// Packages for Puppeteer
const bodyParser = require('body-parser');
const puppeteer = require('puppeteer');

const ticketInfoToString = (ticket, date, type) =>
{
  return `${type === 'single' ? 'Single' : 'Return'} Ticket
Departure Date: ${date}
Departure Station: ${ticket['jsonJourneyBreakdown']['departureStationName']}
Arrival Station:  ${ticket['jsonJourneyBreakdown']['arrivalStationName']}
Departure Time: ${ticket['jsonJourneyBreakdown']['departureTime']}
Arrival Time: ${ticket['jsonJourneyBreakdown']['arrivalTime']}
Price: £${ticket['singleJsonFareBreakdowns'][0]['fullFarePrice'].toFixed(2)}`;
};

const ticketInfoToHTMLString = (ticket, date, type) =>
{
  return `${type === 'single' ? 'Single' : 'Return'} Ticket<br>
Departure Date: ${date}<br>
Departure Station: ${ticket['jsonJourneyBreakdown']['departureStationName']}<br>
Arrival Station:  ${ticket['jsonJourneyBreakdown']['arrivalStationName']}<br>
Departure Time: ${ticket['jsonJourneyBreakdown']['departureTime']}<br>
Arrival Time: ${ticket['jsonJourneyBreakdown']['arrivalTime']}<br>
Price: £${ticket['singleJsonFareBreakdowns'][0]['fullFarePrice'].toFixed(2)}`;
};

const getMonthString = month =>
{
  switch(parseInt(month))
  {
    case 1:
      return 'Jan';
    case 2:
      return 'Feb';
    case 3:
      return 'Mar';
    case 4:
      return 'Apr';
    case 5:
      return 'May';
    case 6:
      return 'Jun';
    case 7:
      return 'Jul';
    case 8:
      return 'Aug';
    case 9:
      return 'Sep';
    case 10:
      return 'Oct';
    case 11:
      return 'Nov';
    case 12:
      return 'Dec';
  }
  return null;
}

const changeDateFormat = date =>
{
  const dateArr = date.split('/');
  console.log(dateArr);
  dateArr[1] = getMonthString(dateArr[1]);
  console.log(dateArr);
  const newDate = dateArr.join(' ');
  console.log(newDate);
  return newDate;
}

/* Train Ticket Object:
{
  single: {
            depStation,
            arrStation,
            depDate,
            depTimHrs,
            depTimMins,
            arrTimHrs,
            arrTimMins
          },
  return: {
            depDate,
            depTimHrs,
            depTimMins,
            arrTimHrs,
            arrTimMins
          }
} */

async function getTickets(trainObj, ticketNo)
{
  try
  {
    // args: ["--disable-setuid-sandbox"],
    console.log('Opening the browser.');
    // const browser = await puppeteer.launch({    // Create browser interface
    //   headless: false,
    //   args: ['--headless']
	  //   // 'ignoreHTTPSErrors': true
    // });
    const browser = await puppeteer.launch(
      {
        headless: false,
        args: ['--headless'],
        'ignoreHTTPSErrors': true
      });
    const puppeteerFeedPath = './puppeteerFeed/';
    console.log('Browser opened.');
    const page = await browser.newPage();   // Create new page in browser interface

    await page.goto('https://ojp.nationalrail.co.uk/service/planjourney/search',
      { waitUntil:['load', 'domcontentloaded'] });   // Go to National Rail website
    // await page.goto('https://www.nationalrail.co.uk/');   // Go to National Rail website
    console.log('Gone to National Rail website.');

    await page.screenshot({path: `${puppeteerFeedPath}web_scrape_sc1.png`});   // Take screenshot of current view
    console.log('First screenshot taken.');

    // Wait for cookie popup to appear
    await page.waitForSelector('#onetrust-accept-btn-handler',
      { visible: true });
    // Remove cookie popup from view
    await page.evaluate(() => document.querySelector('#onetrust-accept-btn-handler').click());
    await page.waitForTimeout(1200);
    console.log('Cookie popup removed.');

    await page.screenshot({path: `${puppeteerFeedPath}web_scrape_sc2.png`});   // Take screenshot of current view
    console.log('Second screenshot taken.');

    await page.evaluate(depStation => document.querySelector('#txtFrom').value = depStation, trainObj.single.depStation);
    await page.evaluate(arrStation => document.querySelector('#txtTo').value = arrStation, trainObj.single.arrStation);
    await page.evaluate(depDate => document.querySelector('#txtDate').value = depDate, trainObj.single.depDate);

    // If user wants to either depart at a certain time or arrive by a certain time
    if (trainObj.single.depTimHrs !== null)
    {
      console.log('Single Departing Time Entered');
      await page.evaluate(depTimHrs => document.querySelector('#sltHours').value = depTimHrs, trainObj.single.depTimHrs);
      await page.evaluate(depTimMins => document.querySelector('#sltMins').value = depTimMins, trainObj.single.depTimMins.padStart(2, '0'));
    }
    else
    {
      console.log('Single Arriving Time Entered');
      await page.evaluate(() => document.querySelector('#sltArr').value = 'ARRIVE');
      await page.evaluate(arrTimHrs => document.querySelector('#sltHours').value = arrTimHrs, trainObj.single.arrTimHrs);
      await page.evaluate(arrTimMins => document.querySelector('#sltMins').value = arrTimMins, trainObj.single.arrTimMins.padStart(2, '0'));
    }

    if (trainObj.return !== null)
    {
      console.log('Return not null');
      await page.evaluate(() => document.querySelector('#ret-ch').click());
      await page.waitForTimeout(2000);
      await page.evaluate(depDate => document.querySelector('#txtDateRet').value = depDate, trainObj.return.depDate);

      if (trainObj.return.depTimHrs !== null)
      {
        console.log('Return Departing Time Entered');
        await page.evaluate(depTimHrs => document.querySelector('#sltHoursRet').value = depTimHrs, trainObj.return.depTimHrs);
        await page.evaluate(depTimMins => document.querySelector('#sltMinsRet').value = depTimMins, trainObj.return.depTimMins.padStart(2, '0'));
      }
      else
      {
        console.log('Return Arriving Time Entered');
        await page.evaluate(() => document.querySelector('#sltArrRet').value = 'ARRIVE');
        await page.evaluate(arrTimHrs => document.querySelector('#sltHoursRet').value = arrTimHrs, trainObj.return.arrTimHrs);
        await page.evaluate(arrTimMins => document.querySelector('#sltMinsRet').value = arrTimMins, trainObj.return.arrTimMins.padStart(2, '0'));
      }
    }
    else
    {
      console.log('Return is null');
    }

    console.log('Filled out form input fields.');
    await page.screenshot({path: `${puppeteerFeedPath}web_scrape_sc3.png`});
    console.log('Third screenshot taken.');

    // Find and click submit button
    const submitButton = await page.evaluateHandle(
      text => [...document.querySelectorAll('button')].find(a => a.innerText === text),
      'Go'
    );

    await submitButton.click();
    console.log('Submit button clicked.');
    await page.waitForTimeout(2000);
    const url2 = await page.url();

    console.log(`Current URL: ${url2}`);

    await page.screenshot({path: `${puppeteerFeedPath}web_scrape_sc4.png`});
    console.log('Fourth screenshot taken.');

    // await page.waitForSelector('#fsrFocusFirst',
    //   { visible: true });
    // await page.evaluate(() => document.querySelector('#fsrFocusFirst').click());

    await page.screenshot({path: `${puppeteerFeedPath}web_scrape_sc5.png`});
    console.log('Fifth screenshot taken.');


    const singleTickets = [];
    const returnTickets = [];

    for (let i = 1; i < 11; i++)
    {
      if (trainObj.return == null && i > 5)
      {
        break;
      }

      const ticketNode = await page.$(`#jsonJourney-4-${i}`);
      const ticketStr = await ticketNode.evaluate(el => el.textContent);
      const ticketJson = JSON.parse(ticketStr);

      if (i < 6)
      {
        singleTickets.push(ticketJson);
      }
      else
      {
        returnTickets.push(ticketJson);
      }
    }

    console.log('Single Tickets:\n');
    for (let i = 0; i < singleTickets.length; i++)
    {
      console.log(ticketInfoToString(singleTickets[i], trainObj.single.depDate,'single')+'\n');
    }

    if (trainObj.return !== null)
    {
      console.log('Return Tickets:\n')
      for (let i = 0; i < returnTickets.length; i++)
      {
        console.log(ticketInfoToString(returnTickets[i], trainObj.return.depDate, 'return')+'\n');
      }
    }

    let cheapestTickets = [];
    let cheapestTicketUrl = '';
    let cheapestTicketPrice = 0;

    try
    {
      const cheapestTicketNodes = await page.$$('.has-cheapest');
      // console.log(`cheapestTicketNodes length: ${cheapestTicketNodes.length}`);
      await page.waitForTimeout(500);

      for (let i = 0; i < cheapestTicketNodes.length; i++)
      {
        const cheapestTicketStr = await cheapestTicketNodes[i].evaluate(el => el.children[0].textContent.trim());
        const cheapestTicketJson = JSON.parse(cheapestTicketStr);
        cheapestTicketPrice += cheapestTicketJson['singleJsonFareBreakdowns'][0]['fullFarePrice'];

        if (i == 0)
        {
          cheapestTickets.push(ticketInfoToHTMLString(cheapestTicketJson, trainObj.single.depDate, 'single'));
          console.log(`Cheapest Single Ticket:\n${ticketInfoToString(cheapestTicketJson, trainObj.single.depDate, 'single')}\n`);
        }
        else
        {
          cheapestTickets.push(ticketInfoToHTMLString(cheapestTicketJson, trainObj.return.depDate, 'return'));
          console.log(`Cheapest Return Ticket:\n${ticketInfoToString(cheapestTicketJson, trainObj.return.depDate, 'return')}\n`);
        }
      }

      cheapestTicketUrl = await page.url();
      // await page.evaluate(() => document.querySelector('#buyCheapestButton').click());
      // await page.waitForTimeout(2000);

      console.log(`Cheapest Ticket URL: ${cheapestTicketUrl}`);
    }
    catch (err)
    {
      console.log(`Get cheapest tickets error: ${err.message}`);
      cheapestTickets = null;
      cheapestTicketsUrl = null;
      cheapestTicketPrice = null;
    }

    await browser.close();

    return [cheapestTickets, cheapestTicketUrl, cheapestTicketPrice];
  }
  catch (err)
  {
    console.log(`Unable to create browser: ${err.message}`);
    return [null, null, null];
  }
}

// const trainJourneyObj = {
//   "single": {
//     "depStation": "Norwich",
//     "arrStation": "Romford",
//     "depDate": "25/07/2023",
//     "depTimHrs": null,
//     "depTimMins": null,
//     "arrTimHrs": "12",
//     "arrTimMins": "0"
//   },
//   "return": null
// }

const trainJourneyObj = {
  "single": {
    "depStation": "Norwich",
    "arrStation": "Romford",
    "depDate": "25/07/2023",
    "depTimHrs": null,
    "depTimMins": null,
    "arrTimHrs": "12",
    "arrTimMins": "0"
  },
  "return": {
    "depDate": "27/07/2023",
    "depTimHrs": "14",
    "depTimMins": "30",
    "arrTimHrs": null,
    "arrTimMins": null
  }
}

// getTickets(trainJourneyObj);
// console.log(changeDateFormat(trainJourneyObj['single']['depDate']));

module.exports = {ticketInfoToString, getTickets};

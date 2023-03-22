import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

import QuantLib as ql

## -----
##
##  Function to calculate penalty interest
##
##  Author: Daniel Jakobsson
##
##  Example: Penalty_Interest_Amount = calculatePenalty(100, datetime(2022,1,20), datetime(2023,1,5)) 
##
## -----

Amount = 1000
startDate = datetime(2022,1,20)
endDate = datetime(2023,1,5)

Penalty_Interest_Amount = calculatePenalty(Amount, startDate, endDate)

print( Penalty_Interest_Amount )



# Create yearly date range
def dateRange(startDate, endDate):
  
  # Initialize an empty dataframe
  result = pd.DataFrame()
  
  # Loop through the range of dates and append to the list
  while startDate <= endDate:

    df = pd.DataFrame( {
        'FromDate': [startDate],
        'ToDate': [startDate + relativedelta(years=1)]
    })


    result = pd.concat((result,df), axis=0)

    startDate += relativedelta(years=1)

  # Reset index
  result.reset_index(drop=True, inplace=True)

  # adjust dates
  result.at[result.index[-1], 'ToDate'] = endDate

  return result


# Convert to quantlib dateformat
def convertDate(date):
  return ql.Date(date.strftime('%Y-%m-%d'), '%Y-%m-%d')

# Calculate year fraction
def yearFrac(startDate, endDate):
  return ql.Thirty360(ql.Thirty360.European).yearFraction(startDate, endDate)

def getPenaltyRates(startDate, endDate):

  # Get rates from CBI
  path = 'https://www.sedlabanki.is/xmltimeseries/Default.aspx?DagsFra=1900-01-01&DagsTil=2200-01-01&TimeSeriesID=22&Type=xml'

  # Convert xml data to dataframe
  df = pd.read_xml(path, xpath=".//Entry")

  # Convert string column to datetime
  df['Date'] =  pd.to_datetime(df['Date'])

  # Change date value to first date of the month
  startDate = startDate.replace(day=1)
  endDate = endDate.replace(day=1)

  # Filter DateFrame
  df = df.query("Date >= @startDate & Date <= @endDate")

  # Reset index
  df.reset_index(drop=True, inplace=True)

  return df

# Calculate simple penalty interest - that is, without yearly compounding
def calculateSimplePenalty(Amount, startDate, endDate):

  # Get penalty rates for given time period
  df = getPenaltyRates(startDate, endDate)

  # Adjust dates 
  df['FromDate'] = df['Date']
  df['ToDate'] = df.Date.shift(-1)

  df.at[0, 'FromDate'] = startDate
  df.at[df.index[-1], 'ToDate'] = endDate


  # Convert to quantlib dateformat
  df['QLFromDate'] = df['FromDate'].apply(convertDate)
  df['QLToDate'] = df['ToDate'].apply(convertDate)

  # Calculate year fraction
  df['yearFrac'] = df.apply(lambda x: yearFrac(x.QLFromDate, x.QLToDate), axis=1)

  # Calculate interest amount
  df['InterestAmount'] = Amount * df['Value'] / 100 * df['yearFrac']

  InterestAmount = df['InterestAmount'].sum()

  return InterestAmount


# Calculate penalty interest with yearly compounding
def calculatePenalty(Amount, startDate, endDate):

  df = dateRange(startDate, endDate)

  InterestAmount = 0
  for x in df.index:
    startDate = df.iloc[x]['FromDate']
    endDate = df.iloc[x]['ToDate']


    InterestAmount += calculateSimplePenalty(Amount + InterestAmount, startDate, endDate)

  return InterestAmount

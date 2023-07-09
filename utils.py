import datetime
from dateutil.relativedelta import relativedelta


def get_past_date(str_days_ago:str):
    """gets the date object based on past date string object

    Args:
        str_days_ago (str): string containing date info (Eg: 30 Days Ago, Yesterday)

    Returns:
        Date: date
    """
    today_date = datetime.date.today()
    splitted = str_days_ago.split()
    if len(splitted) == 1 and splitted[0].lower() == 'today':
        return today_date
    elif len(splitted) == 1 and splitted[0].lower() == 'yesterday':
        date = today_date - relativedelta(days=1)
        return date
    elif splitted[1].lower() in ['hour', 'hours', 'hr', 'hrs', 'h']:
        date = datetime.datetime.now() - relativedelta(hours=int(splitted[0]))
        return date
    elif splitted[1].lower() in ['day', 'days', 'd']:
        date = today_date - relativedelta(days=int(splitted[0]))
        return date
    elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
        date = today_date - relativedelta(weeks=int(splitted[0]))
        return date
    elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
        date = today_date - relativedelta(months=int(splitted[0]))
        return date
    elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
        date = today_date - relativedelta(years=int(splitted[0]))
        return date
    else:
        return None

from datetime import datetime
import json
from typing import Dict
from dotenv import load_dotenv
import logging
import csv
import requests
import os
import traceback

from constants import COMPANY_NAMES_CSV, \
    COMPANY_SEARCH_API_HEADER_CSV, \
    COMPANY_KEYWORDS_CSV, COMPANY_SEARCH_API_CSV, \
    COMPANY_STATUS_CSV, COMPANY_SEARCH_API_EXTRA_HEADER_CSV,\
    COMPANY_KNOWN_JOBS_CSV, LOG_FILE_LOCATION,\
    SLACK_DEPLOYMENT_NOTIFICATION_WEBHOOK_VAR,\
    SLACK_ERROR_NOTIFICATION_WEBHOOK_VAR,\
    SLACK_JOB_NOTIFICATION_WEBHOOK_VAR,\
    LOG_FOLDER_LOCATION
from job_checker import get_relevant_jobs


def get_company_data():
    company_info = {}
    # Get company names and their IDs
    with open(COMPANY_NAMES_CSV, newline='') as company_name_csvfile:
        reader = csv.DictReader(company_name_csvfile)
        for row in reader:
            company_info[row['CompanyID']] = {
                'CompanyName': row['CompanyName'],
                'CompanyPortal': row['CompanyPortal']}
    # Get company related keywords
    with open(COMPANY_KEYWORDS_CSV, newline='') as company_keywords_csvfile:
        reader = csv.DictReader(company_keywords_csvfile)
        for row in reader:
            company_info[row['CompanyID']].update({
                'Keywords': row['Keywords'].split('|')})
    # Get company search APIs
    with open(COMPANY_SEARCH_API_CSV, newline='') as company_search_api_csvfile:
        csv_reader = csv.reader(company_search_api_csvfile, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
                continue
            company_info[row[0]].update({
                'SearchAPI': row[2], 'SearchType': row[1]})
    # Get company search API headers
    with open(COMPANY_SEARCH_API_HEADER_CSV, newline='') as company_header_csvfile:
        reader = csv.DictReader(company_header_csvfile, delimiter='|')
        for row in reader:
            if row['SearchHeader'] == "":
                company_info[row['CompanyID']].update({
                    'SearchHeader': row['SearchHeader']})
            else:
                company_info[row['CompanyID']].update({
                    'SearchHeader': json.loads(row['SearchHeader'])})
    # Get company search API extra headers
    with open(COMPANY_SEARCH_API_EXTRA_HEADER_CSV, newline='') as company_extra_header_csvfile:
        reader = csv.DictReader(company_extra_header_csvfile, delimiter='|')
        for row in reader:
            if row['SearchExtraHeader'] == "":
                company_info[row['CompanyID']].update({
                    'SearchExtraHeader': row['SearchExtraHeader']})
            else:
                company_info[row['CompanyID']].update({
                    'SearchExtraHeader': json.loads(row['SearchExtraHeader'])})
    # Get company known jobs
    with open(COMPANY_KNOWN_JOBS_CSV, newline='') as company_known_csvfile:
        reader = csv.DictReader(company_known_csvfile)
        for row in reader:
            company_info[row['CompanyID']].update(
                {'KnownJobs': row['KnownJobs']})
    # Get monitored company status
    with open(COMPANY_STATUS_CSV, newline='') as company_status_csvfile:
        reader = csv.DictReader(company_status_csvfile)
        for row in reader:
            company_info[row['CompanyID']].update(
                {'MonitorStatus': row['MonitorStatus']})
    return company_info


def send_deployment_notification_to_user(notification_type: str,
                                         notification_message: str, session):
    """sends the deployment notification to user

    Args:
        notification_type (str): notification type
        notification_message (str): notification message
        session (request): session for the url
    """
    req = session.post(url=os.getenv(SLACK_DEPLOYMENT_NOTIFICATION_WEBHOOK_VAR),
                       headers={
                           'Content-type': 'application/json'},
                       json={'text': f'Deployment Message: {notification_type} - {notification_message}'})
    logging.info(
        'Notification sent to deployment with response status code: '
        + str(req.status_code))


def send_error_notification_to_user(notification_message: str, session):
    """sends the error notification to user

    Args:
        notification_message (str): notification message
        session (_type_): session for the requested url
    """
    req = session.post(url=os.getenv(SLACK_ERROR_NOTIFICATION_WEBHOOK_VAR),
                       headers={
                           'Content-type': 'application/json'},
                       json={'text': f'Error Message: ERROR - {notification_message}'})
    logging.info(
        'Error notification sent to deployment with response status code: '
        + str(req.status_code))


def send_notification_to_user(company_name: str, job_id: str,
                              job_title: str, job_posted_date: str,
                              job_application_link: str, session):
    """sends the notification to the user for the company position with details

    Args:
        company_name (str): company name
        job_id (str): job id
        job_title (str): job title
        job_posted_date (str): job creation date
        job_application_link (str): job application link
        session (request): session for the url
    """
    req = session.post(url=os.getenv(SLACK_JOB_NOTIFICATION_WEBHOOK_VAR),
                       headers={
                           'Content-type': 'application/json'},
                       json={
                           'text': f'Company Name: *{company_name}*\nJob Id: *{job_id}*\nJob Title: *{job_title}*\nPosted Date: *{job_posted_date.strftime("%m/%d/%Y")}*\nApply: <{job_application_link}>\n----------\n'
    }
    )
    logging.info(
        'notification sent to deployment with response status code: '
        + str(req.status_code))


def update_known_jobs(company_info: Dict[str, str]):
    """updated the newly found known job in the csv file

    Args:
        company_info (Dict[str,str]): company name and its new job ids
    """
    with open(COMPANY_KNOWN_JOBS_CSV, 'w', newline='') as company_known_csvfile:
        # create the csv writer
        writer = csv.writer(company_known_csvfile)
        # write a row to the csv file
        writer.writerow(['CompanyID', 'KnownJobs'])
        for company_id in company_info:
            company_data = company_info[company_id]
            writer.writerow([company_id, company_data['KnownJobs']])
    logging.info('Updated the known jobs file.')


def main():
    if not os.path.exists(LOG_FOLDER_LOCATION):
        os.makedirs(LOG_FOLDER_LOCATION)
    logging.basicConfig(filename=LOG_FILE_LOCATION,
                        level=logging.DEBUG, filemode='w')
    load_dotenv()
    with requests.session() as session:
        current_date_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        company_info = None
        try:
            send_deployment_notification_to_user(
                "Info", f'{current_date_time} - Starting the application ...', session)
            # -- Already Known Stuff --
            company_info = get_company_data()
            # -- Fetching New Data --
            for company_id in company_info:
                company_name = company_info[company_id]['CompanyName']
                monitor_status = company_info[company_id]['MonitorStatus']
                if monitor_status != 'Enabled':
                    logging.info(
                        f"Bypassing {company_name} as information not available")
                    continue
                # Get the keywords for this company
                keywords = company_info[company_id]['Keywords']
                company_portal = company_info[company_id]['CompanyPortal']
                # Get the search API url
                search_api_url = company_info[company_id]['SearchAPI']
                search_api_type = company_info[company_id]['SearchType']
                search_api_header = company_info[company_id]['SearchHeader']
                search_api_extra_header = company_info[company_id]['SearchExtraHeader']
                known_jobs = company_info[company_id]['KnownJobs'].split('|')
                relevant_jobs = get_relevant_jobs(company_name, company_portal, search_api_type,
                                                  search_api_url, keywords, search_api_header, search_api_extra_header, session)
                if len(relevant_jobs) < 1:
                    continue
                for job_id in relevant_jobs:
                    # If job not present in the already notified list,
                    # notify it to the user, add that job id to already notified list
                    if job_id not in known_jobs:
                        job_title = relevant_jobs[job_id]['title']
                        job_posted_date = relevant_jobs[job_id]['posted_date']
                        job_application_link = relevant_jobs[job_id]['apply']
                        logging.info(
                            f'New job found: {job_title} posted on : {job_posted_date} for company:{company_name}. Notifying user ...')
                        # send notification
                        send_notification_to_user(company_name, job_id, job_title,
                                                  job_posted_date, job_application_link, session)
                        # save the job id to known jobs list
                        known_jobs.append(job_id)
                company_info[company_id]['KnownJobs'] = '|'.join(known_jobs)
            # rewrite the csv file with the new known job list
            if company_info:
                update_known_jobs(company_info)
            logging.info('All new jobs notified to the user.')
            current_date_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            send_deployment_notification_to_user(
                "Information", f"{current_date_time} - Application completed successfully.", session)
        except Exception as e:
            if company_info:
                update_known_jobs(company_info)
            current_date_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            logging.error(f'Error occurred: {e}')
            # send error notification to user
            send_error_notification_to_user(
                f"{current_date_time} - {traceback.format_exc()}", session)


if __name__ == '__main__':
    main()

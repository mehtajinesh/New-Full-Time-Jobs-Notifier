import copy
import math
import os
from typing import Dict, List
import urllib
import logging
from datetime import datetime, date
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
import json
from json import JSONDecodeError

from utils import get_past_date
from constants import FUZZY_RATIO_MATCH, DAYS_TO_CHECK, SLACK_ERROR_NOTIFICATION_WEBHOOK_VAR, TERMS_TO_IGNORE


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


def get_relevant_jobs(company_name: str, company_portal, search_api_type: str, search_api_url: str,
                      keywords: List[str], search_api_header: Dict, search_api_extra_header, session) -> Dict:
    """gets the relevant jobs from the company's career page

    Args:
        company_name (str): company name
        company_portal (str): company portal type
        search_api_type (str): search api type
        search_api_url (str): search api url
        keywords (List[str]): list of keywords to search from
        search_api_header (Dict): search api header
        session (request): requests session object

    Returns:
        Dict: relevant jobs
    """
    relevant_jobs = {}
    original_search_api_url = search_api_url
    try:
        for keyword in keywords:
            if search_api_type == "GET":
                # Push the keyword to the url (replace it with curly brackets)
                # Update the search url with the keywords
                search_api_url = original_search_api_url.replace(
                    "{}", urllib.parse.quote(keyword))
                # For each keyword, get the job details using keyword, api and headers
                logging.info(
                    f'Fetching data from {company_name} for keyword: {keyword} ...')
            else:
                if company_portal == "Workday":
                    search_api_header['searchText'] = keyword.replace(
                        " ", "+").lower()
                elif company_portal == "Uber":
                    search_api_header['params']['query'] = keyword.lower()
                elif company_portal == "Tiktok":
                    search_api_header['keyword'] = keyword.lower()
                elif company_portal == "Akamai":
                    search_api_header['fieldData']['fields']['KEYWORD'] = keyword.lower(
                    )
                # For each keyword, get the job details using keyword, api and headers
                logging.info(
                    f'Fetching data from {company_name} for keyword: {keyword} ...')
            response = get_response_for_search_url(search_api_type,
                                                   search_api_url, session, search_api_header, search_api_extra_header)
            if not response:
                return relevant_jobs
            if company_name == 'Amazon':
                relevant_jobs.update(for_amazon(keyword, response))
            elif company_name == 'Google':
                relevant_jobs.update(for_google(
                    keyword, response, search_api_url, session))
            elif company_name == 'Netflix':
                relevant_jobs.update(for_netflix(keyword, response))
            elif company_name == 'Apple':
                relevant_jobs.update(for_apple(keyword, response, session))
            elif company_name == 'Microsoft':
                relevant_jobs.update(for_microsoft(
                    keyword, search_api_url, response, session))
            elif company_name == 'Tencent':
                relevant_jobs.update(for_tencent(keyword, response))
            elif company_name == 'Oracle':
                relevant_jobs.update(for_oracle(keyword, response))
            elif company_name == 'Nvidia':
                relevant_jobs.update(for_nvidia(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'AstraZeneca':
                relevant_jobs.update(for_astrazeneca(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'DeepMind':
                relevant_jobs.update(for_deepmind(keyword, response))
            elif company_name == 'JaneStreet':
                relevant_jobs.update(for_janestreet(keyword, response))
            elif company_name == 'Qualcomm':
                relevant_jobs.update(for_qualcomm(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Intuit':
                relevant_jobs.update(for_intuit(keyword, response, session))
            elif company_name == 'GoldmanSachs':
                relevant_jobs.update(for_goldman_sachs(
                    keyword, response))
            elif company_name == 'LG':
                relevant_jobs.update(
                    for_lg(keyword, response, search_api_url, session))
            elif company_name == 'Uber':
                relevant_jobs.update(
                    for_uber(keyword, response, search_api_url, search_api_header, session))
            elif company_name == 'Tiktok':
                relevant_jobs.update(
                    for_tiktok(keyword, response, search_api_url, search_api_header, session))
            elif company_name == 'Akamai':
                relevant_jobs.update(
                    for_akamai(keyword, response, search_api_url, search_api_header, search_api_extra_header, session))
            elif company_name == 'Atlassian':
                relevant_jobs.update(
                    for_atlassian(keyword, response))
            elif company_name == 'AMD':
                relevant_jobs.update(
                    for_amd(keyword, response, search_api_url, session))
            elif company_name == 'Cisco':
                relevant_jobs.update(
                    for_cisco(keyword, response, search_api_url, session))
            elif company_name == 'SchniederElectric':
                relevant_jobs.update(
                    for_schnieder_electric(keyword, response, search_api_url, session))
            elif company_name == 'Stripe':
                relevant_jobs.update(
                    for_stripe(keyword, response))
            elif company_name == 'Tesla':
                relevant_jobs.update(
                    for_tesla(keyword, response))
            elif company_name == 'Databricks':
                relevant_jobs.update(for_databricks(
                    response, keyword, session))
    # Oracle Cloud Based Companies
            elif company_name == 'JPMorgon':
                relevant_jobs.update(for_jpmorgon(
                    keyword, response))
            elif company_name == 'Citizens':
                relevant_jobs.update(for_citizens(
                    keyword, response))
    # Eightfold Based Companies
            elif company_name == 'MorganStanley':
                relevant_jobs.update(for_morgan_stanley(
                    keyword, response, search_api_url, session))
            elif company_name == 'AmericanExpress':
                relevant_jobs.update(for_american_express(
                    keyword, response, search_api_url, session))
    # Workday Based Banks
            elif company_name == 'BankOfAmerica':
                relevant_jobs.update(for_bank_of_america(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'CapitalOne':
                relevant_jobs.update(for_capital_one(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'WellsFargo':
                relevant_jobs.update(for_wells_fargo(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Citi':
                relevant_jobs.update(for_citi(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Santander':
                relevant_jobs.update(for_santander(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'StateStreet':
                relevant_jobs.update(for_state_street(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Discover':
                relevant_jobs.update(for_discover(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'DeutscheBank':
                relevant_jobs.update(for_deutsche_bank(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
    # Workday Based Tech Companies
            elif company_name == 'Sony':
                relevant_jobs.update(for_sony(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Adobe':
                relevant_jobs.update(for_adobe(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'VMWare':
                relevant_jobs.update(for_vmware(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            # elif company_name == 'HPE':
            #     relevant_jobs.update(for_hpe(
            #         keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Salesforce':
                relevant_jobs.update(for_salesforce(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'ABCFinancialServices':
                relevant_jobs.update(for_abc_financial_services(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'ActivisionBlizzard':
                relevant_jobs.update(for_activision_blizzard(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'AutoDesk':
                relevant_jobs.update(for_autodesk(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Belkin':
                relevant_jobs.update(for_belkin(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'BlackBerry':
                relevant_jobs.update(for_blackberry(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Disney':
                relevant_jobs.update(for_disney(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Paypal':
                relevant_jobs.update(for_paypal(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Workday':
                relevant_jobs.update(for_workday(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'KLA':
                relevant_jobs.update(for_kla(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Snapchat':
                relevant_jobs.update(for_snapchat(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'HPE':
                relevant_jobs.update(for_hpe(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Overstock':
                relevant_jobs.update(for_overstock(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Regions':
                relevant_jobs.update(for_regions(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "USFoods":
                relevant_jobs.update(for_usfoods(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "Activision Blizzard Media":
                relevant_jobs.update(for_activision_blizzard_media(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "Carrier":
                relevant_jobs.update(for_carrier(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "Dell":
                relevant_jobs.update(for_dell(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "ULine":
                relevant_jobs.update(for_uline(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "Yahoo":
                relevant_jobs.update(for_yahoo(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "Gartner":
                relevant_jobs.update(for_gartner(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "BroadInstitute":
                relevant_jobs.update(for_broad_institute(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "Walmart":
                relevant_jobs.update(for_walmart(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "WarnerBrothers":
                relevant_jobs.update(for_warner_brothers(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "SonyGlobal":
                relevant_jobs.update(for_sony_global(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == "SonyPictures":
                relevant_jobs.update(for_sony_pictures(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'Fidelity':
                relevant_jobs.update(for_fidelity(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
            elif company_name == 'NorthWestern Mutual':
                relevant_jobs.update(for_northwestern_mutual(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
    # Greenhouse Based Companies
            elif company_name == 'Apollo.io':
                relevant_jobs.update(greenhouse_based_company(
                    response, keyword, session))
            elif company_name == 'Samsung Research America':
                relevant_jobs.update(greenhouse_based_company(
                    response, keyword, session))
            elif company_name == 'OpenAI':
                relevant_jobs.update(greenhouse_based_company(
                    response, keyword, session))
    # Lever Based Companies
            elif company_name == 'Plaid':
                relevant_jobs.update(for_plaid(
                    response, keyword, session))
            elif company_name == 'Lucid':
                relevant_jobs.update(for_lucid(
                    response, keyword, session))
    # SmartRecruiters Based Companies
            elif company_name == 'Bosch':
                relevant_jobs.update(smartrecruiters_based_company(
                    response, keyword, session))
    except JSONDecodeError as e:
        logging.info(
            f'Looks like the company [ {company_name} ] career page is down. So will try later in 20 mins')
        send_error_notification_to_user(
            f'Looks like the company [ {company_name} ] career page is down. So will try later in 20 mins', session)
    return relevant_jobs


def get_response_for_search_url(search_type: str, search_api_url: str, session, search_api_header: Dict = "", search_api_extra_header: Dict = "") -> Dict:
    """gets the page response from the given search api url

    Args:
        search_type (str): search type
        search_api_url (str): search api url
        session (request): session object
        search_api_header (Dict): search api headers

    Returns:
        request: response from the page
    """
    if search_type == "POST":
        req = None
        if search_api_extra_header:
            req = session.post(
                url=search_api_url, json=search_api_header, headers=search_api_extra_header)
        else:
            req = session.post(
                url=search_api_url, json=search_api_header)
        logging.info(
            f'Data fetched from search with response status code: '
            + str(req.status_code))
        if ("text/html" in req.headers['Content-Type']) or ("text/plain" in req.headers['content-type']):
            response = req.text
        else:
            response = req.json()
    else:
        req = session.get(url=search_api_url)
        logging.info(
            f'Data fetched from search with response status code: '
            + str(req.status_code))
        if not req.headers:
            return {}
        if "text/html" in req.headers['Content-Type']:
            response = req.text
        else:
            response = req.json()
    return response


def for_deepmind(keyword: str, response: Dict) -> Dict[str, Dict]:
    """logic for getting jobs from amazon careers page response

    Args:
        keyword (str): keyword for job title matching
        response (Dict): raw response from the website

    Returns:
        Dict[str, Dict]: relevant jobs where key is jobID and value is jobInformation
    """
    relevant_jobs = {}
    available_jobs = response['jobs']
    for job in available_jobs:
        job_id = str(job['id'])
        if 'title' in job:
            curr_job_title = job['title']
            posted_date = datetime.strptime(
                job['updated_at'], "%Y-%m-%dT%H:%M:%S%z").date()
            today = date.today()
            location = job['location']['name']
            if "US" in location:
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': job['absolute_url']}
    return relevant_jobs


def for_apple(keyword: str, response: Dict, session) -> Dict[str, Dict]:
    """gets the job positions from apple's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): page response
        session (request): request session object

    Returns:
        [str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_page(page_available_jobs, keyword):
        page_relevant_jobs = {}
        for job in page_available_jobs:
            job_id = job['positionId']
            curr_job_title = job['postingTitle']
            posted_date = datetime.strptime(
                job['postingDate'], "%b %d, %Y").date()
            today = date.today()
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    date_difference = today - posted_date
                    if date_difference.days < DAYS_TO_CHECK:
                        page_relevant_jobs[job_id] = {
                            'title': curr_job_title, 'posted_date': posted_date,
                            'apply': f"https://jobs.apple.com/en-us/details/{job_id}/{job['transformedPostingTitle']}?team={job['team']['teamCode']}"}
        return page_relevant_jobs

    def get_relevant_jobs_from_html_response(page_response, keyword):
        response_relevant_jobs = {}
        soup = BeautifulSoup(page_response, 'html.parser')
        scripts = soup.find_all('script', {"type": "text/javascript"})
        pages = 0
        url = ""
        if len(scripts) > 0:
            data = scripts[0].text
            data = data.replace("\n      window.APP_STATE = ", "")
            data = data.replace(";\n", "").strip()
            json_data = json.loads(data)
            total_jobs = json_data['totalRecords']
            if total_jobs:
                pages = math.ceil(total_jobs / 20)
                response_available_jobs = json_data['searchResults']
                url = json_data['fullUrl']
                response_relevant_jobs = get_relevant_jobs_from_page(
                    response_available_jobs, keyword)
        return response_relevant_jobs, pages, url

    relevant_jobs, no_of_pages, org_url = get_relevant_jobs_from_html_response(
        response, keyword)
    if no_of_pages > 1 and org_url != "":
        curr_page_count = 2
        while (curr_page_count < min(5, no_of_pages)):
            new_url = org_url + f'&page={curr_page_count}'
            new_response = get_response_for_search_url("GET", new_url, session)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, new_pages, org_url = get_relevant_jobs_from_html_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_amazon(keyword: str, response: Dict) -> Dict[str, Dict]:
    """logic for getting jobs from amazon careers page response

    Args:
        keyword (str): keyword for job title matching
        response (Dict): raw response from the website

    Returns:
        Dict[str, Dict]: relevant jobs where key is jobID and value is jobInformation
    """
    relevant_jobs = {}
    available_jobs = response['jobs']
    for job in available_jobs:
        job_id = job['id_icims']
        curr_job_title = job['title']
        posted_date = datetime.strptime(
            job['posted_date'], "%B %d, %Y").date()
        today = date.today()
        if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
            ignore_position = False
            for term in TERMS_TO_IGNORE:
                if term in curr_job_title:
                    ignore_position = True
                    break
            if not ignore_position:
                date_difference = today - posted_date
                if date_difference.days < DAYS_TO_CHECK:
                    relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://www.amazon.jobs{job['job_path']}"}
    return relevant_jobs


def for_google(keyword: str, response: Dict, search_api_url, session) -> Dict[str, Dict]:
    """logic for getting jobs from google careers page response

    Args:
        keyword (str): keyword for job title matching
        response (Dict): raw response from the website

    Returns:
        Dict[str, Dict]: relevant jobs where key is jobID and value is jobInformation
    """
    def get_relevant_jobs_from_page(page_available_jobs, keyword):
        page_relevant_jobs = {}
        for job in page_available_jobs:
            job_id = job[0]
            curr_job_title = job[1].split(",")[0]
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    page_relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': date.today(),
                        'apply': job[2]}
        return page_relevant_jobs

    def get_relevant_jobs_from_html_response(page_response, keyword):
        response_relevant_jobs = {}
        soup = BeautifulSoup(page_response, 'html.parser')
        scripts = soup.find_all('script')
        pages = 0
        for script in scripts:
            data = script.text
            if not data.startswith("AF_initDataCallback({key: \'ds:1\'"):
                continue
            data = data.replace("hash: \'2\',", "").replace("hash: \'1\',", "").replace(
                "AF_initDataCallback({key: \'ds:1\',", "{").replace("data:", '"data":').replace("sideChannel:", '"sideChannel":')[:-2]
            json_data = json.loads(data)
            total_jobs = json_data['data'][2]
            pages = math.ceil(total_jobs / 20)
            response_available_jobs = json_data['data'][0]
            response_relevant_jobs = get_relevant_jobs_from_page(
                response_available_jobs, keyword)
        return response_relevant_jobs, pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_html_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 2
        while (curr_page_count < min(5, no_of_pages)):
            new_url = search_api_url + f'&page={curr_page_count}'
            new_response = get_response_for_search_url("GET", new_url, session)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, new_pages = get_relevant_jobs_from_html_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_netflix(keyword: str, response: Dict) -> Dict[str, Dict]:
    """gets all the revelant jobs from netflix's careers page

    Args:
        keyword (str): keyword to match in job title
        response (Dict): raw response from netflix's page

    Returns:
        Dict[str, Dict]: relevant positions with their information
    """
    relevant_jobs = {}
    available_jobs = response['records']['postings']
    for job in available_jobs:
        job_id = job['external_id']
        curr_job_title = job['text']
        posted_date = datetime.strptime(
            job['created_at'], "%Y-%m-%dT%H:%M:%S%z").date()
        today = date.today()
        if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
            ignore_position = False
            for term in TERMS_TO_IGNORE:
                if term in curr_job_title:
                    ignore_position = True
                    break
            if not ignore_position:
                date_difference = today - posted_date
                if date_difference.days < DAYS_TO_CHECK:
                    relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://jobs.netflix.com/jobs/{job_id}"}
    return relevant_jobs


def for_ibm(keyword: str, response: Dict) -> Dict[str, Dict]:
    """gets all the revelant jobs from ibm's careers page

    Args:
        keyword (str): keyword to match in job title
        response (Dict): raw response from ibm's page

    Returns:
        Dict[str, Dict]: relevant positions with their information
    """
    relevant_jobs = {}
    available_jobs = response['queryResult']
    for job in available_jobs:
        job_id = job['id']
        curr_job_title = job['title']
        posted_date = datetime.strptime(
            job['open_date'], "%Y-%m-%dT%H:%M:%S%z").date()
        today = date.today()
        country = job['primary_country']
        if country == 'US':
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    date_difference = today - posted_date
                    if date_difference.days < DAYS_TO_CHECK:
                        relevant_jobs[job_id] = {
                            'title': curr_job_title, 'posted_date': posted_date, 'apply': f"{job['url']}"}
    return relevant_jobs


def for_microsoft(keyword: str, search_api_url: str, response: Dict, session) -> Dict[str, Dict]:
    """gets the job information from microsoft's career page

    Args:
        keyword (str): keyword to match with job title
        search_api_url (str): search api url for apple's career page
        response (Dict): initial response from the search api url
        session (request): request session object 

    Returns:
        [str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_json_response(page_response, keyword):
        page_relevant_jobs = {}
        total_jobs = page_response["operationResult"]["result"]["totalJobs"]
        no_of_pages = math.ceil(total_jobs / 20)
        page_available_jobs = page_response["operationResult"]["result"]["jobs"]
        for job in page_available_jobs:
            if 'title' in job:
                job_id = job['jobId']
                curr_job_title = job['title']
                posted_date = datetime.strptime(
                    job['postingDate'], "%Y-%m-%dT%H:%M:%S%z").date()
                today = date.today()
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            page_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://careers.microsoft.com/us/en/job/{job_id}"}
        return page_relevant_jobs, no_of_pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 2
        while (curr_page_count < min(5, no_of_pages)):
            new_url = search_api_url + f'&pg={curr_page_count}'
            new_response = get_response_for_search_url("GET", new_url, session)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_tencent(keyword: str, response: Dict) -> Dict[str, Dict]:
    """get the jobs from tencent's career page

    Args:
        keyword (str): keywords to match for tencent's career page
        response (Dict): initial response from tencent's career page

    Returns:
        [str, Dict]: relevant jobs
    """
    relevant_jobs = {}
    available_jobs = response['Data']['Posts']
    for job in available_jobs:
        job_id = str(job['RecruitPostId'])
        curr_job_title = job['RecruitPostName']
        posted_date = datetime.strptime(
            job['LastUpdateTime'], "%B %d,%Y").date()
        today = date.today()
        if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
            ignore_position = False
            for term in TERMS_TO_IGNORE:
                if term in curr_job_title:
                    ignore_position = True
                    break
            if not ignore_position:
                date_difference = today - posted_date
                if date_difference.days < DAYS_TO_CHECK:
                    relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': posted_date, 'apply': f"{job['PostURL']}"}
    return relevant_jobs


def for_oracle(keyword: str, response: Dict) -> Dict[str, Dict]:
    """gets the job information from oracle's career page

    Args:
        keyword (str): keywords to match for job title
        response (Dict): initial response from the oracle's career page

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    relevant_jobs = {}
    available_jobs = response['items'][0]['requisitionList']
    for job in available_jobs:
        if 'title' in job:
            job_id = job['Id']
            curr_job_title = job['Title']
            posted_date = datetime.strptime(
                job['PostedDate'], "%Y-%m-%dT%H:%M:%S%z").date()
            today = date.today()
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    date_difference = today - posted_date
                    if date_difference.days < DAYS_TO_CHECK:
                        relevant_jobs[job_id] = {
                            'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://careers.oracle.com/jobs/#en/sites/jobsearch/job/{job_id}"}
    return relevant_jobs


def for_janestreet(keyword: str, response: Dict) -> Dict[str, Dict]:
    """gets all the revelant jobs from janestreet's careers page

    Args:
        keyword (str): keyword to match in job title
        response (Dict): raw response from janestreet's page

    Returns:
        Dict[str, Dict]: relevant positions with their information
    """
    relevant_jobs = {}
    for job in response:
        job_id = str(job['id'])
        curr_job_title = job['position']
        city = job['city']
        today = date.today()
        if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
            ignore_position = False
            for term in TERMS_TO_IGNORE:
                if term in curr_job_title:
                    ignore_position = True
                    break
            if not ignore_position:
                if city == "NYC":
                    relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': today, 'apply': f"https://www.janestreet.com/join-jane-street/position/{job_id}"}
    return relevant_jobs


def for_intuit(keyword: str, response: Dict, session) -> Dict[str, Dict]:
    """gets the job positions from intuit's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): page response
        session (request): request session object

    Returns:
        [str, Dict]: relevant jobs
    """
    relevant_jobs = {}
    soup = BeautifulSoup(response.strip(), 'html.parser')
    scripts = soup.find_all("div", {"id": "search-results-list"})
    if len(scripts) > 0:
        data = scripts[0]
        # get second item from contents list
        ul_data = data.contents[1]
        for item in ul_data.contents:
            if item.text == '\n':
                continue
            job_data = item.contents[1]
            job_id = job_data['data-job-id']
            curr_job_title = job_data['data-title']
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': date.today(),
                        'apply': f"https://jobs.intuit.com{job_data['href']}"}
    return relevant_jobs


def for_goldman_sachs(keyword: str, response: Dict) -> Dict[str, Dict]:
    """gets the job information from goldman sachs's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    relevant_jobs = {}
    available_jobs = response["data"]["roleSearch"]["items"]
    for job in available_jobs:
        if 'jobTitle' in job:
            job_id = job['externalSource']['sourceId']
            curr_job_title = job['jobTitle']
            posted_date = date.today()
            today = date.today()
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    date_difference = today - posted_date
                    if date_difference.days < DAYS_TO_CHECK:
                        relevant_jobs[job_id] = {
                            'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://higher.gs.com/roles?title={urllib.parse.quote(curr_job_title)}&id={job_id}"}
    return relevant_jobs


def for_lg(keyword: str, response: Dict, search_api_url, session) -> Dict[str, Dict]:
    """gets the job information from lg's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url
        search_api_url (str): search api url for lg's career page
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_page(page_available_jobs, keyword):
        page_relevant_jobs = {}
        for job in page_available_jobs:
            job_id = job['positionId']
            curr_job_title = job['postingTitle']
            posted_date = datetime.strptime(
                job['postingDate'], "%b %d, %Y").date()
            today = date.today()
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    date_difference = today - posted_date
                    if date_difference.days < DAYS_TO_CHECK:
                        page_relevant_jobs[job_id] = {
                            'title': curr_job_title, 'posted_date': posted_date,
                            'apply': f"https://jobs.apple.com/en-us/details/{job_id}/{job['transformedPostingTitle']}?team={job['team']['teamCode']}"}
        return page_relevant_jobs

    def get_relevant_jobs_from_html_response(page_response, keyword):
        response_relevant_jobs = {}
        soup = BeautifulSoup(page_response['postings'], 'html.parser')
        scripts = soup.find_all('tbody')
        pages = 0
        url = ""
        if len(scripts) > 0:
            data = scripts[0].text
            data = data.replace("\n      window.APP_STATE = ", "")
            data = data.replace(";\n", "").strip()
            json_data = json.loads(data)
            total_jobs = json_data['totalRecords']
            pages = math.ceil(total_jobs / 20)
            response_available_jobs = json_data['searchResults']
            url = json_data['fullUrl']
            response_relevant_jobs = get_relevant_jobs_from_page(
                response_available_jobs, keyword)
        return response_relevant_jobs, pages, url

    relevant_jobs, no_of_pages, org_url = get_relevant_jobs_from_html_response(
        response, keyword)
    if no_of_pages > 1 and org_url != "":
        curr_page_count = 2
        while (curr_page_count < min(5, no_of_pages)):
            new_url = org_url + f'&page={curr_page_count}'
            new_response = get_response_for_search_url("GET", new_url, session)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, new_pages, org_url = get_relevant_jobs_from_html_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_uber(keyword: str, response: Dict, search_api_url, search_api_header, session) -> Dict[str, Dict]:
    """gets the job information from uber's career page

    Args:
        keyword (str): keyword to match with job title
        search_api_header (str): search api header for uber's career page
        response (Dict): initial response from the search api url
        session (request): request session object 

    Returns:
        [str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_json_response(page_response, keyword):
        page_relevant_jobs = {}
        total_jobs = page_response["data"]["totalResults"]["low"]
        no_of_pages = math.ceil(total_jobs / 10)
        page_available_jobs = page_response["data"]["results"]
        for job in page_available_jobs:
            if 'title' in job:
                job_id = str(job['id'])
                curr_job_title = job['title']
                posted_date = datetime.strptime(
                    job['updatedDate'], "%Y-%m-%dT%H:%M:%S%z").date()
                today = date.today()
                if job['location']['country'] != "USA":
                    continue
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            page_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://www.uber.com/global/en/careers/list/{job_id}"}
        return page_relevant_jobs, no_of_pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 1
        while (curr_page_count < min(7, no_of_pages)):
            new_header = search_api_header.deepcopy()
            new_header['page'] = curr_page_count
            new_response = get_response_for_search_url(
                "POST", search_api_url, session, new_header)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_tiktok(keyword, response, search_api_url, search_api_header, session) -> Dict[str, Dict]:
    """gets the job information from microsoft's career page

    Args:
        keyword (str): keyword to match with job title
        search_api_url (str): search api url for apple's career page
        response (Dict): initial response from the search api url
        session (request): request session object 

    Returns:
        [str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_json_response(page_response, keyword):
        page_relevant_jobs = {}
        total_jobs = page_response["operationResult"]["result"]["totalJobs"]
        no_of_pages = math.ceil(total_jobs / 20)
        page_available_jobs = page_response["operationResult"]["result"]["jobs"]
        for job in page_available_jobs:
            if 'title' in job:
                job_id = job['jobId']
                curr_job_title = job['title']
                posted_date = datetime.strptime(
                    job['postingDate'], "%Y-%m-%dT%H:%M:%S%z").date()
                today = date.today()
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            page_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://careers.microsoft.com/us/en/job/{job_id}"}
        return page_relevant_jobs, no_of_pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 2
        while (curr_page_count < min(5, no_of_pages)):
            new_url = search_api_url + f'&pg={curr_page_count}'
            new_response = get_response_for_search_url("GET", new_url, session)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_akamai(keyword, response, search_api_url, search_api_header, search_api_extra_header, session) -> Dict[str, Dict]:
    """gets the job information from microsoft's career page

    Args:
        keyword (str): keyword to match with job title
        search_api_url (str): search api url for apple's career page
        response (Dict): initial response from the search api url
        session (request): request session object 

    Returns:
        [str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_json_response(page_response, keyword):
        page_relevant_jobs = {}
        total_jobs = page_response["pagingData"]["totalCount"]
        page_available_jobs = page_response["requisitionList"]
        if (total_jobs == 0) or (len(page_available_jobs) == 0):
            return page_relevant_jobs, 0
        no_of_pages = math.ceil(total_jobs / len(page_available_jobs))
        for job in page_available_jobs:
            if 'jobId' in job:
                job_id = job['jobId']
                curr_job_title = job['column'][0]
                posted_date = datetime.strptime(
                    job['column'][2], "%b %d, %Y").date()
                today = date.today()
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            page_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://akamaicareers.inflightcloud.com/apply?section=aka_ext&job={job_id}"}
        return page_relevant_jobs, no_of_pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 2
        while (curr_page_count < min(5, no_of_pages)):
            search_api_header['pageNo'] = curr_page_count
            new_response = get_response_for_search_url("POST",
                                                       search_api_url, session, search_api_header, search_api_extra_header)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_atlassian(keyword, response) -> Dict[str, Dict]:
    """gets the job information from atlassian's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    relevant_jobs = {}
    if 'postings' not in response:
        return
    available_jobs = response['postings']
    for job in available_jobs:
        if 'id' in job:
            job_id = job['id']
            location = job['categories']['location']
            if "United States" not in location:
                continue
            curr_job_title = job['text']
            posted_date = datetime.fromtimestamp(job['updatedAt']/1000).date()
            today = date.today()
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    date_difference = today - posted_date
                    if date_difference.days < DAYS_TO_CHECK:
                        relevant_jobs[job_id] = {
                            'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://jobs.lever.co/atlassian/{job_id}/apply"}
    return relevant_jobs


def for_amd(keyword, response, search_api_url, session) -> Dict[str, Dict]:
    """gets the job information from amd's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_json_response(page_response, keyword):
        page_relevant_jobs = {}
        total_jobs = page_response["totalCount"]
        if total_jobs == 0:
            return page_relevant_jobs, 0
        page_available_jobs = page_response["jobs"]
        no_of_pages = math.ceil(total_jobs / len(page_available_jobs))
        for job in page_available_jobs:
            if 'req_id' in job['data']:
                job_id = job['data']['req_id']
                curr_job_title = job['data']['title']
                posted_date = datetime.strptime(
                    job['data']['posted_date'], "%B %d, %Y").date()
                today = date.today()
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            page_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': job['data']['apply_url']}
        return page_relevant_jobs, no_of_pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 2
        while (curr_page_count < min(5, no_of_pages)):
            new_search_api_url = search_api_url + f'&page={curr_page_count}'
            new_response = get_response_for_search_url(
                "GET", new_search_api_url, session)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_cisco(keyword, response, search_api_url, session) -> Dict[str, Dict]:
    """gets the job information from cisco's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_html_response(page_response, keyword):
        response_relevant_jobs = {}
        soup = BeautifulSoup(page_response.strip(), 'html.parser')
        scripts = soup.find_all('tbody')
        if len(scripts) > 0:
            data = scripts[0]
            for item in data.contents:
                if item.text == '\n':
                    continue
                temp = item.contents[1]
                if temp.text == 'No results':
                    break
                job_link = temp.contents[0]['href']
                job_id = job_link.split('/')[-1]
                curr_job_title = item.contents[1].contents[0].text
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        today = date.today()
                        new_response_date = session.get(url=job_link)
                        date_soup = BeautifulSoup(
                            new_response_date.text.strip(), 'html.parser')
                        date_scripts = date_soup.find_all(
                            'script', {'type': 'application/ld+json'})
                        date_inter = date_scripts[0].contents[0]
                        date_json = json.loads(date_inter)
                        posted_date = datetime.strptime(
                            date_json['datePosted'], "%Y-%m-%d").date()
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            response_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date,
                                'apply': job_link}
        return response_relevant_jobs

    response_total = session.get(
        url=f"https://jobs.cisco.com/jobs/SearchJobsResultsAJAX/{urllib.parse.quote(keyword)}?21178=%5B169482%5D&21178_format=6020&21180=%5B164,163%5D&21180_format=6022&listFilterMode=1")
    total_jobs = int(response_total.content.strip())
    if total_jobs == 0:
        return {}
    no_of_pages = math.ceil(total_jobs / 25)
    relevant_jobs = get_relevant_jobs_from_html_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 1
        while (curr_page_count < min(20, no_of_pages)):
            new_search_api_url = search_api_url + \
                f'&projectOffset={25*curr_page_count}'
            new_response = get_response_for_search_url(
                "GET", new_search_api_url, session)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs = get_relevant_jobs_from_html_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_schnieder_electric(keyword, response, search_api_url, session) -> Dict[str, Dict]:
    """gets the job information from schnieder electric's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    def get_relevant_jobs_from_json_response(page_response, keyword):
        page_relevant_jobs = {}
        total_jobs = page_response["totalCount"]
        if total_jobs == 0:
            return page_relevant_jobs, 0
        page_available_jobs = page_response["jobs"]
        no_of_pages = math.ceil(total_jobs / 10)
        for job in page_available_jobs:
            if 'req_id' in job['data']:
                job_id = job['data']['req_id']
                curr_job_title = job['data']['title']
                posted_date = datetime.strptime(
                    job['data']['meta_data']['last_mod'], "%Y-%m-%dT%H:%M:%S%z").date()
                today = date.today()
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            page_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': job['data']['apply_url']}
        return page_relevant_jobs, no_of_pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 2
        while (curr_page_count < min(20, no_of_pages)):
            new_search_api_url = search_api_url + f'&page={curr_page_count}'
            new_response = get_response_for_search_url(
                "GET", new_search_api_url, session)
            if not new_response:
                return relevant_jobs
            new_relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
    return relevant_jobs


def for_stripe(keyword, response) -> Dict[str, Dict]:
    """gets the job information from stripe's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    relevant_jobs = {}
    soup = BeautifulSoup(response.strip(), 'html.parser')
    scripts = soup.find_all('tbody')
    if len(scripts) > 0:
        data = scripts[0]
        for item in data.contents:
            if item.text == '\n':
                continue
            temp = item.contents[1]
            if temp.text == 'No results':
                break
            job_link = temp.contents[0]['href']
            job_id = job_link.split('/')[-1]
            curr_job_title = item.contents[1].contents[0].text
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in curr_job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': date.today(),
                        'apply': job_link}
    return relevant_jobs


def for_tesla(keyword, response) -> Dict[str, Dict]:
    """gets the job information from tesla's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    # relevant_jobs = {}
    # all_locations_data = response["geo"][0]["sites"][0]['states']
    # location_ids = []
    # for state in all_locations_data:
    #     cities = state['cities']
    #     for city in cities.values():
    #         location_ids.extend(city)
    # total_jobs = response["listings"]
    # if len(total_jobs) > 0:
    #     for job in total_jobs:
    #         if 'id' in job:

    #             if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
    #                 ignore_position = False
    #                 for term in TERMS_TO_IGNORE:
    #                     if term in curr_job_title:
    #                         ignore_position = True
    #                         break
    #                 if not ignore_position:
    #                     relevant_jobs[job_id] = {
    #                         'title': curr_job_title, 'posted_date': date.today(),
    #                         'apply': job_link}
    # return relevant_jobs


# Oracle Cloud Based Companies


def for_oracle_cloud_based_company(page_respone, job_keyword, apply_prefix):
    relevant_jobs = {}
    if (len(page_respone["items"]) > 0):
        available_jobs = page_respone["items"][0]["requisitionList"]
        for job in available_jobs:
            if 'Title' in job:
                job_id = str(job['Id'])
                curr_job_title = job['Title']
                posted_date = datetime.strptime(
                    job['PostedDate'], "%Y-%m-%dT%H:%M:%S%z").date()
                today = date.today()
                if fuzz.ratio(curr_job_title, job_keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': f"{apply_prefix}{job_id}"}
    return relevant_jobs


def for_jpmorgon(keyword: str, response: Dict) -> Dict[str, Dict]:
    """gets the job information from jpmorgon's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    return for_oracle_cloud_based_company(response, keyword, "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/")


def for_citizens(keyword: str, response: Dict) -> Dict[str, Dict]:
    """gets the job information from citizens's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url

    Returns:
        [str, Dict]: relevant jobs
    """
    return for_oracle_cloud_based_company(response, keyword, "https://hcgn.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job")

# Eightfold Based Companies


def for_eightfold_based_company(company_page_respone, company_job_keyword, search_api_url, session):
    def get_relevant_jobs_from_json_response(page_response, keyword):
        page_relevant_jobs = {}
        total_jobs = page_response["count"]
        no_of_pages = math.ceil(total_jobs / 10)
        page_available_jobs = page_response["positions"]
        for job in page_available_jobs:
            if 'name' in job:
                job_id = str(job['id'])
                curr_job_title = job['name']
                # convert from timestamp to date
                posted_date = datetime.fromtimestamp(job['t_update']).date()
                today = date.today()
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            page_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': job['canonicalPositionUrl']}
        return page_relevant_jobs, no_of_pages
    relevant_jobs = {}
    if "count" in company_page_respone:
        relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
            company_page_respone, company_job_keyword)
        if no_of_pages > 1:
            curr_page_count = 1
            while (curr_page_count < min(no_of_pages+1, 5)):
                new_search_api_url = search_api_url + \
                    f"&start={curr_page_count*10}&num=10"
                new_response = get_response_for_search_url(
                    "GET", new_search_api_url, session)
                if not new_response:
                    return relevant_jobs
                new_relevant_jobs, new_pages = get_relevant_jobs_from_json_response(
                    new_response, company_job_keyword)
                relevant_jobs.update(new_relevant_jobs)
                curr_page_count += 1
    return relevant_jobs


def for_morgan_stanley(keyword: str, response: Dict, search_api_url, session) -> Dict[str, Dict]:
    """gets the job information from morgan stanley's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url
        search_api_url (str): search api url
        session (_type_): request session object

    Returns:
        [str, Dict]: relevant jobs
    """
    return for_eightfold_based_company(response, keyword, search_api_url, session)


def for_american_express(keyword: str, response: Dict, search_api_url, session) -> Dict[str, Dict]:
    """gets the job information from american express's career page

    Args:
        keyword (str): keyword to match with job title
        response (Dict): initial response from the search api url
        search_api_url (str): search api url
        session (_type_): request session object

    Returns:
        [str, Dict]: relevant jobs
    """
    return for_eightfold_based_company(response, keyword, search_api_url, session)

# Workday based Companies


def workday_based_company(company_page_respone, company_job_keyword, company_apply_link_prefix, search_api_header, search_api_url, session):
    relevant_jobs = {}

    def get_relevant_jobs_from_json_response(page_response, keyword, apply_link_prefix):
        page_relevant_jobs = {}
        if "total" not in page_response:
            return page_relevant_jobs, 0
        total_jobs = page_response["total"]
        no_of_pages = math.ceil(total_jobs / 20)
        page_available_jobs = page_response["jobPostings"]
        for job in page_available_jobs:
            if 'title' in job:
                job_id = job['bulletFields'][0]
                curr_job_title = job['title']
                posted_date = get_past_date(job['postedOn'].replace(
                    "Posted ", "").replace("+", "").lower())
                today = date.today()
                if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in curr_job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            page_relevant_jobs[job_id] = {
                                'title': curr_job_title, 'posted_date': posted_date, 'apply': f"{apply_link_prefix}{job['externalPath']}"}
        return page_relevant_jobs, no_of_pages
    if "total" in company_page_respone:
        relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
            company_page_respone, company_job_keyword, company_apply_link_prefix)
        if no_of_pages > 1:
            curr_page_count = 2
            while (curr_page_count < min(no_of_pages+1, 5)):
                search_api_header['offset'] += 20
                new_response = get_response_for_search_url(
                    "POST", search_api_url, session, search_api_header)
                if not new_response:
                    return relevant_jobs
                new_relevant_jobs, new_pages = get_relevant_jobs_from_json_response(
                    new_response, company_job_keyword, company_apply_link_prefix)
                relevant_jobs.update(new_relevant_jobs)
                curr_page_count += 1
    return relevant_jobs


def for_sony(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the sony career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for sony
    """
    return workday_based_company(response, keyword, "https://sonyglobal.wd1.myworkdayjobs.com/en-US/SonyGlobalCareers", search_api_header, search_api_url, session)


def for_adobe(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the adobe career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for adobe
    """
    return workday_based_company(response, keyword, "https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced", search_api_header, search_api_url, session)


def for_salesforce(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the salesforce career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for salesforce
    """
    return workday_based_company(response, keyword, "https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site", search_api_header, search_api_url, session)


def for_abc_financial_services(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the abc finanacial career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for finanacial
    """
    return workday_based_company(response, keyword, "https://abcfinancial.wd5.myworkdayjobs.com/en-US/ABCFinancialServices", search_api_header, search_api_url, session)


def for_activision_blizzard(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the activision blizzard career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for activision blizzard
    """
    return workday_based_company(response, keyword, "https://activision.wd1.myworkdayjobs.com/External", search_api_header, search_api_url, session)


def for_autodesk(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the autodesk career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for autodesk
    """
    return workday_based_company(response, keyword, "https://autodesk.wd1.myworkdayjobs.com/Ext", search_api_header, search_api_url, session)


def for_belkin(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the belkin career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for belkin
    """
    return workday_based_company(response, keyword, "https://belkin.wd5.myworkdayjobs.com/belkin_careers/jobs", search_api_header, search_api_url, session)


def for_blackberry(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from blackberry's career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object
    Returns:
        Dict[str, Dict]: relevant jobs for blackberry
    """
    return workday_based_company(response, keyword, "https://bb.wd3.myworkdayjobs.com/BlackBerry", search_api_header, search_api_url, session)


def for_astrazeneca(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the astrazeneca career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for astrazeneca
    """
    return workday_based_company(response, keyword, "https://astrazeneca.wd3.myworkdayjobs.com/en-US/Careers", search_api_header, search_api_url, session)


def for_nvidia(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from nvidia's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite", search_api_header, search_api_url, session)


def for_qualcomm(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the qualcomm career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for qualcomm
    """
    return workday_based_company(response, keyword, "https://qualcomm.wd5.myworkdayjobs.com/en-US/External", search_api_header, search_api_url, session)


def for_bank_of_america(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets all the relevant jobs from the bank of america career's page

    Args:
        keyword (str): keyword to match for job
        search_api_url (str): search api url
        response (Dict): response for the initial query
        search_api_header (Dict): search api header
        session (_type_): request session object

    Returns:
        Dict[str, Dict]: relevant jobs for bank of america
    """
    return workday_based_company(response, keyword, "https://ghr.wd1.myworkdayjobs.com/en-US/Lateral-US", search_api_header, search_api_url, session)


def for_capital_one(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from capital one's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://capitalone.wd1.myworkdayjobs.com/Capital_One", search_api_header, search_api_url, session)


def for_wells_fargo(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from wells fargo's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://wd1.myworkdaysite.com/en-US/recruiting/wf/WellsFargoJobs", search_api_header, search_api_url, session)


def for_citi(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from citi's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://citi.wd5.myworkdayjobs.com/2", search_api_header, search_api_url, session)


def for_santander(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from santander's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://santander.wd3.myworkdayjobs.com/en-US/SantanderCareers", search_api_header, search_api_url, session)


def for_state_street(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from state street corporation's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://statestreet.wd1.myworkdayjobs.com/en-US/Global", search_api_header, search_api_url, session)


def for_discover(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from discover's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://discover.wd5.myworkdayjobs.com/en-US/Discover", search_api_header, search_api_url, session)


def for_deutsche_bank(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from deutsche bank's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://db.wd3.myworkdayjobs.com/en-US/DBWebsite", search_api_header, search_api_url, session)


def for_vmware(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from vmware's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://vmware.wd1.myworkdayjobs.com/VMware", search_api_header, search_api_url, session)


def for_disney(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from disney's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://disney.wd5.myworkdayjobs.com/en-US/disneycareer", search_api_header, search_api_url, session)


def for_paypal(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from paypal's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://wd1.myworkdaysite.com/recruiting/paypal/jobs", search_api_header, search_api_url, session)


def for_workday(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions from workday's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://workday.wd5.myworkdayjobs.com/Workday", search_api_header, search_api_url, session)


def for_kla(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions kla's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://kla.wd1.myworkdayjobs.com/Search", search_api_header, search_api_url, session)


def for_snapchat(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions kla's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object

    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://wd1.myworkdaysite.com/en-US/recruiting/snapchat/snap/", search_api_header, search_api_url, session)


def for_hpe(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions hpe's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://hpe.wd5.myworkdayjobs.com/en-US/Jobsathpe", search_api_header, search_api_url, session)


def for_overstock(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions overstock's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header 
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://overstock.wd5.myworkdayjobs.com/Overstock_Careers", search_api_header, search_api_url, session)


def for_regions(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions regions's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header 
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://regions.wd5.myworkdayjobs.com/Regions_Careers", search_api_header, search_api_url, session)


def for_usfoods(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions usfoods's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header 
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://usfoods.wd1.myworkdayjobs.com/usfoodscareersExternal", search_api_header, search_api_url, session)


def for_activision_blizzard_media(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job positions activision blizzard media's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header 
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://activision.wd1.myworkdayjobs.com/King_External_Careers", search_api_header, search_api_url, session)


def for_carrier(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available job carrier's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header 
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://carrier.wd5.myworkdayjobs.com/jobs", search_api_header, search_api_url, session)


def for_dell(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available dell's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header 
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://dell.wd1.myworkdayjobs.com/External", search_api_header, search_api_url, session)


def for_uline(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available dell's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header 
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://uline.wd1.myworkdayjobs.com/External", search_api_header, search_api_url, session)


def for_yahoo(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available yahoo's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header 
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://ouryahoo.wd5.myworkdayjobs.com/en-US/careers", search_api_header, search_api_url, session)


def for_gartner(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available gartner's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header 
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://gartner.wd5.myworkdayjobs.com/EXT", search_api_header, search_api_url, session)


def for_broad_institute(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available broad institute's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        response (Dict): response for initial query
        search_api_header (Dict): search api header 
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """
    return workday_based_company(response, keyword, "https://broadinstitute.wd1.myworkdayjobs.com/broad_institute", search_api_header, search_api_url, session)


def for_walmart(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available walmart's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header 
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """

    return workday_based_company(response, keyword, "https://walmart.wd5.myworkdayjobs.com/en-US/WalmartExternal", search_api_header, search_api_url, session)


def for_warner_brothers(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available warner brothers's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header 
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """

    return workday_based_company(response, keyword, "https://warnerbros.wd5.myworkdayjobs.com/global", search_api_header, search_api_url, session)


def for_sony_global(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available sony global's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header 
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """

    return workday_based_company(response, keyword, "https://sonyglobal.wd1.myworkdayjobs.com/SonyGlobalCareers", search_api_header, search_api_url, session)


def for_sony_pictures(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available sony pictures's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """

    return workday_based_company(response, keyword, "https://spe.wd1.myworkdayjobs.com/Sonypictures", search_api_header, search_api_url, session)


def for_fidelity(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available fidelity's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """

    return workday_based_company(response, keyword, "https://wd1.myworkdaysite.com/en-US/recruiting/fmr/FidelityCareers", search_api_header, search_api_url, session)


def for_northwestern_mutual(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    """gets available fidelity's career page

    Args:
        keyword (str): keyword to match in job title
        search_api_url (str): search api url
        search_api_header (Dict): search api header
        response (Dict): response for initial query
        session (request): request session object
    Returns:
        Dict[str, Dict]: relevant jobs
    """

    return workday_based_company(response, keyword, "https://northwesternmutual.wd5.myworkdayjobs.com/CORPORATE-CAREERS", search_api_header, search_api_url, session)

# Greenhouse based Companies


def greenhouse_based_company(company_page_respone, company_job_keyword, session):
    relevant_jobs = {}
    soup = BeautifulSoup(company_page_respone.strip(), 'html.parser')
    available_jobs = soup.find_all("section", {"class": "level-0"})
    if len(available_jobs) > 0:
        for department_jobs in available_jobs:
            for job in department_jobs.contents:
                # check if department_jobs is div or not
                if job.name not in ['div', 'section']:
                    continue
                elif job.name == 'div':
                    job_title = job.text.strip()
                    job_semi_url = job.contents[1]["href"]
                elif job.name == 'section':
                    for sub_job in job.contents:
                        if sub_job.name == 'div':
                            job_title = sub_job.text.strip()
                            job_semi_url = sub_job.contents[1]["href"]
                            break
                job_id = job_semi_url.split("/")[-1]
                job_url = f'https://boards.greenhouse.io{job_semi_url}'
                if fuzz.ratio(job_title, company_job_keyword) > FUZZY_RATIO_MATCH:
                    ignore_position = False
                    for term in TERMS_TO_IGNORE:
                        if term in job_title:
                            ignore_position = True
                            break
                    if not ignore_position:
                        job_data_response = get_response_for_search_url(
                            "GET", job_url, session)
                        job_data_soup = BeautifulSoup(
                            job_data_response.strip(), 'html.parser')
                        job_data = job_data_soup.find_all(
                            "script", {"type": "application/ld+json"})
                        if len(job_data) > 0:
                            job_data = json.loads(job_data[0].text.strip())
                            job_location = job_data['jobLocation']['address']['addressLocality']
                            if job_location:
                                if ('United States' not in job_location) and ('US' not in job_location):
                                    continue
                            today = date.today()
                            posted_date = datetime.strptime(
                                job_data['datePosted'], "%Y-%m-%d").date()
                            date_difference = today - posted_date
                            if date_difference.days < DAYS_TO_CHECK:
                                relevant_jobs[job_id] = {
                                    'title': job_title, 'posted_date': posted_date,
                                    'apply': job_url}
    return relevant_jobs


# Lever Based Companies

def lever_based_company(company_page_respone, company_job_keyword, session, locations):
    relevant_jobs = {}
    soup = BeautifulSoup(company_page_respone.strip(), 'html.parser')
    available_jobs = soup.find_all("div", {"class": "posting"})
    if len(available_jobs) > 0:
        for job in available_jobs:
            # check if department_jobs is div or not
            job_url = job.contents[1]["href"]
            job_id = job_url.split("/")[-1]
            job_title = job.contents[1].text.split('-')[0].strip()
            if fuzz.ratio(job_title, company_job_keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    job_data_response = get_response_for_search_url(
                        "GET", job_url, session)
                    job_data_soup = BeautifulSoup(
                        job_data_response.strip(), 'html.parser')
                    job_data = job_data_soup.find_all(
                        "script", {"type": "application/ld+json"})
                    if len(job_data) > 0:
                        job_data = json.loads(job_data[0].text.strip())
                        job_location = job_data['jobLocation']['address']['addressLocality']
                        if job_location:
                            if job_location not in locations:
                                continue
                        today = date.today()
                        posted_date = datetime.strptime(
                            job_data['datePosted'], "%Y-%m-%d").date()
                        date_difference = today - posted_date
                        if date_difference.days < DAYS_TO_CHECK:
                            relevant_jobs[job_id] = {
                                'title': job_title, 'posted_date': posted_date,
                                'apply': job_url}
    return relevant_jobs


def for_plaid(company_page_respone, company_job_keyword, session):
    return lever_based_company(company_page_respone, company_job_keyword, session, ['United States', 'US', 'USA', 'United States of America', 'San Francisco', 'New York'])


def for_lucid(company_page_respone, company_job_keyword, session):
    return lever_based_company(company_page_respone, company_job_keyword, session, ['ATLANTA, GA', 'BEVERLY HILLS, CA', 'BOSTON, MA', 'CASA GRANDE, AZ', 'CHARLOTTE, NC', 'CHICAGO, IL', 'COLDWATER, MI', 'CORTE MADERA, CA', 'COSTA MESA, CA', 'DALLAS, TX', 'DENVER, CO', 'HOUSTON, TX', 'MANHASSET, NY', 'MCLEAN, VA', 'MIAMI, FL', 'MILLBRAE, CA', 'NASHVILLE, TN', 'NATICK, MA', 'NEW YORK CITY, NY', 'NEWARK, CA', 'NEWPORT BEACH, CA', 'OAK BROOK, IL', 'PLAINVIEW, NY', 'REMOTE', 'RIVIERA BEACH, FL', 'ROCKLIN, CA', 'SAN DIEGO, CA', 'SANTA CLARA, CA', 'SCOTTSDALE, AZ', 'SEATTLE, WA', 'SHORT HILLS, NJ', 'TEMPE, AZ', 'TORRANCE, CA', 'TROY, MI', 'WEST PALM BEACH, FL', 'WHITE PLAINS, NY'])

# SmartRecruiters Based Companies


def smartrecruiters_based_company(company_page_respone, company_job_keyword, session):
    relevant_jobs = {}
    soup = BeautifulSoup(company_page_respone.strip(), 'html.parser')
    available_jobs = soup.find_all("li", {"class": "opening-job"})
    if len(available_jobs) > 0:
        for job in available_jobs:
            if "href" not in job.contents[0].attrs:
                continue
            # check if department_jobs is div or not
            job_url = job.contents[0]["href"]
            job_id = job_url.split("=")[-1]
            job_title = job.contents[0].text.replace(
                'Full-time', '').split('-')[0].split('(')[0]
            if fuzz.ratio(job_title, company_job_keyword) > FUZZY_RATIO_MATCH:
                ignore_position = False
                for term in TERMS_TO_IGNORE:
                    if term in job_title:
                        ignore_position = True
                        break
                if not ignore_position:
                    job_data_response = get_response_for_search_url(
                        "GET", job_url, session)
                    job_data_soup = BeautifulSoup(
                        job_data_response.strip(), 'html.parser')
                    # get location
                    job_location_data = job_data_soup.find_all(
                        "meta", {"itemprop": "addressCountry"})
                    job_location = job_location_data[0]['content']
                    if job_location:
                        if job_location not in ['United States', 'US', 'USA', 'United States of America', 'San Francisco', 'New York']:
                            continue
                    # get posted date
                    job_date = job_data_soup.find_all(
                        "meta", {"itemprop": "datePosted"})
                    today = date.today()
                    posted_date = date.today()
                    if len(job_date) > 0:
                        posted_date = datetime.strptime(
                            job_date[0]['content'], "%Y-%m-%dT%H:%M:%S.%fZ").date()
                    date_difference = today - posted_date
                    if date_difference.days < DAYS_TO_CHECK:
                        relevant_jobs[job_id] = {
                            'title': job_title, 'posted_date': posted_date, 'apply': job_url}
    return relevant_jobs

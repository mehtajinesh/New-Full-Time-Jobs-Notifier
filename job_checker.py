import copy
import math
from typing import Dict, List
import urllib
import logging
from datetime import datetime, date
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
import json
from json import JSONDecodeError

from utils import get_past_date
from constants import FUZZY_RATIO_MATCH, DAYS_TO_CHECK, TERMS_TO_IGNORE


def get_relevant_jobs(company_name: str, search_api_type: str, search_api_url: str, keywords: List[str], search_api_header: Dict, session) -> Dict:
    """gets the relevant jobs from the company's career page

    Args:
        company_name (str): company name
        search_api_type (str): search api type
        search_api_url (str): search api url
        keywords (List[str]): list of keywords to search from
        search_api_header (Dict): search api header
        session (request): requests session object

    Returns:
        Dict: relevant jobs
    """
    relevant_jobs = {}
    try:
        for keyword in keywords:
            if search_api_type == "GET":
                # Push the keyword to the url (replace it with curly brackets)
                # Update the search url with the keywords
                search_api_url = search_api_url.replace(
                    "{}", urllib.parse.quote(keyword))
                # For each keyword, get the job details using keyword, api and headers
                logging.info(
                    f'Fetching data from {company_name} for keyword: {keyword} ...')
            else:
                search_api_header['searchText'] = keyword.replace(
                    " ", "+").lower()
                # For each keyword, get the job details using keyword, api and headers
                logging.info(
                    f'Fetching data from {company_name} for keyword: {keyword} ...')
            response = get_response_for_search_url(search_api_type,
                                                   search_api_url, session, search_api_header)
            if not response:
                return relevant_jobs
            if company_name == 'Amazon':
                relevant_jobs.update(for_amazon(keyword, response))
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
            elif company_name == 'Disney':
                relevant_jobs.update(for_disney(
                    keyword, search_api_url, response, session))
# Workday Based Banks
            elif company_name == 'BankOfAmerica':
                relevant_jobs.update(for_bank_of_america(
                    keyword, search_api_url, response, copy.deepcopy(search_api_header), session))
# Workday Based Tech Companies
            elif company_name == 'Adobe':
                relevant_jobs.update(for_adobe(
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

    except JSONDecodeError as e:
        logging.info(
            f'Looks like the company [ {company_name} ] career page is down. So will try later in 20 mins')
    return relevant_jobs


def get_response_for_search_url(search_type: str, search_api_url: str, session, search_api_header: Dict = ""):
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
        req = session.post(url=search_api_url, json=search_api_header)
        logging.info(
            f'Data fetched from search with response status code: '
            + str(req.status_code))
        if "text/html" in req.headers['Content-Type']:
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
            pages = math.ceil(total_jobs / 20)
            response_available_jobs = json_data['searchResults']
            url = json_data['fullUrl']
            response_relevant_jobs = get_relevant_jobs_from_page(
                response_available_jobs, keyword)
        return response_relevant_jobs, pages, url

    relevant_jobs, no_of_pages, org_url = get_relevant_jobs_from_html_response(
        response, keyword)
    if no_of_pages > 1:
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
                        'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://www.amazon.jobs/{job['job_path']}"}
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


def for_disney(keyword: str, search_api_url: str, response: Dict, session) -> Dict[str, Dict]:
    """gets the job information from disney's career page

    Args:
        keyword (str): keyword to match with job title
        search_api_url (str): search api url for disney's career page
        response (Dict): initial response from the search api url
        session (request): request session object 

    Returns:
        [str, Dict]: relevant jobs
    """
    # def get_relevant_jobs_from_json_response(page_response, keyword):
    #     page_relevant_jobs = {}
    #     page_html_response = page_response["results"].replace(
    #         "\n", "").replace("\r", "")
    #     soup = BeautifulSoup(page_html_response, 'html.parser')
    #     print(soup)
    # total_jobs = ["result"]["totalJobs"]
    # no_of_pages = math.ceil(total_jobs / 20)
    # page_available_jobs = page_response["operationResult"]["result"]["jobs"]
    # for job in page_available_jobs:
    #     if 'title' in job:
    #         job_id = job['jobId']
    #         curr_job_title = job['title']
    #         posted_date = datetime.strptime(
    #             job['postingDate'], "%Y-%m-%dT%H:%M:%S%z").date()
    #         today = date.today()
    #         if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
    #             ignore_position = False
    #             for term in TERMS_TO_IGNORE:
    #                 if term in curr_job_title:
    #                     ignore_position = True
    #                     break
    #             if not ignore_position:
    #                 date_difference = today - posted_date
    #                 if date_difference.days < DAYS_TO_CHECK:
    #                     page_relevant_jobs[job_id] = {
    #                         'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://careers.microsoft.com/us/en/job/{job_id}"}
    # return page_relevant_jobs, no_of_pages
    # relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
    #     response, keyword)
    # if no_of_pages > 1:
    #     curr_page_count = 2
    #     while (curr_page_count < min(5, no_of_pages)):
    #         new_url = search_api_url + f'&pg={curr_page_count}'
    #         new_response = get_response_for_search_url("GET", new_url, session)
    #         if not new_response:
    #             return relevant_jobs
    #         new_relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
    #             new_response, keyword)
    #         relevant_jobs.update(new_relevant_jobs)
    #         curr_page_count += 1
    relevant_jobs = {}
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

# Workday based Companies


def workday_based_company(company_page_respone, company_job_keyword, company_apply_link_prefix, search_api_header, search_api_url, session):
    def get_relevant_jobs_from_json_response(page_response, keyword, apply_link_prefix):
        page_relevant_jobs = {}
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

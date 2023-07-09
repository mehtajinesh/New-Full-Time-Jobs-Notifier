import math
from typing import Dict, List
import urllib
import logging
from datetime import datetime, date
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
import json

from utils import get_past_date
from constants import FUZZY_RATIO_MATCH, DAYS_TO_CHECK


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
        Dict: _description_
    """
    relevant_jobs = {}
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
            search_api_header['searchText'] = keyword.replace(" ", "+").lower()
            # For each keyword, get the job details using keyword, api and headers
            logging.info(
                f'Fetching data from {company_name} for keyword: {keyword} ...')
        response = get_response_for_search_url(search_api_type,
                                               search_api_url, session, search_api_header)
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
        if company_name == 'Nvidia':
            relevant_jobs.update(for_nvidia(
                keyword, search_api_url, response, search_api_header, session))

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
        if "text/html" in req.headers['Content-Type']:
            response = req.text
        else:
            response = req.json()
    return response


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
            date_difference = today - posted_date
            if date_difference.days < DAYS_TO_CHECK:
                relevant_jobs[job_id] = {
                    'title': curr_job_title, 'posted_date': posted_date, 'apply': job['url_next_step']}
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
            date_difference = today - posted_date
            if date_difference.days < DAYS_TO_CHECK:
                relevant_jobs[job_id] = {
                    'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://jobs.netflix.com/jobs/{job_id}"}
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
        while (curr_page_count < 3):
            new_url = org_url + f'&page={curr_page_count}'
            new_response = get_response_for_search_url("GET", new_url, session)
            new_relevant_jobs, no_of_pages, org_url = get_relevant_jobs_from_html_response(
                new_response, keyword)
            relevant_jobs.update(get_relevant_jobs_from_page(
                new_relevant_jobs, keyword))
            curr_page_count += 1
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
            job_id = job['jobId']
            curr_job_title = job['title']
            posted_date = datetime.strptime(
                job['postingDate'], "%Y-%m-%dT%H:%M:%S%z").date()
            today = date.today()
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                date_difference = today - posted_date
                if date_difference.days < DAYS_TO_CHECK:
                    page_relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://careers.microsoft.com/us/en/job/{job_id}"}
        return page_relevant_jobs, no_of_pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 2
        while (curr_page_count < no_of_pages + 1):
            new_url = search_api_url + f'&pg={curr_page_count}'
            new_response = get_response_for_search_url("GET", new_url, session)
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
            date_difference = today - posted_date
            if date_difference.days < DAYS_TO_CHECK:
                relevant_jobs[job_id] = {
                    'title': curr_job_title, 'posted_date': posted_date, 'apply': f"{job['PostURL']}"}
    return relevant_jobs


def for_nvidia(keyword: str, search_api_url: str, response: Dict, search_api_header: Dict, session) -> Dict[str, Dict]:
    def get_relevant_jobs_from_json_response(page_response, keyword):
        page_relevant_jobs = {}
        total_jobs = page_response["total"]
        no_of_pages = math.ceil(total_jobs / 20)
        page_available_jobs = page_response["jobPostings"]
        for job in page_available_jobs:
            job_id = job['bulletFields'][0]
            curr_job_title = job['title']
            posted_date = get_past_date(job['postedOn'].replace(
                "Posted ", "").replace("+", "").lower())
            today = date.today()
            if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
                date_difference = today - posted_date
                if date_difference.days < DAYS_TO_CHECK:
                    page_relevant_jobs[job_id] = {
                        'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite{job['externalPath']}"}
        return page_relevant_jobs, no_of_pages

    relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
        response, keyword)
    if no_of_pages > 1:
        curr_page_count = 2
        while (curr_page_count < 5):
            search_api_header['offset'] += 20
            new_response = get_response_for_search_url(
                "POST", search_api_url, session, search_api_header)
            new_relevant_jobs, no_of_pages = get_relevant_jobs_from_json_response(
                new_response, keyword)
            relevant_jobs.update(new_relevant_jobs)
            curr_page_count += 1
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
        job_id = job['Id']
        curr_job_title = job['Title']
        posted_date = datetime.strptime(
            job['PostedDate'], "%Y-%m-%dT%H:%M:%S%z").date()
        today = date.today()
        if fuzz.ratio(curr_job_title, keyword) > FUZZY_RATIO_MATCH:
            date_difference = today - posted_date
            if date_difference.days < DAYS_TO_CHECK:
                relevant_jobs[job_id] = {
                    'title': curr_job_title, 'posted_date': posted_date, 'apply': f"https://careers.oracle.com/jobs/#en/sites/jobsearch/job/{job_id}"}
    return relevant_jobs

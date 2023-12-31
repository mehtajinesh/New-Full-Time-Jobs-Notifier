import os

# Known Data
DATA_FOLDER_LOCATION = os.path.join(os.getcwd(),'data')
COMPANY_NAMES_CSV = 'company_data.csv'
COMPANY_SEARCH_API_CSV = 'search_api.csv'
COMPANY_KEYWORDS_CSV = 'keywords.csv'
COMPANY_KNOWN_JOBS_CSV = 'already_known_jobs.csv'
COMPANY_SEARCH_API_HEADER_CSV = 'search_headers.csv'
COMPANY_STATUS_CSV = 'company_status.csv'
COMPANY_SEARCH_API_EXTRA_HEADER_CSV = 'search_extra_headers.csv'

# Log File Location
LOG_FOLDER_LOCATION = os.path.join(os.getcwd(), "log")
LOG_FILE_NAME = "log.log"
SLACK_DEPLOYMENT_NOTIFICATION_WEBHOOK_VAR = 'SLACK_DEPLOYMENT_NOTIFICATION_WEBHOOK'
SLACK_ERROR_NOTIFICATION_WEBHOOK_VAR = 'SLACK_ERROR_NOTIFICATION_WEBHOOK'
SLACK_JOB_NOTIFICATION_WEBHOOK_VAR = 'SLACK_JOB_NOTIFICATION_WEBHOOK'

FUZZY_RATIO_MATCH = 50
DAYS_TO_CHECK = 7

# Terms to Ignore
TERMS_TO_IGNORE = [
    "Embedded",
    "Manager",
    "Principal",
    "Staff",
    "Compiler",
    "Enterprise",
    "Linux",
    "Site",
    "Facilities",
    "Security",
    "AV",
    "LMTS",
    "AMTS",
    "PMTS",
    "Internship",
    "Infrastructure",
    "SMTS",
    "Intern",
    "Co-op",
    "Mechanical",
    "Director",
    "Lead",
    "Data Engineer",
    "Sales"
]

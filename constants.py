import os

# Slack Web Hooks
SLACK_JOB_NOTIFICATION_WEBHOOK = "https://hooks.slack.com/services/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"
SLACK_ERROR_NOTIFICATION_WEBHOOK = "https://hooks.slack.com/services/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"
SLACK_DEPLOYMENT_NOTIFICATION_WEBHOOK = "https://hooks.slack.com/services/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"

# Known Data
DATA_FOLDER = '/home/jineshmehta/new-jobs-notifier/data'
COMPANY_NAMES_CSV = os.path.join(DATA_FOLDER, 'company_data.csv')
COMPANY_SEARCH_API_CSV = os.path.join(DATA_FOLDER, 'search_api.csv')
COMPANY_KEYWORDS_CSV = os.path.join(DATA_FOLDER, 'keywords.csv')
COMPANY_KNOWN_JOBS_CSV = os.path.join(DATA_FOLDER, 'already_known_jobs.csv')
COMPANY_SEARCH_API_HEADER_CSV = os.path.join(DATA_FOLDER, 'search_headers.csv')

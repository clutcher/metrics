from .defaults import *

# Application deployment setup
METRICS_BASE_URL = env.str('METRICS_BASE_URL', default='')
METRICS_BASIC_AUTH_USERS = env.json('METRICS_BASIC_AUTH_USERS', default=None)

# Task tracker
METRICS_TASK_TRACKER = env.str('METRICS_TASK_TRACKER', default='jira')

METRICS_AZURE_ORGANIZATION_URL = env.str('METRICS_AZURE_ORGANIZATION_URL', default=None)
METRICS_AZURE_PAT = env.str('METRICS_AZURE_PAT', default=None)

METRICS_JIRA_SERVER_URL = env.str('METRICS_JIRA_SERVER_URL', default=None)
METRICS_JIRA_EMAIL = env.str('METRICS_JIRA_EMAIL', default=None)
METRICS_JIRA_API_TOKEN = env.str('METRICS_JIRA_API_TOKEN', default=None)

# Status codes

METRICS_IN_PROGRESS_STATUS_CODES = env.list('METRICS_IN_PROGRESS_STATUS_CODES',
                                            default=['Analysis', 'Active', 'In Progress', 'In Development', 'QA',
                                                     'Validation', 'Testing', 'Review'])
METRICS_PENDING_STATUS_CODES = env.list('METRICS_PENDING_STATUS_CODES',
                                        default=['Blocked', 'On Hold', 'Pending', 'Waiting'])
METRICS_DONE_STATUS_CODES = env.list('METRICS_DONE_STATUS_CODES', default=['Done', 'Closed', 'Resolved'])

# Recently finished tasks configuration
METRICS_RECENTLY_FINISHED_TASKS_DAYS = env.int('METRICS_RECENTLY_FINISHED_TASKS_DAYS', default=14)

# Filters
METRICS_PROJECT_KEYS = env.list('METRICS_PROJECT_KEYS', default=None)

METRICS_GLOBAL_TASK_TYPES_FILTER = env.list('METRICS_GLOBAL_TASK_TYPES_FILTER', default=None)
METRICS_GLOBAL_TEAM_FILTER = env.list('METRICS_GLOBAL_TEAM_FILTER', default=None)
METRICS_EPIC_FILTER_ID = env.str('METRICS_EPIC_FILTER_ID', default='179788')

# Calculations
METRICS_STORY_POINT_CUSTOM_FIELD_ID = env.str('METRICS_STORY_POINT_CUSTOM_FIELD_ID', default=None)

METRICS_WORKING_DAYS_PER_MONTH = env.int('METRICS_WORKING_DAYS_PER_MONTH', default=22)
METRICS_IDEAL_HOURS_PER_DAY = env.float('METRICS_IDEAL_HOURS_PER_DAY', default=4.0)
METRICS_STORY_POINTS_TO_IDEAL_HOURS_CONVERTION_RATIO = env.float('METRICS_STORY_POINTS_TO_IDEAL_HOURS_CONVERTION_RATIO',
                                                                 default=1.0)

# Fallback values when missing
METRICS_DEFAULT_STORY_POINTS_VALUE_WHEN_MISSING = env.int('METRICS_DEFAULT_STORY_POINTS', default=None)
METRICS_DEFAULT_SENIORITY_LEVEL_WHEN_MISSING = env.str('METRICS_DEFAULT_SENIORITY_LEVEL_WHEN_MISSING', default='middle')
METRICS_DEFAULT_HEALTH_STATUS_WHEN_MISSING = env.str('METRICS_DEFAULT_HEALTH_STATUS_WHEN_MISSING', default='GREEN')

METRICS_MEMBER_GROUP_WHEN_MISSING = env.str('METRICS_MEMBER_GROUP_WHEN_MISSING', default=None)

# Velocity time unit configuration
METRICS_DEFAULT_VELOCITY_TIME_UNIT = env.str('METRICS_DEFAULT_VELOCITY_TIME_UNIT', default='DAY')

# Dev velocity stage configuration
METRICS_DEV_VELOCITY_STAGE = env.str('METRICS_DEV_VELOCITY_STAGE', default='Development')

CACHES['task_search_results'] = {
    'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
    'LOCATION': '/tmp/metrics_task_search_cache',
    "OPTIONS": {"MAX_ENTRIES": 100000},
    'TIMEOUT': 300
}

METRICS_SENIORITY_LEVELS = env.dict('METRICS_SENIORITY_LEVELS', default={
    'senior': 1.0,
    'middle': 2.0,
    'junior': 4.0,
}, subcast=float)

METRICS_STAGES = env.json('METRICS_STAGES', default={
    'Analysis': ['Analysis'],
    'Development': ['Active', 'In Progress', 'In Development', 'Review'],
    'Validation': ['QA', 'Validation', 'Testing'],
    'Recently Finished': ['Done', 'Closed', 'Resolved'],
    'Pending': ['Blocked', 'On Hold', 'Pending', 'Waiting'],
})

METRICS_MEMBERS = env.json('METRICS_MEMBERS', default={})

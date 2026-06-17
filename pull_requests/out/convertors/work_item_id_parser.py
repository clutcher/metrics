import re
from typing import Optional

_AZURE_EXPLICIT_MENTION = re.compile(r'AB#(\d+)', re.IGNORECASE)
_AZURE_HASH_MENTION = re.compile(r'#(\d+)')
_AZURE_BRANCH_NUMBER = re.compile(r'(?:^|[/_-])(\d{2,})(?:[/_-]|$)')
_JIRA_ISSUE_KEY = re.compile(r'\b([A-Z][A-Z0-9]+-\d+)\b')


class WorkItemIdParser:

    @staticmethod
    def parse_azure_work_item_id(source_branch: Optional[str], title: Optional[str]) -> Optional[str]:
        title_text = title or ''
        explicit_mention = _AZURE_EXPLICIT_MENTION.search(title_text) or _AZURE_HASH_MENTION.search(title_text)
        if explicit_mention:
            return explicit_mention.group(1)

        branch_leaf = WorkItemIdParser._branch_leaf(source_branch)
        branch_number = _AZURE_BRANCH_NUMBER.search(branch_leaf)
        if branch_number:
            return branch_number.group(1)

        return None

    @staticmethod
    def parse_jira_issue_key(source_branch: Optional[str], title: Optional[str]) -> Optional[str]:
        branch_leaf = WorkItemIdParser._branch_leaf(source_branch)
        for text in (branch_leaf, title or ''):
            issue_key = _JIRA_ISSUE_KEY.search(text.upper())
            if issue_key:
                return issue_key.group(1)
        return None

    @staticmethod
    def _branch_leaf(source_branch: Optional[str]) -> str:
        if not source_branch:
            return ''
        return source_branch.replace('refs/heads/', '')

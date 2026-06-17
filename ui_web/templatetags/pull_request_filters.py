from django import template

register = template.Library()

_MAIN_TIER = 'main'


@register.filter
def main_approvals(approvals):
    return [approval for approval in approvals if approval.tier == _MAIN_TIER]


@register.filter
def additional_approvals(approvals):
    return [approval for approval in approvals if approval.tier != _MAIN_TIER]

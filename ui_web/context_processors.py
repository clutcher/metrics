from .container import ui_web_container


def member_groups(request):
    if request.headers.get('HX-Request'):
        return {}
    
    try:
        tasks_facade = ui_web_container.tasks_facade
        available_member_groups = tasks_facade.get_available_member_groups()
        return {
            'global_available_member_groups': available_member_groups
        }
    except Exception:
        return {
            'global_available_member_groups': []
        }
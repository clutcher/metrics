from ..data.task_forecast_data import TaskForecastRequestData


class TaskForecastConvertor:

    @staticmethod
    def extract_request_data_from_request(request) -> TaskForecastRequestData:
        if request.method == 'POST':
            return TaskForecastRequestData(
                task_id=request.POST.get('task_id'),
                start_date=request.POST.get('start_date'),
                member_group=request.POST.get('member_group') or None
            )
        else:
            return TaskForecastRequestData(
                task_id=request.GET.get('task_id'),
                start_date=request.GET.get('start_date'),
                member_group=request.GET.get('member_group')
            )

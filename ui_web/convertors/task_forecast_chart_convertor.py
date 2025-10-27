from datetime import datetime, timedelta
from typing import List, Optional

from django.conf import settings

from ..data.chart_data import ChartData, ChartDatasetData
from ..data.task_data import TaskData
from ..utils.color_utils import ColorUtils
from ..utils.task_forecast_chart_utils import TaskForecastChartUtils


class TaskForecastChartConvertor:

    def convert_task_data_list_to_chart(self, task_data_list: List[TaskData]) -> Optional[ChartData]:
        if not task_data_list:
            return None
        
        chart_tasks = []
        for task_data in task_data_list:
            chart_tasks.append(task_data)
            if task_data.child_tasks:
                chart_tasks.extend(child for child in task_data.child_tasks 
                                 if TaskForecastChartUtils._is_task_data_active(child))
        
        chart_data_dict = self._prepare_chart_data_from_task_data(chart_tasks)
        
        datasets = [
            ChartDatasetData(
                label=dataset.get('label', ''),
                data=dataset.get('data', []),
                border_color=dataset.get('borderColor'),
                background_color=dataset.get('backgroundColor'),
                border_width=dataset.get('borderWidth'),
                fill=dataset.get('fill'),
                point_radius=dataset.get('pointRadius')
            )
            for dataset in chart_data_dict.get('datasets', [])
        ]
        
        return ChartData(
            labels=chart_data_dict.get('labels', []),
            datasets=datasets,
            min_date=chart_data_dict.get('min_date'),
            max_date=chart_data_dict.get('max_date')
        )

    def _prepare_chart_data_from_task_data(self, task_data_list: List[TaskData]):
        chart_date_range = self._calculate_chart_date_range_from_task_data(task_data_list)
        chart_datasets = self._build_chart_datasets_from_task_data(task_data_list)
        
        return {
            'labels': [dataset['label'] for dataset in chart_datasets],
            'datasets': chart_datasets,
            'min_date': chart_date_range['min_date'].isoformat(),
            'max_date': chart_date_range['max_date'].isoformat()
        }

    @staticmethod
    def _calculate_chart_date_range_from_task_data(task_data_list: List[TaskData]):
        task_dates = []
        for task_data in task_data_list:
            if task_data.forecast and task_data.forecast.start_date and task_data.forecast.end_date:
                try:
                    start_date = datetime.fromisoformat(task_data.forecast.start_date.replace('Z', '+00:00'))
                    end_date = datetime.fromisoformat(task_data.forecast.end_date.replace('Z', '+00:00'))
                    task_dates.extend([start_date, end_date])
                except:
                    pass

        if not task_dates:
            current_date = datetime.now().date()
            return {
                'min_date': current_date - timedelta(days=7),
                'max_date': current_date + timedelta(days=7)
            }

        min_task_date = min(task_dates)
        max_task_date = max(task_dates)
        
        return {
            'min_date': min_task_date - timedelta(days=7),
            'max_date': max_task_date + timedelta(days=7)
        }

    def _build_chart_datasets_from_task_data(self, task_data_list: List[TaskData]):
        time_unit_abbrev = self._get_time_unit_abbreviation(settings.METRICS_DEFAULT_VELOCITY_TIME_UNIT)
        chart_datasets = []
        
        for task_index, task_data in enumerate(task_data_list):
            if self._task_data_has_forecast_dates(task_data):
                dataset = self._create_task_data_chart_dataset(task_data, task_index, len(task_data_list), time_unit_abbrev)
                chart_datasets.append(dataset)
        
        return chart_datasets

    @staticmethod
    def _task_data_has_forecast_dates(task_data: TaskData) -> bool:
        return (task_data.forecast and 
                task_data.forecast.start_date and
                task_data.forecast.end_date)

    @staticmethod
    def _create_task_data_chart_dataset(task_data: TaskData, task_index: int, total_tasks: int, time_unit_abbrev: str):
        estimation_hours = 0.0
        if task_data.forecast and task_data.forecast.estimation_time_days:
            estimation_hours = task_data.forecast.estimation_time_days * 8.0
            
        task_label = f"{task_data.id}: {task_data.title} ({estimation_hours:.1f}{time_unit_abbrev})"
        task_y_position = total_tasks - task_index
        task_color = ColorUtils.generate_color(task_data.id)

        return {
            'label': task_label,
            'data': [
                {
                    'x': task_data.forecast.start_date,
                    'y': task_y_position
                },
                {
                    'x': task_data.forecast.end_date,
                    'y': task_y_position
                }
            ],
            'fill': False,
            'borderColor': task_color,
            'backgroundColor': task_color,
            'borderWidth': 15,
            'pointRadius': 0
        }

    @staticmethod
    def _get_time_unit_abbreviation(time_unit_name: str) -> str:
        abbreviations = {
            'SECOND': 's',
            'HOUR': 'h',
            'DAY': 'd',
            'WEEK': 'w',
            'MONTH': 'm'
        }
        return abbreviations.get(time_unit_name.upper(), 'h')


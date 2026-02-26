from datetime import datetime
from typing import List

from ui_web.data.chart_data import ChartData


class VelocitySortUtils:

    @staticmethod
    def sort_chart_data_chronologically(chart: ChartData, ascending: bool = True) -> ChartData:
        try:
            sorted_indices = sorted(
                range(len(chart.labels)),
                key=lambda i: datetime.strptime(chart.labels[i], '%Y-%m'),
                reverse=not ascending
            )
        except ValueError:
            sorted_indices = sorted(
                range(len(chart.labels)),
                key=lambda i: chart.labels[i],
                reverse=not ascending
            )

        chart.labels = [chart.labels[i] for i in sorted_indices]
        for dataset in chart.datasets:
            dataset.data = [dataset.data[i] for i in sorted_indices]

        return chart

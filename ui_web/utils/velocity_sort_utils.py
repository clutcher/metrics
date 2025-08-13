from datetime import datetime
from typing import List


class VelocitySortUtils:

    @staticmethod
    def sort_chart_labels_chronologically(labels: List[str], ascending: bool = True) -> List[str]:
        try:
            return sorted(
                labels,
                key=lambda label: datetime.strptime(label, '%Y-%m'),
                reverse=not ascending
            )
        except ValueError:
            return sorted(labels, reverse=not ascending)

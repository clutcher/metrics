from dataclasses import dataclass
from typing import List, Union, Optional


@dataclass(slots=True)
class ChartDatasetData:
    label: str
    data: List[Union[float, int]]
    color: Optional[str] = None
    background_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: Optional[int] = None
    fill: Optional[bool] = None
    point_radius: Optional[int] = None


@dataclass(slots=True)
class ChartData:
    labels: List[str]
    datasets: List[ChartDatasetData]
    min_date: Optional[str] = None
    max_date: Optional[str] = None
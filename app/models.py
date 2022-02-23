
from typing import List

class KFK:
    @classmethod
    def generate(cls, csa_file_path):
        pass

class GameAnalysis:
    kif: str
    score_list: list
    engine_name: str
    time_per_move: int
    analysis_score_list: list
    analysis_info_list: List['AnalysisInfo']


class AnalysisInfo:
    move: str
    score: str
    pv: str

"""
Docs:
https://github.com/yaneurao/YaneuraOu/blob/master/docs/USI%E6%8B%A1%E5%BC%B5%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89.txt

Default setup reference:
https://yaneuraou.yaneu.com/2018/11/03/%E3%82%84%E3%81%AD%E3%81%86%E3%82%89%E7%8E%8B%E3%81%AE%E6%A4%9C%E8%A8%8E%E7%94%A8%E8%A8%AD%E5%AE%9A%E3%81%AE%E3%81%8A%E5%8B%A7%E3%82%81%E3%82%92%E6%95%99%E3%81%88%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95/ 
"""

class EngineOptions:
    hash_key: str = "Hash"
    threads_key: str = "Threads"
    network_delay_key: str = "NetworkDelay"
    network_delay2_key: str = "NetworkDelay2"
    max_moves_to_draw_key: str = "MaxMovesToDraw"
    minimum_thinking_time_key: str = "MinimumThinkingTime"

    def __init__(
        self,
        hash: int = 128,
        threads: int = 4,
        network_delay: int = 300,
        network_delay2: int = 500, # reference: "https://yaneuraou.yaneu.com/2018/08/31/networkdelaynetworkdelay2%e3%81%ae%e3%83%87%e3%83%95%e3%82%a9%e3%83%ab%e3%83%88%e5%80%a4%e3%81%af%e4%bd%95%e6%95%850%e3%81%a7%e3%81%af%e3%81%aa%e3%81%84%e3%81%ae%e3%81%a7%e3%81%99%e3%81%8b%ef%bc%9f/"
        max_moves_to_draw: int = 0,
        minimum_thinking_time: int = 1000
    ):
        self.hash_val: int = hash
        self.threads_val: int = threads
        self.network_delay_val: int = network_delay
        self.network_delay2_val: int = network_delay2
        self.max_moves_to_draw_key: int = max_moves_to_draw
        self.minimum_thinking_time_key: int = minimum_thinking_time
    
    def yaneura_ou(self):
        return self._output()

    def suisho(self):
        self.hash_key = "USI_Hash"
        return self._output()

    def _output(self):
        return {
            self.hash_key: str(self.hash_val),
            self.threads_key: str(self.threads_val),
            self.network_delay_key: str(self.network_delay_val),
            self.network_delay2_key: str(self.network_delay2_val),
        }
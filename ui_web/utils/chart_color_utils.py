import hashlib


class ChartColorUtils:
    RED_PASTEL = "hsl(0, 70%, 72%, 0.8)"
    
    @staticmethod
    def generate_color_from_string(input_str: str) -> str:
        digest = hashlib.md5(input_str.encode()).digest()
        hue = int.from_bytes(digest[0:2], "big") % 360
        saturation = 55 + (digest[2] % 21)
        lightness = 65 + (digest[3] % 16)
        return f"hsl({hue}, {saturation}%, {lightness}%, 0.8)"
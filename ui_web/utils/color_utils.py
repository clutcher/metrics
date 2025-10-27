import hashlib


class ColorUtils:
    RED_PASTEL = "hsl(0, 70%, 72%, 0.8)"

    @staticmethod
    def generate_color(input_str: str) -> str:
        if not input_str:
            input_str = "default"

        hash_bytes = hashlib.sha256(input_str.encode('utf-8')).digest()

        hue = int.from_bytes(hash_bytes[0:2], byteorder='big') % 360
        saturation = 40 + (int.from_bytes(hash_bytes[2:3], byteorder='big') % 20)
        lightness = 45 + (int.from_bytes(hash_bytes[3:4], byteorder='big') % 10)

        return f"hsl({hue}, {saturation}%, {lightness}%)"
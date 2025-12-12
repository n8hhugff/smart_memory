# compression_factory.py
from huffman_compression import HuffmanCompression

class CompressionFactory:
    @staticmethod
    def get(name="huffman"):
        if name.lower() == "huffman":
            return HuffmanCompression()
        # future: add LZW, RLE, etc.
        raise ValueError(f"Unknown compression algorithm: {name}")

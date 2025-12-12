# huffman_compression.py
import heapq
from collections import Counter, namedtuple
import pickle
import math
import os

# Node for Huffman tree
class Node(namedtuple("Node", ["char", "freq", "left", "right"])):
    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanCompression:
    def __init__(self):
        self.codes = {}
        self.reverse_codes = {}

    def build_tree(self, text: str):
        if not text:
            return None
        frequency = Counter(text)
        heap = [Node(ch, fr, None, None) for ch, fr in frequency.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            merged = Node(None, left.freq + right.freq, left, right)
            heapq.heappush(heap, merged)
        return heap[0]

    def generate_codes(self, node, current_code=""):
        if node is None:
            return
        if node.char is not None:
            self.codes[node.char] = current_code or "0"  # handle single-char edge case
            self.reverse_codes[current_code or "0"] = node.char
            return
        self.generate_codes(node.left, current_code + "0")
        self.generate_codes(node.right, current_code + "1")

    def compress(self, text: str):
        if not text:
            return b"", None, 0.0
        root = self.build_tree(text)
        self.codes.clear()
        self.reverse_codes.clear()
        self.generate_codes(root)
        encoded_text = ''.join(self.codes[ch] for ch in text)
        # pad to full byte
        padding = (8 - len(encoded_text) % 8) % 8
        encoded_text_padded = encoded_text + "0" * padding
        b = bytearray()
        for i in range(0, len(encoded_text_padded), 8):
            byte = encoded_text_padded[i:i+8]
            b.append(int(byte, 2))
        compression_ratio = (1 - len(b) / max(1, len(text.encode('utf-8')))) * 100
        print(f"📦 Compression Complete → {round(compression_ratio,2)}% reduction (approx).")
        return bytes(b), root, round(compression_ratio, 2), padding

    def decompress(self, data_bytes: bytes, root, padding=0):
        if not data_bytes or root is None:
            return ""
        bit_str = ''.join(f"{byte:08b}" for byte in data_bytes)
        if padding:
            bit_str = bit_str[:-padding]
        decoded = []
        node = root
        for bit in bit_str:
            node = node.left if bit == "0" else node.right
            if node.char:
                decoded.append(node.char)
                node = root
        return ''.join(decoded)

    # --- Save / Load tree (pickle) ---
    def save_tree(self, root, filename):
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "wb") as f:
            pickle.dump(root, f)
        print(f"💾 Huffman tree saved to {filename}")

    def load_tree(self, filename):
        if not os.path.exists(filename):
            print(f"⚠️ Huffman tree file {filename} not found.")
            return None
        with open(filename, "rb") as f:
            root = pickle.load(f)
        print(f"📂 Huffman tree loaded from {filename}")
        return root

    # --- Convenience: compress file / decompress file ---
    def compress_file(self, input_path, out_path, tree_path=None):
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()
        compressed_bytes, root, ratio, padding = self.compress(text)
        # write bytes with a small header (4 bytes padding)
        with open(out_path, "wb") as f:
            f.write(bytes([padding]))  # store padding in first byte
            f.write(compressed_bytes)
        if tree_path and root:
            self.save_tree(root, tree_path)
        return out_path, ratio

    def decompress_file(self, in_path, tree_path, out_path):
        with open(in_path, "rb") as f:
            padding = f.read(1)[0]
            data_bytes = f.read()
        root = self.load_tree(tree_path)
        text = self.decompress(data_bytes, root, padding)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        return out_path

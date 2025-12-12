import random
import json
import time
import os
from dataclasses import dataclass, asdict, field
from typing import List, Optional

@dataclass
class MemoryBlock:
    size: int
    is_allocated: bool = False
    data: Optional[str] = None
    last_used: float = field(default_factory=lambda: 0.0)
    use_count: int = 0

    def repr(self):
        status = "Used" if self.is_allocated else "Free"
        label = f" ({self.data})" if self.data else ""
        return f"[{status}:{self.size}KB{label}]"


class MemoryManager:
    def __init__(self, total_blocks=12, min_size=16, max_size=128):
        self.memory: List[MemoryBlock] = [
            MemoryBlock(random.randint(min_size, max_size)) for _ in range(total_blocks)
        ]
        os.makedirs("data", exist_ok=True)

    # --------------------------
    # تحسين: دمج الكتل الحرة
    # --------------------------
    def merge_free_blocks(self):
        i = 0
        while i < len(self.memory) - 1:
            if not self.memory[i].is_allocated and not self.memory[i+1].is_allocated:
                self.memory[i].size += self.memory[i+1].size
                del self.memory[i+1]
            else:
                i += 1

    # ----------------------------------------
    # تخصيص مع تحسين: تقسيم الكتل الكبيرة
    # ----------------------------------------
    def _allocate_block(self, block: MemoryBlock, label: str, requested_size=None):
        if requested_size is None:
            requested_size = block.size

        # تقسيم block إذا كان أكبر من المطلوب
        if block.size > requested_size:
            remaining_size = block.size - requested_size
            block.size = requested_size

            new_block = MemoryBlock(size=remaining_size, is_allocated=False)
            index = self.memory.index(block)
            self.memory.insert(index + 1, new_block)

        # تخصيص البلوك
        block.is_allocated = True
        block.data = label
        block.last_used = time.time()
        block.use_count += 1

    # ----------------------------------------
    # First Fit
    # ----------------------------------------
    def first_fit(self, data_size_kb, data_label="Data"):
        for block in self.memory:
            if not block.is_allocated and block.size >= data_size_kb:
                self._allocate_block(block, data_label, data_size_kb)
                print(f"✅ First Fit → Allocated {data_label} ({data_size_kb}KB).")
                self.merge_free_blocks()
                return True
        print(f"❌ First Fit → No suitable block found for {data_label}.")
        return False

    # ----------------------------------------
    # Best Fit
    # ----------------------------------------
    def best_fit(self, data_size_kb, data_label="Data"):
        best_block = None
        min_diff = float('inf')
        for block in self.memory:
            if not block.is_allocated and block.size >= data_size_kb:
                diff = block.size - data_size_kb
                if diff < min_diff:
                    min_diff = diff
                    best_block = block
        if best_block:
            self._allocate_block(best_block, data_label, data_size_kb)
            print(f"✅ Best Fit → Allocated {data_label} ({data_size_kb}KB).")
            self.merge_free_blocks()
            return True
        print(f"❌ Best Fit → No suitable block found for {data_label}.")
        return False

    # ----------------------------------------
    # Free block
    # ----------------------------------------
    def free_block(self, data_label):
        for block in self.memory:
            if block.data == data_label:
                block.is_allocated = False
                block.data = None
                block.last_used = 0.0
                block.use_count = 0
                print(f"♻️ Freed block containing {data_label}.")
                self.merge_free_blocks()
                return True
        print(f"⚠️ No block found with label {data_label}.")
        return False

    # ----------------------------------------
    # Usage / info
    # ----------------------------------------
    def memory_usage(self):
        used = sum(block.size for block in self.memory if block.is_allocated)
        total = sum(block.size for block in self.memory)
        return round((used / total) * 100, 2) if total else 0.0

    def total_used_blocks(self):
        return sum(1 for b in self.memory if b.is_allocated)

    def total_free_blocks(self):
        return sum(1 for b in self.memory if not b.is_allocated)

    def report(self):
        print("Memory Blocks:")
        print(" | ".join(block.repr() for block in self.memory))
        print(f"Used: {self.total_used_blocks()} | Free: {self.total_free_blocks()} | Efficiency: {self.memory_usage()}%")

    # ----------------------------------------
    # Defragmentation (simple)
    # ----------------------------------------
    def defragment(self):
        used = [b for b in self.memory if b.is_allocated]
        free = [b for b in self.memory if not b.is_allocated]
        self.memory = used + free
        print("🧹 Defragmentation complete.")

    # ----------------------------------------
    # LRU
    # ----------------------------------------
    def evict_lru(self):
        used = [b for b in self.memory if b.is_allocated]
        if not used:
            return False
        victim = min(used, key=lambda b: b.last_used or float('inf'))
        label = victim.data
        self.free_block(label)
        print(f"🗑️ Evicted (LRU) block: {label}")
        return True

    # ----------------------------------------
    # LFU
    # ----------------------------------------
    def evict_lfu(self):
        used = [b for b in self.memory if b.is_allocated]
        if not used:
            return False
        victim = min(used, key=lambda b: b.use_count)
        label = victim.data
        self.free_block(label)
        print(f"🗑️ Evicted (LFU) block: {label}")
        return True

    # ----------------------------------------
    # Save / Load
    # ----------------------------------------
    def save_state(self, filename="data/memory_state.json"):
        data = [asdict(b) for b in self.memory]
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Memory state saved to {filename}")

    def load_state(self, filename="data/memory_state.json"):
        if not os.path.exists(filename):
            print(f"⚠️ File not found: {filename}")
            return False
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.memory = [MemoryBlock(**item) for item in data]
        print(f"📂 Memory state loaded from {filename}")
        return True

    # ----------------------------------------
    # Allocate with eviction
    # ----------------------------------------
    def allocate_with_policy(self, data_size_kb, label, fit_method="best", eviction_policy="lru", max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            ok = self.best_fit(data_size_kb, label) if fit_method == "best" else self.first_fit(data_size_kb, label)
            if ok:
                return True

            evicted = self.evict_lru() if eviction_policy == "lru" else self.evict_lfu()
            if not evicted:
                break
            attempts += 1

        print("❌ Allocation failed after eviction attempts.")
        return False

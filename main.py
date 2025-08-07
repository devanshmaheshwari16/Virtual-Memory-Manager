from flask import Flask, render_template, request, jsonify
from collections import deque

app = Flask(__name__)

TOTAL_FRAMES = 10
memory = [None] * TOTAL_FRAMES
free_frames = list(range(TOTAL_FRAMES))
page_table = {}

class FIFO:
    def __init__(self, capacity):
        self.queue = deque()
        self.frames = set()
        self.capacity = capacity

    def reference(self, page):
        hit = page in self.frames
        if not hit:
            if len(self.frames) >= self.capacity:
                old = self.queue.popleft()
                self.frames.remove(old)
            self.frames.add(page)
            self.queue.append(page)
        return hit

fifo = FIFO(3)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/allocate', methods=['POST'])
def allocate():
    data = request.json
    pid = int(data['pid'])
    pages = int(data['pages'])
    allocated = 0
    for i in range(pages):
        if free_frames:
            frame = free_frames.pop(0)
            memory[frame] = (pid, i)
            page_table.setdefault(pid, []).append((i, frame))
            allocated += 1
    return jsonify({"allocated": allocated})

@app.route('/deallocate', methods=['POST'])
def deallocate():
    data = request.json
    pid = int(data['pid'])
    deallocated = 0
    for i in range(len(memory)):
        if memory[i] and memory[i][0] == pid:
            memory[i] = None
            deallocated += 1
    page_table.pop(pid, None)
    recalc_free()
    return jsonify({"deallocated": deallocated})

@app.route('/fragmentation')
def fragmentation():
    holes = [i for i, val in enumerate(memory) if val is None]
    percent = (len(holes) / TOTAL_FRAMES) * 100
    return jsonify({"holes": holes, "percent": round(percent, 2)})

@app.route('/compact')
def compact():
    global memory
    memory = [cell for cell in memory if cell is not None]
    memory += [None] * (TOTAL_FRAMES - len(memory))
    recalc_free()
    return jsonify({"status": "compacted"})

@app.route('/simulate_fifo')
def simulate_fifo():
    sequence = [1, 2, 3, 2, 1, 4, 5, 1]
    log = []
    for page in sequence:
        result = "HIT" if fifo.reference(page) else "MISS"
        log.append(f"Page {page}: {result}")
    return jsonify({"log": log, "frames": list(fifo.queue)})

@app.route('/status')
def status():
    return jsonify({"memory": memory})

def recalc_free():
    global free_frames
    free_frames = [i for i, val in enumerate(memory) if val is None]

if __name__ == "__main__":
    app.run(debug=True)

# main.py
import threading
import time
import liveliness
from gui import create_gui

gui = None
_engine_running = False

def _read_ui_settings():
    s = {}
    s["ear_threshold"] = gui["ear_slider"].get()
    s["pupil_move_threshold"] = gui["move_slider"].get()
    s["iris_edge_threshold"] = gui["edge_slider"].get()
    s["blink_frames_required"] = int(gui["events_slider"].get())
    return s

def start_liveliness():
    global _engine_running
    if _engine_running:
        return
    _engine_running = True
    gui["status_label"].config(text="Iris Scan Running...", fg="#00ff7a")
    settings = _read_ui_settings()
    # start the engine using GUI labels for live updates
    liveliness.start_liveliness(settings=settings,
                                status_label=gui["status_label"],
                                footer_label=gui["stats_label"],
                                cam_index=0)

def stop_liveliness():
    global _engine_running
    if not _engine_running:
        return
    _engine_running = False
    liveliness.stop_liveliness()
    time.sleep(0.25)  # tiny settle
    stats = liveliness.get_final_stats()
    gui["status_label"].config(text="Scan Stopped", fg="#ffaa00")
    contraction_display = stats["contraction"] if stats["contraction"] is not None else "--"
    gui["stats_label"].config(
        text=f"Blinks: {stats['blinks']}    Pupil Moves: {stats['moves']}    Iris Edge Events: {stats['edges']}    Iris Contraction: {contraction_display}"
    )

if __name__ == "__main__":
    gui = create_gui(start_liveliness, stop_liveliness)
    gui["root"].mainloop()

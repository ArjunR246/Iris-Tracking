# gui.py
import tkinter as tk
from tkinter import font

# ------------------ Updated SimpleSlider ------------------
class SimpleSlider(tk.Frame):
    """Slider with a live-updating numeric label."""
    def __init__(self, parent, label, frm, to, init, resolution=0.01, **kwargs):
        super().__init__(parent, bg="#071a26")

        # Left title
        self.title = tk.Label(self, text=label, font=("Helvetica", 12, "bold"),
                              bg="#071a26", fg="#36caff")
        self.title.grid(row=0, column=0, sticky="w")

        # Right numeric value
        self.value_label = tk.Label(self, text=str(init), font=("Helvetica", 12, "bold"),
                                    bg="#071a26", fg="#ffffff")
        self.value_label.grid(row=0, column=1, sticky="e", padx=10)

        # Slider widget
        self.scale = tk.Scale(
            self, from_=frm, to=to, orient="horizontal",
            resolution=resolution, length=360, showvalue=False,
            bg="#071a26", fg="white", troughcolor="#123a52",
            highlightthickness=0, command=self._on_change
        )
        self.scale.set(init)
        self.scale.grid(row=1, column=0, columnspan=2, pady=(2, 8))

        self.pack()

    def _on_change(self, value):
        """Update value label."""
        try:
            v = float(value)
            if v.is_integer():
                self.value_label.config(text=str(int(v)))
            else:
                self.value_label.config(text=f"{v:.2f}")
        except:
            self.value_label.config(text=value)

    def get(self):
        return float(self.scale.get())

    def set(self, value):
        self.scale.set(value)
        self._on_change(value)


# ------------------ GUI CREATION ------------------
def create_gui(start_callback, stop_callback):
    root = tk.Tk()
    root.title("IRIS LIVENESS SECURITY SYSTEM")
    root.geometry("980x620")
    root.configure(bg="#071a26")

    # Title
    title = tk.Label(root, text="IRIS LIVENESS SECURITY SYSTEM",
                     font=("Segoe UI", 26, "bold"), bg="#071a26", fg="#36caff")
    title.pack(pady=(12, 4))

    # Status label
    status_label = tk.Label(root, text="Iris: NOT RUNNING",
                            font=("Helvetica", 20, "bold"),
                            bg="#071a26", fg="#ff6666")
    status_label.pack(pady=(6, 8))

    # Slider frame
    frame = tk.Frame(root, bg="#071a26")
    frame.pack(pady=10)

    # ---- Sliders (NOW DEFINED CORRECTLY) ----
    ear_slider = SimpleSlider(frame, "EAR Threshold", 0.08, 0.40, 0.21)
    move_slider = SimpleSlider(frame, "Pupil Move Threshold (px)", 0.5, 10.0, 2.0)
    edge_slider = SimpleSlider(frame, "Iris Edge Std Threshold", 0.01, 0.30, 0.12)
    events_slider = SimpleSlider(frame, "Events Required (integer)", 1, 6, 2, resolution=1)

    # Buttons
    btn_frame = tk.Frame(root, bg="#071a26")
    btn_frame.pack(pady=14)

    start_btn = tk.Button(btn_frame, text="START SCAN",
                          font=("Helvetica", 14, "bold"),
                          bg="#e6f7ff", fg="#000000",
                          width=12, height=2,
                          command=start_callback)
    start_btn.grid(row=0, column=0, padx=20)

    stop_btn = tk.Button(btn_frame, text="STOP SCAN",
                         font=("Helvetica", 14, "bold"),
                         bg="#ffdfe0", fg="#000000",
                         width=12, height=2,
                         command=stop_callback)
    stop_btn.grid(row=0, column=1, padx=20)

    # Footer stats
    stats_label = tk.Label(root, text="Blinks: 0    Pupil Moves: 0    Iris Edge Events: 0",
                           font=("Helvetica", 12),
                           bg="#071a26", fg="#36b5ff")
    stats_label.pack(pady=(10, 6))

    # Return widget dictionary
    return {
        "root": root,
        "status_label": status_label,
        "stats_label": stats_label,
        "ear_slider": ear_slider,
        "move_slider": move_slider,
        "edge_slider": edge_slider,
        "events_slider": events_slider,
        "start_btn": start_btn,
        "stop_btn": stop_btn
    }


# For testing GUI alone
if __name__ == "__main__":
    def s(): print("Start pressed")
    def t(): print("Stop pressed")
    gui = create_gui(s, t)
    gui["root"].mainloop()

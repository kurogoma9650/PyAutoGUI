import tkinter as tk
from tkinter import messagebox


def main():
    root = tk.Tk()
    root.title("GUI Harness Fixture")
    root.geometry("640x420")

    state = tk.StringVar(value="idle")

    tk.Label(root, text="GUI Harness Fixture").pack(pady=8)
    entry = tk.Entry(root, width=40)
    entry.pack(pady=8)

    def clicked():
        state.set("clicked")

    tk.Button(root, text="Click Target", command=clicked).pack(pady=8)
    tk.Checkbutton(root, text="Check Target").pack(pady=8)
    tk.Label(root, textvariable=state, name="state_label").pack(pady=8)

    canvas = tk.Canvas(root, width=400, height=120, bg="white")
    canvas.pack(pady=8)
    canvas.create_rectangle(20, 30, 100, 90, fill="gray", tags=("draggable",))

    drag = {"x": 0, "y": 0}

    def start(event):
        drag["x"], drag["y"] = event.x, event.y

    def move(event):
        canvas.move("draggable", event.x - drag["x"], event.y - drag["y"])
        drag["x"], drag["y"] = event.x, event.y

    canvas.tag_bind("draggable", "<ButtonPress-1>", start)
    canvas.tag_bind("draggable", "<B1-Motion>", move)

    tk.Button(root, text="Modal", command=lambda: messagebox.showinfo("Fixture", "Modal")).pack()
    entry.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()

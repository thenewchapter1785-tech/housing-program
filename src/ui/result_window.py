import tkinter as tk


class ResultWindow:
    def __init__(self, title: str, content: str) -> None:
        self.root = None
        self.content = content
        try:
            self.root = tk.Tk()
            self.root.title(title)
            self.root.geometry("800x600")

            frame = tk.Frame(self.root, padx=12, pady=12)
            frame.pack(fill=tk.BOTH, expand=True)

            text = tk.Text(frame, wrap=tk.WORD)
            text.insert(tk.END, content)
            text.config(state=tk.DISABLED)
            text.pack(fill=tk.BOTH, expand=True)
        except Exception:
            self.root = None

    def show(self) -> None:
        if self.root is None:
            print(self.content)
            return
        self.root.mainloop()

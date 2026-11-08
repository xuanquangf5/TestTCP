"""Run with: python3 app.py"""

import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from network import NetworkSession, local_ip


class RoundedButton(tk.Canvas):
    """Small colored button without changing the native application theme."""

    def __init__(self, parent, text, command, color='#15803d', foreground='white'):
        background = ttk.Style(parent).lookup('TFrame', 'background') or parent.winfo_toplevel().cget('background')
        super().__init__(parent, width=104, height=30, background=background,
                         highlightthickness=0, bd=0, takefocus=True, cursor='hand2')
        self.command = command
        self.text, self.color, self.foreground = text, color, foreground
        self.enabled = True
        self.pressed = False
        self.bind('<ButtonPress-1>', self.press)
        self.bind('<ButtonRelease-1>', self.release)
        self.bind('<space>', self.activate)
        self.bind('<Return>', self.activate)
        self.bind('<FocusIn>', lambda event: self.draw())
        self.bind('<FocusOut>', lambda event: self.draw())
        self.draw()

    def draw(self):
        self.delete('all')
        color = self.color if self.enabled else '#d1d5db'
        if self.pressed:
            color = '#b91c1c' if self.color == '#dc2626' else '#166534'
        self.create_polygon(9, 1, 95, 1, 103, 1, 103, 9, 103, 21,
                            103, 29, 95, 29, 9, 29, 1, 29, 1, 21, 1, 9, 1, 1,
                            smooth=True, splinesteps=24, fill=color,
                            outline='#2563eb' if self.focus_get() == self else '', width=2)
        self.create_text(52, 15, text=self.text, font=('TkDefaultFont', 11),
                         fill=self.foreground if self.enabled else '#6b7280')

    def set_state(self, text, color, enabled=True):
        self.text, self.color, self.enabled = text, color, enabled
        self.pressed = False
        self.configure(cursor='hand2' if enabled else 'arrow', takefocus=enabled)
        self.draw()

    def press(self, event):
        if self.enabled:
            self.focus_set()
            self.pressed = True
            self.draw()

    def release(self, event):
        activate = self.pressed and 0 <= event.x < 104 and 0 <= event.y < 30
        self.pressed = False
        self.draw()
        if activate:
            self.activate(event)

    def activate(self, event):
        if self.enabled:
            self.command()
        return 'break'


class LogFrame(tk.Canvas):
    """Rounded border around a regular Text widget, without a scrollbar."""

    def __init__(self, parent):
        background = ttk.Style(parent).lookup('TFrame', 'background') or parent.winfo_toplevel().cget('background')
        super().__init__(parent, background=background, highlightthickness=0, bd=0)
        self.text = tk.Text(self, wrap='word', state='disabled', font=('Courier', 11),
                            borderwidth=0, highlightthickness=0, padx=8, pady=6)
        self.window = self.create_window(6, 6, anchor='nw', window=self.text)
        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width, height = event.width, event.height
        radius = 7
        self.delete('border')
        self.create_polygon(
            radius, 1, width-radius, 1, width-1, 1, width-1, radius,
            width-1, height-radius, width-1, height-1, width-radius, height-1,
            radius, height-1, 1, height-1, 1, height-radius, 1, radius, 1, 1,
            smooth=True, splinesteps=24, fill=self.text.cget('background'),
            outline='#9ca3af', width=1, tags='border')
        self.tag_lower('border')
        self.itemconfigure(self.window, width=max(1, width-12), height=max(1, height-12))


class App:
    def __init__(self, root):
        self.root = root
        self.session = None
        self.events = queue.Queue()
        self.generation = 0
        self.closed = False
        root.title('TCP / UDP Connection Tester')
        root.geometry('594x580')
        root.minsize(594, 400)
        panel = ttk.Frame(root, padding=16)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='TCP / UDP Connection Tester', font=('', 18, 'bold')).pack(anchor='w')
        config = ttk.Frame(panel)
        config.pack(fill='x', pady=(16, 0))
        self.entries = []
        self.values = []
        for col, (label, value, width) in enumerate([
            ('IP server / IP bind', local_ip(), 22), ('TCP port', '8008', 10), ('UDP port', '8004', 10)
        ]):
            frame = ttk.Frame(config)
            frame.grid(row=0, column=col, padx=(0, 16), sticky='w')
            ttk.Label(frame, text=label).pack(anchor='w')
            var = tk.StringVar(value=value)
            entry = ttk.Entry(frame, textvariable=var, width=width)
            entry.pack(pady=(4, 0))
            self.values.append(var)
            self.entries.append(entry)
        actions = ttk.Frame(panel)
        actions.pack(fill='x', pady=16)
        self.buttons = {}
        for role in ('server', 'client'):
            button = RoundedButton(actions, text=f'Start {role.title()}',
                                command=lambda r=role: self.toggle(r))
            button.pack(side='left', padx=(0, 10))
            self.buttons[role] = button
        RoundedButton(actions, text='Xóa log', command=self.clear_log,
                      color='#e5e7eb', foreground='#111827').pack(side='right')
        log_frame = LogFrame(panel)
        log_frame.pack(fill='both', expand=True)
        self.output = log_frame.text
        for tag, color in [('ERROR', '#dc2626'), ('WARN', '#a16207'), ('TCP', '#60a5fa'), ('UDP', '#c084fc'), ('INFO', '#15803d')]:
            self.output.tag_configure(tag, foreground=color)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(80, self.poll)

    def clear_log(self):
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.configure(state='disabled')

    def log(self, level, message):
        self.events.put(('log', level, message))

    def set_controls(self, role=None, starting=False):
        for entry in self.entries:
            entry.configure(state='disabled' if role else 'normal')
        for name, button in self.buttons.items():
            running = role == name
            button.set_state(text=f'{"Stop" if running else "Start"} {name.title()}',
                             color='#dc2626' if running else '#15803d',
                             enabled=not (starting or (role and not running)))

    def toggle(self, role):
        if self.session:
            self.session.stop()
            self.session = None
            self.generation += 1
            self.set_controls()
            self.log('INFO', 'Đã dừng và đóng các socket.')
            return
        try:
            ip = self.values[0].get().strip()
            ports = [int(value.get()) for value in self.values[1:]]
            self.generation += 1
            generation = self.generation
            session = NetworkSession(ip, *ports, self.log,
                                     lambda: self.events.put(('failed', generation)))
        except (ValueError, OSError) as exc:
            message = f'Cấu hình không hợp lệ: {exc}'
            self.log('ERROR', message)
            messagebox.showerror('Không thể Start', message, parent=self.root)
            return
        self.session = session
        self.set_controls(role, starting=True)

        def start():
            try:
                session.start(role)
                self.events.put(('ready', generation, role))
            except Exception as exc:
                self.events.put(('start_error', generation, str(exc)))
        threading.Thread(target=start, daemon=True).start()

    def poll(self):
        for _ in range(300):
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if event[0] == 'log':
                _, level, message = event
                self.output.configure(state='normal')
                self.output.insert('end', f'[{level}] {message}\n', level)
                if int(self.output.index('end-1c').split('.')[0]) > 5000:
                    self.output.delete('1.0', '501.0')
                self.output.see('end')
                self.output.configure(state='disabled')
            elif event[1] == self.generation:
                if event[0] == 'ready' and self.session and not self.session.stopped.is_set():
                    self.set_controls(event[2])
                elif event[0] in ('failed', 'start_error'):
                    if self.session:
                        self.session.stop()
                    self.session = None
                    self.set_controls()
                    if event[0] == 'start_error':
                        message = f'Khởi động thất bại: {event[2]}'
                        self.log('ERROR', message)
                        messagebox.showerror('Không thể Start', message, parent=self.root)
        if not self.closed:
            self.root.after(80, self.poll)

    def close(self):
        self.closed = True
        if self.session:
            self.session.stop()
        self.root.destroy()


if __name__ == '__main__':
    window = tk.Tk()
    app = App(window)
    if '--smoke-test' in sys.argv:
        window.after(1000, app.close)
    window.mainloop()

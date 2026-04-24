import time, sys, threading, os, pymem, keyboard
try:
    from rich.console import Console
    from rich.progress import track
    ri_av = True
except ImportError:
    ri_av = False
    class Console:
        def print(self, *args, **kwargs): print(*args)
        def __call__(self, *args, **kwargs): print(*args)
    def track(iterable, description=""): print(description); return iterable
console = Console() if ri_av else Console()
class Bhop:
    def __init__(self): self.pm = self.client = self.hw = None; self.running = self.enabled = False; self.game = "unknown"; self.build = self.onground_offset = self.jump_offset = 0
    def detect_game(self):
        try:
            hl_base = pymem.process.module_from_name(self.pm.process_handle, "hl.exe").lpBaseOfDll
            if self.pm.read_bytes(hl_base + 0x14DF6, 7) == b'cstrike': self.game, self.onground_offset, self.jump_offset = "cstrike", 0x122E2D4, 0x131434
            elif self.pm.read_bytes(hl_base + 0x14DF0, 5) == b'valve': self.game, self.onground_offset, self.jump_offset = "half-life", 0x122E2D4, 0xA4BE0
            elif self.pm.read_bytes(hl_base + 0x14DF6, 4) == b'dod\x00': self.game, self.onground_offset, self.jump_offset = "day of defeat", 0x122E2D4, 0x18AA68
            elif self.pm.read_bytes(hl_base + 0x14DF6, 4) == b'dmc\x00': self.game, self.onground_offset, self.jump_offset = "deathmatch classic", 0x122E2D4, 0xA0A9C
            else: self.game, self.onground_offset, self.jump_offset = "unknown", 0x122E2D4, 0xA4BE0
            return self.game
        except: self.game, self.onground_offset, self.jump_offset = "unknown", 0x122E2D4, 0xA4BE0; return "unknown"
    def check_build(self):
        try: self.build = self.pm.read_int(self.hw + 0x1684F0); return self.build == 8684
        except: return False
    def is_game_running(self):
        try: pymem.process.module_from_name(self.pm.process_handle, "hl.exe"); return True
        except: return False
    def attach(self):
        try: self.pm = pymem.Pymem("hl.exe"); self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll; self.hw = pymem.process.module_from_name(self.pm.process_handle, "hw.dll").lpBaseOfDll; return True
        except: return False
    def write_jump(self, value):
        try: self.pm.write_int(self.client + self.jump_offset, value)
        except: pass
    def read_onground(self):
        try: return self.pm.read_int(self.hw + self.onground_offset)
        except: return 0
    def loop(self):
        holding = False
        while self.running:
            if not self.is_game_running(): console.print("\n[bold red]❌ game is closed[/bold red]" if ri_av else "\ngame is closed"); os.system("pause"); os._exit(0)
            if self.enabled:
                if keyboard.is_pressed('space'):
                    if not holding:
                        if self.read_onground() == 1: self.write_jump(5)
                        holding = True
                    else:
                        if self.read_onground() == 1: self.write_jump(5)
                        else: self.write_jump(4)
                else:
                    if holding: self.write_jump(4); holding = False
            else:
                if holding: self.write_jump(4); holding = False
            time.sleep(0.001)
    def start(self):
        if not self.attach() or not self.check_build(): return False
        self.running = self.enabled = True
        self.thread = threading.Thread(target=self.loop, daemon=True); self.thread.start()
        return True
    def stop(self): self.running = False; self.write_jump(4)
def clear(): os.system('cls' if sys.platform == 'win32' else 'clear')
def main():
    if sys.platform == "win32":
        try: import ctypes; ctypes.windll.kernel32.SetConsoleTitleW("bhop")
        except: pass
    clear()
    if not ri_av: console.print("[warning] rich not installed, using basic output[/warning]")
    bhop = Bhop()
    if not bhop.attach(): 
        console.print("failed to attach, start hl.exe first")
        os.system("pause")
        return
    game = bhop.detect_game()
    if ri_av:
        console.print(f"[bold green]detected game: {game}[/bold green]")
    else:
        console.print(f"\ndetected game: {game}\n")
    if not bhop.check_build(): 
        console.print(f"unsupported build: {bhop.build}\nonly steam_legacy (build 8684) is supported")
        os.system("pause")
        return
    if ri_av:
        console.print(f"build: {bhop.build} (steam_legacy)\nF6 - toggle bhop")
    else:
        console.print(f"\nbuild: {bhop.build} (steam_legacy)\nF6 - toggle bhop\npress Ctrl+C to exit\n")
    while True:
        if not bhop.is_game_running(): 
            console.print("\ngame is closed")
            os.system("pause")
            break
        if keyboard.is_pressed('f6'):
            if not bhop.running:
                if bhop.start(): 
                    console.print("\nbhop enabled")
            else:
                bhop.enabled = not bhop.enabled
                if bhop.enabled: 
                    console.print("\nbhop enabled")
                else: 
                    bhop.write_jump(4)
                    console.print("\nbhop disabled")
        time.sleep(0.05)
    bhop.stop()
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\nexit")

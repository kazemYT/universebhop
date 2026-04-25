import time,sys,threading,os,pymem,keyboard
try:from rich.console import Console;from rich.progress import track;ri_av=True
except:ri_av=False;Console=lambda:None;track=lambda i,d:i
console=Console()if ri_av else type('',(),{'print':lambda s,*a,**k:print(*a)})()
class Bhop:
    def __init__(s):
        s.pm=s.client=s.hw=None;s.engine=s.game=s.process_name='unknown'
        s.running=s.enabled=False;s.jump_offset=s.onground_offset=s.onground2_offset=0;s.build=0
    def pattern_scan(s,p,m='client.dll'):
        try:
            mod=pymem.process.module_from_name(s.pm.process_handle,m)
            start,l=mod.lpBaseOfDll,mod.SizeOfImage
            pb=bytes.fromhex(p.replace(' ',''))
            mask=[0 if x=='??'or x=='?'else 1 for x in p.split()]
            for i in range(l-len(pb)):
                for j in range(len(pb)):
                    if mask[j] and s.pm.read_bytes(start+i+j,1)[0]!=pb[j]:break
                else:return start+i
        except:return None
    def detect_game_source(s):
        try:
            if s.process_name=='hl2.exe':s.game='half-life 2 deathmatch';s.engine='source';s.jump_offset=0x4B134C;s.onground_offset=0x4B38D4;s.onground2_offset=0x4B3914;return 1
            if s.process_name=='gmod.exe':
                s.game='garrys mod';s.engine='source';s.jump_offset=0xA2D800;s.onground_offset=0xA31370
                for o,v in[(s.jump_offset,'jump'),(s.onground_offset,'onground')]:
                    try:s.pm.read_int(s.client+o)
                    except:
                        pat='C0 7D 69 44 FC 7F 00 00 90 88 69 44 FC 7F 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 04'if v=='jump'else'FC 7F 00 00 50 8C 70 43 FC 7F 00 00 8E 01 00 80 00 00 00 00 D0 8A 70 43 FC 7F 00 00 A0 8A 70 43 FC 7F 00 00 8F 01 00 80 00 00 00 00 01'
                        a=s.pattern_scan(pat)
                        if a:
                            if v=='jump':s.jump_offset=a+98
                            else:s.onground_offset=a+44
                return 1
        except:return 0
    def detect_game_goldsource(s):
        try:
            hl=pymem.process.module_from_name(s.pm.process_handle,'hl.exe').lpBaseOfDll
            if s.pm.read_bytes(hl+0x14DF6,7)==b'cstrike':s.game='cstrike';s.jump_offset=0x131434
            elif s.pm.read_bytes(hl+0x14DF0,5)==b'valve':s.game='half-life';s.jump_offset=0xA4BE0
            elif s.pm.read_bytes(hl+0x14DF6,4)==b'dod\x00':s.game='dayofdefeat';s.jump_offset=0x18AA68
            elif s.pm.read_bytes(hl+0x14DF6,4)==b'dmc\x00':s.game='deathmatchclassic';s.jump_offset=0xA0A9C
            else:s.game='unknown goldsource';s.jump_offset=0xA4BE0
            s.engine='goldsource';s.onground_offset=0x122E2D4
            return 1
        except:return 0
    def check_build_goldsource(s):
        try:s.hw=pymem.process.module_from_name(s.pm.process_handle,'hw.dll').lpBaseOfDll;s.build=s.pm.read_int(s.hw+0x1684F0);return s.build==8684
        except:return 0
    def is_game_running(s):
        try:pymem.process.module_from_name(s.pm.process_handle,s.process_name);return 1
        except:return 0
    def attach(s):
        for p in['hl.exe','hl2.exe','gmod.exe']:
            try:s.pm=pymem.Pymem(p);s.process_name=p;return 1
            except:continue
        return 0
    def init_offsets(s):
        if s.process_name=='hl.exe':
            if not s.detect_game_goldsource()or not s.check_build_goldsource():return 0
            s.client=pymem.process.module_from_name(s.pm.process_handle,'client.dll').lpBaseOfDll
            return 1
        if s.process_name in['hl2.exe','gmod.exe']:
            s.client=pymem.process.module_from_name(s.pm.process_handle,'client.dll').lpBaseOfDll
            return s.detect_game_source()
        return 0
    def write_jump(s,v):
        try:s.pm.write_int(s.client+s.jump_offset,v)
        except:pass
    def read_onground(s):
        try:
            if s.engine=='goldsource':return s.pm.read_int(s.hw+s.onground_offset)
            o=s.pm.read_int(s.client+s.onground_offset)
            if s.onground2_offset and o==0:
                try:
                    if s.pm.read_int(s.client+s.onground2_offset)==1:return 1
                except:pass
            return o
        except:return 0
    def loop(s):
        h=0
        while s.running:
            if not s.is_game_running():print('\ngame is closed');time.sleep(1);os._exit(0)
            if s.enabled and keyboard.is_pressed('space'):
                s.write_jump(5 if s.read_onground()==1 else 4)
                h=1
            elif h:s.write_jump(4);h=0
            time.sleep(0.001)
    def start(s):
        if not s.init_offsets():return 0
        s.running=s.enabled=1;s.thread=threading.Thread(target=s.loop,daemon=1);s.thread.start();return 1
    def stop(s):s.running=0;s.write_jump(4)
def main():
    if sys.platform=='win32':
        try:import ctypes;ctypes.windll.kernel32.SetConsoleTitleW('bhop')
        except:pass
    os.system('cls' if sys.platform=='win32' else 'clear')
    b=Bhop()
    print('waiting for game...\nsupported: hl.exe, hl2.exe, gmod.exe\n')
    if not b.attach():print('failed to attach');os.system('pause');return
    if not b.init_offsets():print('failed to init offsets');os.system('pause');return
    os.system('cls' if sys.platform=='win32' else 'clear')
    print(f"engine: {b.engine}\ngame: {b.game}\njump: {hex(b.jump_offset)}\nonground: {hex(b.onground_offset)}\n\nF6 - toggle bhop")
    while 1:
        if not b.is_game_running():print('game closed');os.system('pause');break
        if keyboard.is_pressed('f6'):
            if not b.running:b.start();print('\nbhop enabled')
            else:
                b.enabled=not b.enabled
                if b.enabled:print('\nbhop enabled')
                else:b.write_jump(4);print('\nbhop disabled')
        time.sleep(0.05)
    b.stop()
if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('exiting...')

# Made by AjaxFNC
# If you are ironweb10, FUCK OFF

import customtkinter
import json
import os
import webbrowser
import asyncio
import psutil
import subprocess
import aiohttp
import threading
import win32gui
import win32con
import time
from ctkdlib.custom_widgets import *


customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

authPath = os.path.join(".settings", "auth.json")
savedDataPath = os.path.join(".settings", "settings.json")

class fortniteAuth():
    def __init__(self, app_instance=None):
        self.app = app_instance

    def set_app(self, app_instance):
        self.app = app_instance

    def openSite(self, site):
        webbrowser.open(site)

    def getAuthIfExists(self):
        try:
            if not os.path.exists(authPath):
                return None
            with open(authPath, "r") as f:
                auth_data = json.loads(f.read().strip())
                return auth_data if auth_data else None
        except:
            return None

    def saveAuth(self, auth, isAuth=False):
        os.makedirs(os.path.dirname(authPath), exist_ok=True)
        
        if isAuth:
            for key in ['message', 'status', 'success']:
                auth.pop(key, None)
        
        with open(authPath, "w") as f:
            json.dump(auth, f)

    async def checkAuth(self, authURI):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(authURI) as response:
                    if response.status == 200:
                        return {"success": True, "data": await response.json()}
                    elif response.status == 400:
                        return {"success": False, "message": "User denied authentication"}
                    elif response.status == 202:
                        return {"success": False, "message": "Authentication pending"}
                    return None
            except:
                return None

    async def getAccessToken(self, accountId: str, deviceId: str, secret: str) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic M2Y2OWU1NmM3NjQ5NDkyYzhjYzI5ZjFhZjA4YThhMTI6YjUxZWU5Y2IxMjIzNGY1MGE2OWVmYTY3ZWY1MzgxMmU="
                }
                
                data = {
                    "grant_type": "device_auth",
                    "account_id": accountId,
                    "device_id": deviceId,
                    "secret": secret
                }
                
                async with session.post("https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token", 
                                     headers=headers, 
                                     data=data) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        return json_data.get("access_token")
                    return None
            except:
                return None
    async def getExchangeCode(self, accessToken: str, consumingClientId: str = None) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "Authorization": f"Bearer {accessToken}"
                }
                
                url = "https://account-public-service-prod.ol.epicgames.com/account/api/oauth/exchange"
                if consumingClientId is not None:
                    url += f"?consumingClientId={consumingClientId}"
                
                async with session.get(url, 
                                     headers=headers) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        return json_data.get("code")
                    return None
            except:
                return None

    async def startAuthIfNotExists(self):
        if self.getAuthIfExists():
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://fnbl.xyz/api/device-auth') as response:
                    if response.status == 200:
                        data = await response.json()
                        self.openSite(data.get('url'))
                        
                        if self.app:
                            self.app.switch_page(self.app.Page_2)

                        def auth_loop():
                            async def check_auth_loop():
                                while True:
                                    await asyncio.sleep(5)
                                    result = await self.checkAuth(data.get('authorizationURL'))
                                    
                                    if not result:
                                        continue
                                                
                                    if result.get('success'):
                                        auth_data = result.get('data')
                                        self.saveAuth(auth_data, isAuth=True)
                                        
                                        def update_app():
                                            self.app.auth_data = auth_data
                                            self.app.is_logged_in = True
                                            self.app.switch_page(self.app.Page_3)
                                            self.app.update_ui_with_auth()
                                            
                                        self.app.after(0, update_app)
                                        break
                                    elif result.get('message') == "User denied authentication":
                                        self.app.after(0, lambda: self.app.switch_page(self.app.Page_1))
                                        break

                            asyncio.run(check_auth_loop())

                        threading.Thread(target=auth_loop, daemon=True).start()

        except Exception as e:
            print(f"Auth error: {e}")
            if self.app:
                self.app.switch_page(self.app.Page_1)

class NotificationWindow(customtkinter.CTkToplevel):
    def __init__(self):
        super().__init__()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = 300
        window_height = 80
        x = 20
        y = 20
        
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.overrideredirect(True)
        
        self.after(10, self.setup_window)
        
        self.frame = customtkinter.CTkFrame(self)
        self.frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.label = customtkinter.CTkLabel(
            self.frame,
            text="",
            font=customtkinter.CTkFont('Roboto', size=16, weight='bold')
        )
        self.label.pack(expand=True)
        
        self.alpha = 255
        self.after(4000, self.destroy)

    def setup_window(self):
        try:
            hwnd = self.winfo_id()
            extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                                extended_style | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST | win32con.WS_EX_NOACTIVATE)
            self.attributes('-topmost', True)
        except Exception as e:
            print(f"Window setup error: {e}")

    def fade_out(self):
        if self.alpha > 0:
            self.alpha = max(0, self.alpha - 5)
            self.attributes('-alpha', self.alpha / 255)
            self.after(50, self.fade_out)
        else:
            self.destroy()

    def show_message(self, message):
        self.label.configure(text=message)
        self.update()

class App(customtkinter.CTk):

    HEIGHT = 600
    WIDTH = 1000

    def __init__(self):
        super().__init__()
        self.auth_handler = fortniteAuth()
        self.auth_handler.set_app(self)
        
        self.is_logged_in = False
        self.auth_data = None
        self.access_token = None
        self.auto_refresh_enabled = True
        self.notifications_enabled = True
        self.auto_refresh_task = None
        self.previous_players = None
        self.game_path = "C:\\Program Files\\Epic Games\\Fortnite\\FortniteGame\\Binaries\\Win64"
        
        self.title("Real Players | V2 | Made by AjaxFNC")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.resizable(False, False)
        self.Page_1 = customtkinter.CTkFrame(self, fg_color='transparent', corner_radius=0, border_width=0)
        self.Page_1.pack(expand=True, fill='both')
        self.Page_2 = customtkinter.CTkFrame(self, fg_color='transparent', corner_radius=0, border_width=0)
        self.Page_3 = customtkinter.CTkFrame(self, fg_color='transparent', corner_radius=0, border_width=0)

        self.Label1 = customtkinter.CTkLabel(
            self.Page_1, font=customtkinter.CTkFont(
                'Roboto', size=74, weight='bold'), text="Real Players | Login")
        self.Label1.place(x=169, y=0)

        self.Button1 = customtkinter.CTkButton(
            self.Page_1,
            font=customtkinter.CTkFont(
                'Roboto',
                size=54,
                weight='bold'),
            width=590,
            height=120,
            text="Start Login",
            corner_radius=100)
        self.Button1.place(x=205, y=98)

        self.Label2 = customtkinter.CTkLabel(self.Page_2, font=customtkinter.CTkFont(
            'Roboto', size=74, weight='bold'), text="Real Players | Waiting for auth")
        self.Label2.place(x=-4, y=0)

        self.Button2 = customtkinter.CTkButton(
            self.Page_2,
            font=customtkinter.CTkFont(
                'Roboto',
                size=54,
                weight='bold'),
            width=590,
            height=120,
            text="Cancel",
            corner_radius=98)
        self.Button2.place(x=205, y=98)

        self.Label3 = customtkinter.CTkLabel(
            self.Page_3, font=customtkinter.CTkFont(
                'Roboto', size=74, weight='bold'), text="Real Players")
        self.Label3.place(x=299, y=0)

        self.Frame1 = customtkinter.CTkFrame(self.Page_3, width=710, height=386, corner_radius=25)
        self.Frame1.place(x=156, y=91)

        self.Button3 = customtkinter.CTkButton(
            self.Page_3,
            bg_color=[
                'gray86',
                'gray17'],
            font=customtkinter.CTkFont(
                'Roboto',
                size=19,
                weight='bold'),
            width=292,
            height=37,
            text="Logout")
        self.Button3.place(x=210, y=430)
        

        self.ButtonLaunch = customtkinter.CTkButton(
            self.Page_3,
            bg_color=[
                'gray86',
                'gray17'],
            font=customtkinter.CTkFont(
                'Roboto',
                size=19,
                weight='bold'),
            width=292,
            height=37,
            text="Launch Game")
        self.ButtonLaunch.place(x=210, y=385)

        self.Button4 = customtkinter.CTkButton(
            self.Page_3,
            bg_color=[
                'gray86',
                'gray17'],
            font=customtkinter.CTkFont(
                'Roboto',
                size=19,
                weight='bold'),
            width=292,
            height=37,
            text="Refresh")
        self.Button4.place(x=516, y=429)

        self.info_labels = [
            customtkinter.CTkLabel(
                self.Page_3,
                bg_color=[
                    'gray86',
                    'gray17'],
                font=customtkinter.CTkFont(
                    'Roboto',
                    size=35,
                    weight='bold'),
                text="Session Players (real players): N/A"),
            customtkinter.CTkLabel(
                self.Page_3,
                bg_color=[
                    'gray86',
                    'gray17'],
                font=customtkinter.CTkFont(
                    'Roboto',
                    size=35,
                    weight='bold'),
                text="Session Playlist: N/A")
        ]
        self.info_labels[0].place(x=180, y=110)
        self.info_labels[1].place(x=180, y=150)

        self.CheckBox1 = customtkinter.CTkCheckBox(
            self.Page_3,
            bg_color=[
                'gray86',
                'gray17'],
            corner_radius=23,
            text="Automaticly refresh")
        self.CheckBox1.place(x=515, y=395)

        self.CheckBox2 = customtkinter.CTkCheckBox(
            self.Page_3,
            bg_color=[
                'gray86',
                'gray17'],
            corner_radius=22,
            text="Show Notification")
        self.CheckBox2.place(x=675, y=395)

        self.Frame2 = customtkinter.CTkFrame(
            self.Page_3,
            width=522,
            height=125,
            corner_radius=42,
            fg_color="#202020",
            bg_color="#2b2b2b")
        self.Frame2.place(x=245, y=248)

        self.Label7 = customtkinter.CTkLabel(
            self.Page_3, bg_color="#202020", font=customtkinter.CTkFont(
                'Roboto', size=35, weight='bold'), text="Logged In: True")
        self.Label7.place(x=265, y=255)

        self.Label8 = customtkinter.CTkLabel(
            self.Page_3,
            bg_color=[
                'gray86',
                'gray17'],
            font=customtkinter.CTkFont(
                'Roboto',
                size=35,
                weight='bold'),
            text="Logged In as: ",
            fg_color="#202020")
        self.Label8.place(x=265, y=300)

        self.Button1.configure(command=self.handle_auth)
        self.Button2.configure(command=lambda: self.switch_page(self.Page_1))
        self.Button3.configure(command=self.handle_logout)
        self.ButtonLaunch.configure(command=self.handle_launch)
        CTkPopupMenu(self.ButtonLaunch, popup_type=0, values={'Launch Game': self.handle_launch, 'Launch Game (All cores)': lambda: self.handle_launch(performance=True), 'Change Game Path': self.edit_gamePath}, corner_radius=6)
        self.Button4.configure(command=self.handle_refresh_wrapper)
        self.CheckBox1.configure(command=self.toggle_auto_refresh)
        self.CheckBox2.configure(command=self.toggle_notifications)

        self.CheckBox1.select()
        self.CheckBox2.select()

        exists = self.auth_handler.getAuthIfExists()
        if exists:
            self.is_logged_in = True
            self.auth_data = exists
            self.switch_page(self.Page_3)
            self.update_ui_with_auth()
            self.load_settings()
            if self.auto_refresh_enabled:
                self.start_auto_refresh()
        else:
            self.is_logged_in = False
            self.auth_data = None
            self.switch_page(self.Page_1)
            self.load_settings()

        if self.auto_refresh_enabled:
            self.start_auto_refresh()

    def switch_page(self, page):
        for p in [self.Page_1, self.Page_2, self.Page_3]:
            p.pack_forget()
        page.pack(expand=True, fill='both')

    def handle_auth(self):
        asyncio.run(self.auth_handler.startAuthIfNotExists())

    def handle_logout(self):
        if os.path.exists(authPath):
            os.remove(authPath)
        self.is_logged_in = False
        self.auth_data = None
        self.access_token = None
        self.previous_players = None
        self.stop_auto_refresh()
        self.switch_page(self.Page_1)

    def handle_launch(self, performance=False):
        if not self.auth_data:
            return
            
        if self.checkGameRunning():
            close_commands = [
                "taskkill /f /im FortniteLauncher.exe",
                "taskkill /f /im FortniteClient-Win64-Shipping.exe",
                "taskkill /f /im FortniteClient-Win64-Shipping_EAC.exe",
                "taskkill /f /im FortniteClient-Win64-Shipping_EAC_EOS.exe",
                "taskkill /f /im FortniteClient-Win64-Shipping_BE.exe",
                "taskkill /f /im CrashReportClient.exe"
            ]
            for cmd in close_commands:
                os.system(cmd)
            self.ButtonLaunch.configure(text="Launch Game")
            return
        
        exchangeCode = asyncio.run(self.auth_handler.getExchangeCode(self.access_token))
        auth_data = self.auth_data
        
        args = ["-AUTH_LOGIN=unused", f"-AUTH_PASSWORD={exchangeCode}", "-AUTH_TYPE=exchangecode", 
                "-epicapp=Fortnite", "-epicenv=Prod", "-EpicPortal", f"-epicuserid={auth_data['accountId']}"]
                
        if performance:
            args.extend(["-NOTEXTURESTREAMING", "-USEALLAVAILABLECORES"])
            
        launcher_path = os.path.join(self.game_path, "FortniteLauncher.exe")
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen([launcher_path] + args, cwd=self.game_path, startupinfo=startupinfo)

    def edit_gamePath(self):
        dialog = customtkinter.CTkInputDialog(
            text="Enter Fortnite Game Path (Make sure its the win64 folder):\n\nCurrent:\n" + self.game_path,
            title="Change Game Path"
        )
        new_path = dialog.get_input()
        if new_path:
            if os.path.exists(new_path) and os.path.exists(os.path.join(new_path, "FortniteLauncher.exe")):
                self.game_path = new_path
                self.save_settings()
                self.show_message("Success", "Game path updated successfully!")
            else:
                self.show_message("Error", "Invalid path: FortniteLauncher.exe not found")

    def toggle_auto_refresh(self):
        self.auto_refresh_enabled = self.CheckBox1.get()
        if self.auto_refresh_enabled:
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
        self.save_settings()

    def toggle_notifications(self):
        self.notifications_enabled = self.CheckBox2.get()
        self.save_settings()

    def checkGameRunning(self):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == 'FortniteLauncher.exe':
                    return True
                if proc.info['name'] == 'FortniteClient-Win64-Shipping.exe':
                    return True
                if proc.info['name'] == "FortniteClient-Win64-Shipping_EAC_EOS.exe":
                    return True
                if proc.info['name'] == "FortniteClient-Win64-Shipping_EAC.exe":
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def start_auto_refresh(self):
        if not hasattr(self, 'auto_refresh_running') or not self.auto_refresh_running:
            self.auto_refresh_running = True
            def auto_refresh_loop():
                while self.auto_refresh_running and self.auto_refresh_enabled:
                    self.handle_refresh_wrapper()
                    time.sleep(5)
            threading.Thread(target=auto_refresh_loop, daemon=True).start()

    def stop_auto_refresh(self):
        self.auto_refresh_running = False

    def handle_refresh_wrapper(self):
        threading.Thread(target=self.refresh_thread, daemon=True).start()
        threading.Thread(target=self.handle_game_running, daemon=True).start()

    def handle_game_running(self):
        isGameRunning = self.checkGameRunning()
        if isGameRunning:
            self.ButtonLaunch.configure(text="Close Game")
        else:
            self.ButtonLaunch.configure(text="Launch Game")


    def refresh_thread(self):
        asyncio.run(self.handle_refresh())

    async def handle_refresh(self):
        if not self.is_logged_in:
            print("Not logged in!")
            return

        print("Auth Data:", self.auth_data)
        self.access_token = await self.auth_handler.getAccessToken(
            self.auth_data["accountId"],
            self.auth_data["deviceId"],
            self.auth_data["secret"]
        )
        print("Access Token:", self.access_token)

        dataUrl = f"https://fngw-mcp-gc-livefn.ol.epicgames.com/fortnite/api/matchmaking/session/findPlayer/{self.auth_data['accountId']}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(dataUrl, headers=headers) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        print(json_data)
                        if json_data == []:
                            self.info_labels[0].configure(text="Session Players (real players): None")
                            self.info_labels[1].configure(text="Session Playlist: None")
                            self.previous_players = None
                            return
                        else:
                            current_players = json_data[0]['totalPlayers']
                            if current_players > 0 and self.previous_players != current_players:
                                self.show_notification(
                                    "Real Players",
                                    f"Real players updated: {current_players}"
                                )
                            self.previous_players = current_players
                            self.info_labels[0].configure(text=f"Session Players (real players): {current_players}")
                            self.info_labels[1].configure(text=f"Session Playlist: {json_data[0]['attributes']['PLAYLISTNAME_s']}")
        except Exception as e:
            print(f"Error refreshing: {str(e)}")

    def update_session_info(self, session_data):
        try:
            stats = session_data.get('profileChanges', [{}])[0].get('profile', {}).get('stats', {})
            
            self.info_labels[0].configure(text=f"Session Players (real players): {stats.get('attributes', {}).get('player_count', 'N/A')}")
            self.info_labels[1].configure(text=f"Session Playlist: {stats.get('attributes', {}).get('playlist', 'N/A')}")
            
            self.Label7.configure(text=f"Logged In: {str(self.is_logged_in)}")
            self.Label8.configure(text=f"Logged In as: {self.auth_data.get('username', 'Unknown')}")
            
            current_players = stats.get('attributes', {}).get('player_count')
            if self.notifications_enabled and self.previous_players is not None and current_players != self.previous_players:
                self.show_notification("Player Count Updated", f"Players in session: {current_players}")
            self.previous_players = current_players
            
        except Exception as e:
            print(f"Error updating session info: {str(e)}")

    def update_ui_with_auth(self):
        if self.auth_data:
            self.Label7.configure(text=f"Logged In: {str(self.is_logged_in)}")
            self.Label8.configure(text=f"Logged In as: {self.auth_data.get('username', 'Unknown')}")
            self.handle_refresh_wrapper()

    def show_notification(self, title, message):
        if self.notifications_enabled:
            try:
                def create_notification():
                    if hasattr(self, 'notification_window') and self.notification_window is not None:
                        try:
                            self.notification_window.destroy()
                        except:
                            pass
                    self.notification_window = NotificationWindow()
                    self.notification_window.title(title)
                    self.notification_window.show_message(message)
                
                self.after(0, create_notification)
            except Exception as e:
                print(f"Error showing notification: {str(e)}")

    def show_message(self, title, message):
        dialog = customtkinter.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("300x100")
        dialog.resizable(False, False)
        
        dialog.update()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        label = customtkinter.CTkLabel(dialog, text=message)
        label.pack(expand=True)
        
        dialog.after(2000, dialog.destroy)
        dialog.grab_set()

    def save_settings(self):
        if not os.path.exists(".settings"):
            os.makedirs(".settings")
        with open(".settings/settings.json", "w") as f:
            json.dump({
                "auto_refresh": int(self.auto_refresh_enabled),
                "show_notifications": int(self.notifications_enabled),
                "game_path": self.game_path
            }, f)

    def load_settings(self):
        try:
            if not os.path.exists(".settings/settings.json"):
                self.save_settings()
            with open(".settings/settings.json", "r") as f:
                settings = json.load(f)
                self.auto_refresh_enabled = bool(settings.get("auto_refresh", True))
                self.notifications_enabled = bool(settings.get("show_notifications", True))
                self.game_path = settings.get("game_path", "C:\\Program Files\\Epic Games\\Fortnite\\FortniteGame\\Binaries\\Win64")
                
                if not self.auto_refresh_enabled:
                    self.CheckBox1.deselect()
                if not self.notifications_enabled:
                    self.CheckBox2.deselect()
        except:
            self.save_settings()

if __name__ == "__main__":
    app = App()
    app.mainloop()


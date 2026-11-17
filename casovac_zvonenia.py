import re
import time
import threading
import winsound
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
from playwright.sync_api import sync_playwright

URL = "https://ostrov.edupage.sk"
bezi = True
aktualny_stav = "Spúšťam prehliadač na pozadí..."

def vytvor_ikonu():
    obrazok = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    kreslenie = ImageDraw.Draw(obrazok)
    kreslenie.ellipse((4, 4, 60, 60), fill=(0, 102, 204, 255))
    kreslenie.polygon([(32, 14), (20, 42), (44, 42)], fill=(255, 215, 0, 255))
    kreslenie.ellipse((28, 42, 36, 50), fill=(255, 215, 0, 255))
    return obrazok

def zobraz_upozornenie():
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showwarning(
        "Časovač zvonenia",
        "Ostáva 5 minút do konca vyučovacej hodiny!",
        parent=root
    )
    root.destroy()

def sledovanie_na_pozadi(ikona):
    global aktualny_stav, bezi
    upozornene_pre_tuto_hodinu = False

    try:
        with sync_playwright() as p:
            aktualny_stav = "Otváram stránku EduPage..."
            # Použije vstavaný Microsoft Edge vo Windowse (bez problémov s cestou v .exe)
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.goto(URL, wait_until="domcontentloaded", timeout=20000)

            while bezi:
                try:
                    # Hľadá priamo v sekcii Časovač (box s nadpisom Časovač)
                    text_stranky = page.inner_text("body")
                    zhoda = re.search(
                        r"Časovač[\s\S]{0,150}?\b0?(\d{1,2}):([0-5]\d)\b",
                        text_stranky,
                        re.IGNORECASE
                    )

                    if zhoda:
                        minuty = int(zhoda.group(1))
                        sekundy = int(zhoda.group(2))
                        aktualny_stav = f"Do zvonenia: {minuty:02d}:{sekundy:02d}"
                        ikona.title = f"EduPage | {aktualny_stav}"

                        if minuty == 5 and sekundy == 0:
                            if not upozornene_pre_tuto_hodinu:
                                upozornene_pre_tuto_hodinu = True
                                threading.Thread(target=zobraz_upozornenie, daemon=True).start()
                        elif minuty != 5:
                            upozornene_pre_tuto_hodinu = False
                    else:
                        aktualny_stav = "Časovač momentálne neodpočítava (prestávka / po vyučovaní)."
                        ikona.title = "EduPage | Neaktívny časovač"

                except Exception as chyba_citania:
                    aktualny_stav = f"Chyba čítania: {str(chyba_citania)[:60]}"

                time.sleep(1)

            browser.close()
    except Exception as kriticka_chyba:
        aktualny_stav = f"Chyba spustenia: {str(kriticka_chyba)}"
        ikona.title = "EduPage | Chyba spustenia"

def zobrazit_stav(ikona, polozka):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo("Aktuálny stav", aktualny_stav, parent=root)
    root.destroy()

def ukoncit_aplikaciu(ikona, polozka):
    global bezi
    bezi = False
    ikona.stop()

def main():
    menu = (
        item("Zobraziť aktuálny stav", zobrazit_stav),
        item("Ukončiť sledovač", ukoncit_aplikaciu)
    )
    ikona = pystray.Icon("EduPageZvonenie", vytvor_ikonu(), "EduPage Sledovač", menu)

    vlakno = threading.Thread(target=sledovanie_na_pozadi, args=(ikona,), daemon=True)
    vlakno.start()

    ikona.run()

if __name__ == "__main__":
    main()

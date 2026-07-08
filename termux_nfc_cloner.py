#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import shutil
import time

DB_FILE = "tags_db.json"

# Detect the correct termux-nfc executable (NOT termux-nfc-read, which does not exist)
TERMUX_NFC_BIN = shutil.which("termux-nfc")
if not TERMUX_NFC_BIN:
    # Fallback to absolute path (useful when running as root or in non-standard shell)
    ABS_PATH = "/data/data/com.termux/files/usr/bin/termux-nfc"
    if os.path.exists(ABS_PATH):
        TERMUX_NFC_BIN = ABS_PATH

# ANSI Colors for premium terminal aesthetics (Green-only Matrix style)
C_BLUE = "\033[92m"
C_CYAN = "\033[92m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[92m"
C_RED = "\033[92m"
C_PURPLE = "\033[92m"
C_BOLD = "\033[1m"
C_END = "\033[0m"

def print_header():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{C_GREEN}{C_BOLD}================================================={C_END}")
    print(f"{C_GREEN}{C_BOLD}               NFC  CLONER - CLI                 {C_END}")
    print(f"{C_GREEN}{C_BOLD}               by Simone Santoro                 {C_END}")
    print(f"{C_GREEN}{C_BOLD}================================================={C_END}")

def check_termux_api():
    if not TERMUX_NFC_BIN:
        print_header()
        print(f"{C_RED}{C_BOLD}[!] ERRORE: Comando 'termux-nfc' non trovato!{C_END}\n")
        print("Per poter scansionare tag NFC da Termux è necessario:")
        print(f"1. Installare l'app {C_YELLOW}Termux:API{C_END} da F-Droid.")
        print(f"2. Installare il pacchetto nel terminale eseguendo: {C_GREEN}pkg install termux-api{C_END}")
        print("3. Assicurarsi che l'NFC e i permessi NFC per Termux siano attivi sul telefono.")
        print("\nPremi INVIO per uscire...")
        input()
        sys.exit(1)

def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_db(db):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"{C_RED}Errore durante il salvataggio del database: {e}{C_END}")

def scan_tag():
    print_header()
    print(f"{C_YELLOW}{C_BOLD}[*] IN ATTESA DI UN TAG NFC...{C_END}")
    print("Avvicina un tag NFC al retro del tuo smartphone.")
    print("Premi Ctrl+C per annullare.")
    print(f"{C_PURPLE}-------------------------------------------------{C_END}")
    
    try:
        # Step 1: Read the UID of the tag using 'termux-nfc -r id'
        # This works for both NDEF and non-NDEF cards and returns {"card_id": "XXXX"}
        proc_id = subprocess.Popen(
            [TERMUX_NFC_BIN, "-r", "id"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout_id, stderr_id = proc_id.communicate()
        
        if proc_id.returncode != 0:
            print(f"\n{C_RED}[!] Errore durante la scansione NFC: {stderr_id.strip()}{C_END}")
            time.sleep(2)
            return None
        
        id_data = json.loads(stdout_id)
        # Output format: {"card_id": "04A3B2C1"}
        uid = id_data.get("card_id", "Sconosciuto").strip()

        # Step 2: Try to read NDEF payload using 'termux-nfc -r short'
        payload = "Nessun payload NDEF leggibile"
        tag_type = "NFC Tag"
        proc_ndef = subprocess.Popen(
            [TERMUX_NFC_BIN, "-r", "short"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout_ndef, _ = proc_ndef.communicate()
        if proc_ndef.returncode == 0 and stdout_ndef.strip():
            try:
                ndef_data = json.loads(stdout_ndef)
                # NDEF output structure: {"Record": [{"Payload": "...", ...}]}
                records = ndef_data.get("Record", [])
                if records:
                    tag_type = "NDEF Tag"
                    payload = "\n".join(
                        r.get("Payload", "") for r in records if r.get("Payload")
                    ).strip() or "Payload vuoto"
            except (json.JSONDecodeError, AttributeError):
                # Not JSON or different format, use raw output
                payload = stdout_ndef.strip()
        
        scanned = {
            "uid": uid,
            "type": tag_type,
            "payload": payload,
            "timestamp": int(time.time())
        }
        
        print(f"\n{C_GREEN}{C_BOLD}[+] Tag Rilevato!{C_END}")
        print(f"UID: {scanned['uid']}")
        print(f"Tipo: {scanned['type']}")
        return scanned
        
    except KeyboardInterrupt:
        print(f"\n{C_RED}Scansione interrotta.{C_END}")
        time.sleep(1)
        return None
    except Exception as e:
        print(f"\n{C_RED}[!] Errore: {e}{C_END}")
        time.sleep(2)
        return None

def show_database(db):
    print_header()
    if not db:
        print(f"{C_YELLOW}Database vuoto. Nessun tag memorizzato.{C_END}")
    else:
        print(f"{C_BOLD}Elenco Tag Salvati ({len(db)}):{C_END}\n")
        for idx, tag in enumerate(db, 1):
            date_str = time.strftime('%d/%m/%Y %H:%M', time.localtime(tag['timestamp']))
            print(f"{C_CYAN}[{idx}]{C_END} {C_BOLD}{tag.get('name', 'Tag Senza Nome')}{C_END}")
            print(f"    UID: {tag['uid']}")
            print(f"    Tipo: {tag['type']}")
            print(f"    Data: {date_str}")
            print(f"    Dati: {tag['payload'][:60]}..." if len(tag['payload']) > 60 else f"    Dati: {tag['payload']}")
            print(f"{C_PURPLE}    ---------------------------------------------{C_END}")
            
    print("\nPremi INVIO per tornare al menu...")
    input()

def delete_tag_menu(db):
    print_header()
    if not db:
        print(f"{C_YELLOW}Database vuoto. Niente da eliminare.{C_END}")
        print("\nPremi INVIO per continuare...")
        input()
        return db
        
    print(f"{C_BOLD}Seleziona il tag da eliminare:{C_END}\n")
    for idx, tag in enumerate(db, 1):
        print(f"{C_RED}[{idx}]{C_END} {tag.get('name', 'Tag')} (UID: {tag['uid']})")
        
    print(f"\n{C_CYAN}[0]{C_END} Annulla")
    print(f"{C_PURPLE}-------------------------------------------------{C_END}")
    
    try:
        scelta = input(f"{C_BOLD}Inserisci il numero: {C_END}")
        idx = int(scelta)
        if idx == 0:
            return db
        if 1 <= idx <= len(db):
            deleted = db.pop(idx - 1)
            print(f"\n{C_GREEN}[+] Tag '{deleted.get('name')}' eliminato con successo.{C_END}")
            save_db(db)
        else:
            print(f"\n{C_RED}[!] Scelta non valida.{C_END}")
    except ValueError:
        print(f"\n{C_RED}[!] Inserisci un numero valido.{C_END}")
        
    time.sleep(1.5)
    return db

def show_emulation_info():
    print_header()
    print(f"{C_YELLOW}{C_BOLD}GUIDA ALL'EMULAZIONE NFC SU ANDROID{C_END}\n")
    print(f"{C_BOLD}1. Emulazione Standard (HCE):{C_END}")
    print("   Android supporta la Host Card Emulation (HCE) solo per protocolli smart card")
    print("   ISO-DEP (ISO 14443-4) e richiede la registrazione di identificativi AID specifici.")
    print("   Questa CLI di Termux NON può registrare servizi HCE a livello di OS.")
    print(f"   {C_CYAN}--> Utilizza l'app nativa compilata (NFC Cloner APK) per avviare l'HCE.{C_END}\n")
    
    print(f"{C_BOLD}2. Clonazione UID Hardware (Con Root):{C_END}")
    print("   Per clonare tessere di sicurezza (Mifare Classic, ecc.) cambiando l'UID hardware,")
    print("   è necessario disporre di privilegi di ROOT sul telefono e patchare i file di")
    print("   configurazione NFC (`libnfc-nxp.conf` o `libnfc-brcm.conf`) per poi riavviare il chip.")
    print(f"   {C_CYAN}--> L'app nativa APK fornisce un'interfaccia sicura e automatizzata.{C_END}")
    print("   Se desideri farlo manualmente da Termux CLI con ROOT, esegui:")
    print(f"   {C_GREEN}su -c \"mount -o rw,remount /vendor && nano /vendor/etc/libnfc-nxp.conf\"{C_END}")
    print(f"   modifica {C_YELLOW}NXP_DEFAULT_SE_UID{C_END} e riavvia con: {C_GREEN}su -c \"svc nfc disable && svc nfc enable\"{C_END}")
    
    print("\nPremi INVIO per tornare al menu...")
    input()

def main():
    check_termux_api()
    db = load_db()
    
    while True:
        print_header()
        print(f"{C_GREEN}[1]{C_END} Scansiona Tag NFC")
        print(f"{C_GREEN}[2]{C_END} Visualizza Database Tag")
        print(f"{C_GREEN}[3]{C_END} Elimina Tag Salvato")
        print(f"{C_GREEN}[4]{C_END} Info Emulazione (HCE & Root)")
        print(f"{C_RED}[5]{C_END} Esci")
        print(f"{C_PURPLE}-------------------------------------------------{C_END}")
        
        scelta = input(f"{C_BOLD}Scegli un'opzione: {C_END}")
        
        if scelta == "1":
            new_tag = scan_tag()
            if new_tag:
                name = input(f"\n{C_BOLD}Assegna un nome a questo tag: {C_END}")
                new_tag["name"] = name.strip() if name.strip() else f"Tag_{new_tag['uid']}"
                db.append(new_tag)
                save_db(db)
                print(f"{C_GREEN}[+] Tag salvato nel database!{C_END}")
                time.sleep(1.5)
        elif scelta == "2":
            show_database(db)
        elif scelta == "3":
            db = delete_tag_menu(db)
        elif scelta == "4":
            show_emulation_info()
        elif scelta == "5":
            print_header()
            print(f"\n{C_CYAN}Grazie per aver usato NFC Cloner. Arrivederci!{C_END}\n")
            break
        else:
            print(f"\n{C_RED}[!] Scelta non valida.{C_END}")
            time.sleep(1)

if __name__ == "__main__":
    main()

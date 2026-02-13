import json
import re
from collections import deque
from pyllist import dllist
from datetime import datetime, timedelta

class Pacientas:
    def __init__(self, vardas, pavarde, asmens_kodas, istorija=None, simptomai=""):
        self.vardas = vardas
        self.pavarde = pavarde
        self.asmens_kodas = asmens_kodas
        self.istorija = deque(istorija) if istorija else deque()
        self.simptomai = simptomai
    
    def prideti_i_istorija(self, irasas):
        self.istorija.append(irasas)
    
    def __str__(self):
        return f"{self.vardas} {self.pavarde} (AK: {self.asmens_kodas})"

class Lapelis:
    def __init__(self, laikas, pacientas=None, simptomai="", papildomas=False, skubus=False):
        self.laikas = laikas
        self.pacientas = pacientas
        self.simptomai = simptomai
        self.papildomas = papildomas
        self.skubus = skubus
        self.diagnoze = ""
    
    def ar_uzimtas(self):
        return self.pacientas is not None
    
    def __str__(self):
        if not self.ar_uzimtas():
            return f"{self.laikas} - LAISVAS"
        
        zenklas = ""
        if self.skubus:
            zenklas = " [SKUBUS!]"
        elif self.papildomas:
            zenklas = " [PAPILDOMAS]"
        
        return f"{self.laikas}{zenklas} - {self.pacientas}"


class TvarkarascioSistema:
    DARBO_LAIKAS = [
        ("07:00", "09:00"),
        ("09:00", "11:00"),
        ("12:00", "14:00"),
        ("14:00", "16:00")
    ]
    
    def __init__(self):
        self.tvarkarastis = dllist()
        self.pacientai_db = {}
        self.siandien = datetime.now().strftime("%Y-%m-%d")
        self.inicijuoti_sistema()
    
    def inicijuoti_sistema(self):
        self.nuskaityti_pacientus()
        self.nuskaityti_tvarkarasti()
        self.sukurti_aptarnautu_faila()
    
    def nuskaityti_pacientus(self):
        with open('Pacientai.json', 'r', encoding='utf-8') as f:
            pacientai_data = json.load(f)
        
        for p in pacientai_data:
            pacientas = Pacientas(
                p['vardas'],
                p['pavarde'],
                p['asmens_kodas'],
                p.get('istorija', []),
                p.get('simptomai', '')
            )
            self.pacientai_db[p['asmens_kodas']] = pacientas
    
    def sukurti_aptarnautu_faila(self):
        failo_vardas = f"Aptarnauti-{self.siandien}.json"
        try:
            with open(failo_vardas, 'r', encoding='utf-8') as f:
                pass
        except FileNotFoundError:
            with open(failo_vardas, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def nuskaityti_tvarkarasti(self):
        failo_vardas = f"Tvarkarastis-{self.siandien}.json"
        
        with open(failo_vardas, 'r', encoding='utf-8') as f:
            rezervacijos = json.load(f)
        
        rezervacijos_dict = {r['laikas']: r['asmens_kodas'] for r in rezervacijos}
        
        for pradzia, pabaiga in self.DARBO_LAIKAS:
            dekas = deque()
            laikai = self.generuoti_laikus(pradzia, pabaiga)
            
            for laikas in laikai:
                if laikas in rezervacijos_dict:
                    asmens_kodas = rezervacijos_dict[laikas]
                    pacientas = self.pacientai_db.get(asmens_kodas)
                    if pacientas:
                        lapelis = Lapelis(laikas, pacientas, pacientas.simptomai)
                    else:
                        lapelis = Lapelis(laikas)
                else:
                    lapelis = Lapelis(laikas)
                
                dekas.append(lapelis)
            
            self.tvarkarastis.append(dekas)

    def generuoti_laikus(self, pradzia, pabaiga):
        intervalai = []
        pradzia_obj = datetime.strptime(pradzia, "%H:%M")
        pabaiga_obj = datetime.strptime(pabaiga, "%H:%M")
        
        dabartinis = pradzia_obj
        while dabartinis < pabaiga_obj:
            kitas = dabartinis + timedelta(minutes=15)
            pradzia_str = dabartinis.strftime('%H:%M').lstrip('0') or '0:00'
            pabaiga_str = kitas.strftime('%H:%M').lstrip('0') or '0:00'
            intervalas = f"{pradzia_str}-{pabaiga_str}"
            intervalai.append(intervalas)
            dabartinis = kitas
        
        return intervalai
    
    def validuoti_asmens_koda(self, kodas):
        if not re.match(r'^[3-6]\d{10}$', kodas):
            return False
        return True
    
    def validuoti_varda(self, tekstas):
        if not re.match(r'^[a-zA-ZąčęėįšųūžĄČĘĖĮŠŲŪŽ]+$', tekstas):
            return False
        return True
    
    def gauti_artimiausio_paciento(self):
        for dekas_node in self.tvarkarastis.iternodes():
            dekas = dekas_node.value
            for lapelis in dekas:
                if lapelis.ar_uzimtas() and not lapelis.diagnoze:
                    return lapelis
        return None
    
    def atspausdinti_tvarkarasti(self):
        print("\n" + "="*70)
        print("ŠEIMOS GYDYTOJO DIENOS TVARKARAŠTIS".center(70))
        print(f"{self.siandien}".center(70))
        print("="*70)
        
        dalis_nr = 1
        for dekas_node in self.tvarkarastis.iternodes():
            dekas = dekas_node.value
            pradzia, pabaiga = self.DARBO_LAIKAS[dalis_nr - 1]
            
            print(f"\n{'─'*70}")
            print(f"  {dalis_nr} DALIS: {pradzia} - {pabaiga}")
            print(f"{'─'*70}")
            
            papildomi = sum(1 for l in dekas if l.papildomas)
            skubus = sum(1 for l in dekas if l.skubus)
            
            if papildomi > 0 or skubus > 0:
                info = []
                if skubus > 0:
                    info.append(f"Skubūs: {skubus}")
                if papildomi > 0:
                    info.append(f"Papildomi: {papildomi}")
                print(f"  [{', '.join(info)}]")
            
            for lapelis in dekas:
                if lapelis.ar_uzimtas():
                    ikona = "  ●"
                    if lapelis.skubus:
                        ikona = "  🚨"
                    elif lapelis.papildomas:
                        ikona = "  +"
                    
                    statusas = " ✓" if lapelis.diagnoze else ""
                    print(f"{ikona} {lapelis}{statusas}")
                    if lapelis.simptomai:
                        print(f"      Simptomai: {lapelis.simptomai}")
                else:
                    print(f"  ○ {lapelis}")
            
            dalis_nr += 1
        
        print("\n" + "="*70)
        print("Legenda: 🚨-Skubus | +-Papildomas | ●-Užimtas | ○-Laisvas | ✓-Priimtas")
        print("="*70 + "\n")
    
    def prideti_papildoma_pacienta(self):
        print("\n--- PAPILDOMO PACIENTO PRIDĖJIMAS ---")
        
        asmens_kodas = input("Asmens kodas: ").strip()
        if not self.validuoti_asmens_koda(asmens_kodas):
            print("! Neteisingas asmens kodas (turi būti 11 skaitmenų ir prasidėti 3-6)")
            return
        
        vardas = input("Vardas: ").strip()
        if not self.validuoti_varda(vardas):
            print("! Neteisingas vardas (tik lotyniški/lietuviški simboliai)")
            return
        
        pavarde = input("Pavardė: ").strip()
        if not self.validuoti_varda(pavarde):
            print("! Neteisinga pavardė (tik lotyniški/lietuviški simboliai)")
            return
        
        simptomai = input("Simptomai: ").strip()
        
        print("\nPasirinkite dienos dalį:")
        for i, (p, pb) in enumerate(self.DARBO_LAIKAS, 1):
            print(f"  {i}. {p}-{pb}")
        
        try:
            pasirinkimas = int(input("Dalis (1-4): "))
            if pasirinkimas < 1 or pasirinkimas > 4:
                print("! Neteisingas pasirinkimas!")
                return
        except ValueError:
            print("! Neteisingas įvestis!")
            return
        
        dekas = self.tvarkarastis.nodeat(pasirinkimas - 1).value
        papildomi_sk = sum(1 for l in dekas if l.papildomas)
        
        if papildomi_sk >= 2:
            print("! Šioje dalyje jau yra 2 papildomi pacientai!")
            return
        
        pacientas = Pacientas(vardas, pavarde, asmens_kodas, [], simptomai)
        self.pacientai_db[asmens_kodas] = pacientas

        pradzia, pabaiga = self.DARBO_LAIKAS[pasirinkimas - 1]
        laikas = f"{pabaiga} (papildomas)"
        lapelis = Lapelis(laikas, pacientas, simptomai, papildomas=True)
        dekas.append(lapelis)
        
        print(f"✓ Papildomas pacientas {pacientas} pridėtas")
    
    def prideti_skubu_pacienta(self):
        """Prideda skubų pacientą"""
        print("\n--- SKUBAUS PACIENTO PRIDĖJIMAS ---")
        
        asmens_kodas = input("Asmens kodas: ").strip()
        if not self.validuoti_asmens_koda(asmens_kodas):
            print("! Neteisingas asmens kodas (turi būti 11 skaitmenų, prasidėti 3-6)")
            return
        
        vardas = input("Vardas: ").strip()
        if not self.validuoti_varda(vardas):
            print("! Neteisingas vardas (tik lotyniški/lietuviški simboliai)")
            return
        
        pavarde = input("Pavardė: ").strip()
        if not self.validuoti_varda(pavarde):
            print("! Neteisinga pavardė (tik lotyniški/lietuviški simboliai)")
            return
        
        simptomai = input("Simptomai: ").strip()
        
        print("\nPasirinkite dienos dalį:")
        for i, (p, pb) in enumerate(self.DARBO_LAIKAS, 1):
            print(f"  {i}. {p}-{pb}")
        
        try:
            pasirinkimas = int(input("Dalis (1-4): "))
            if pasirinkimas < 1 or pasirinkimas > 4:
                print("! Neteisingas pasirinkimas!")
                return
        except ValueError:
            print("! Neteisingas įvestis!")
            return
        
        pacientas = Pacientas(vardas, pavarde, asmens_kodas, [], simptomai)
        self.pacientai_db[asmens_kodas] = pacientas
        
        dekas = self.tvarkarastis.nodeat(pasirinkimas - 1).value
        pradzia, _ = self.DARBO_LAIKAS[pasirinkimas - 1]
        laikas = f"{pradzia} (SKUBUS)"
        lapelis = Lapelis(laikas, pacientas, simptomai, skubus=True)
        dekas.appendleft(lapelis) 
        
        print(f"✓ SKUBUS pacientas {pacientas} pridėtas")
    
    def priimti_pacienta(self):
        artimiausia = self.gauti_artimiausio_paciento()
        
        if not artimiausia:
            print("\n! Nėra laukiančių pacientų!")
            return
        
        print("\n" + "="*50)
        print("PACIENTO PRIĖMIMAS")
        print("="*50)
        print(f"Laikas: {artimiausia.laikas}")
        print(f"Pacientas: {artimiausia.pacientas}")
        print(f"Simptomai: {artimiausia.simptomai}")
        print("="*50)
        
        while True:
            diagnoze = input("\nĮveskite diagnozę: ").strip()
            if diagnoze:
                break
            print("! Diagnozė negali būti tuščia!")
        
        artimiausia.diagnoze = diagnoze
        
        irasas = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "simptomai": artimiausia.simptomai,
            "diagnoze": diagnoze
        }
        artimiausia.pacientas.prideti_i_istorija(irasas)
        
        self.irasyti_i_aptarnautus(artimiausia)
        
        for dekas_node in self.tvarkarastis.iternodes():
            dekas = dekas_node.value
            if artimiausia in dekas:
                dekas.remove(artimiausia)
                break
        
        print(f"✓ Pacientas {artimiausia.pacientas} priimtas ir įrašytas į aptarnautų sąrašą")
    
    def irasyti_i_aptarnautus(self, lapelis):
        failo_vardas = f"Aptarnauti-{self.siandien}.json"
        
        with open(failo_vardas, 'r', encoding='utf-8') as f:
            aptarnauti = json.load(f)
        
        irasas = {
            "laikas": lapelis.laikas,
            "vardas": lapelis.pacientas.vardas,
            "pavarde": lapelis.pacientas.pavarde,
            "asmens_kodas": lapelis.pacientas.asmens_kodas,
            "simptomai": lapelis.simptomai,
            "diagnoze": lapelis.diagnoze,
            "papildomas": lapelis.papildomas,
            "skubus": lapelis.skubus
        }
        
        aptarnauti.append(irasas)
        
        with open(failo_vardas, 'w', encoding='utf-8') as f:
            json.dump(aptarnauti, f, ensure_ascii=False, indent=2)


def rodyti_menu():
    print("\n" + "╔" + "═"*48 + "╗")
    print("║" + " ŠEIMOS GYDYTOJO SISTEMA ".center(48) + "║")
    print("╚" + "═"*48 + "╝")
    print("\n1. Peržiūrėti tvarkaraštį")
    print("2. Pridėti papildomą pacientą")
    print("3. Pridėti skubų pacientą")
    print("4. Priimti pacientą")
    print("5. Išeiti")
    print("-" * 50)


def main():
    print("\n" + "="*50)
    print("ŠEIMOS GYDYTOJO SISTEMA")
    print("="*50)
    
    sistema = TvarkarascioSistema()
    
    artimiausia = sistema.gauti_artimiausio_paciento()
    if artimiausia:
        print("\n" + "┌" + "─"*48 + "┐")
        print("│" + " ARTIMIAUSIA KONSULTACIJA ".center(48) + "│")
        print("├" + "─"*48 + "┤")
        ikona = "🚨 " if artimiausia.skubus else ""
        print(f"│ {ikona}{str(artimiausia):<46}│")
        print("└" + "─"*48 + "┘")
    
    while True:
        rodyti_menu()
        pasirinkimas = input("Pasirinkite (1-5): ").strip()
        
        if pasirinkimas == '1':
            sistema.atspausdinti_tvarkarasti()
        elif pasirinkimas == '2':
            sistema.prideti_papildoma_pacienta()
        elif pasirinkimas == '3':
            sistema.prideti_skubu_pacienta()
        elif pasirinkimas == '4':
            sistema.priimti_pacienta()
        elif pasirinkimas == '5':
            print("\n✓ Viso gero!")
            break
        else:
            print("\n! Neteisingas pasirinkimas!")


if __name__ == "__main__":
    main()
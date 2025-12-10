# 🏠 SmartHome WebApp: Systém pro Správu Chytré Domácnosti

## 🚀 Přehled Projektu

Tento repozitář obsahuje zdrojové kódy a dokumentaci k bakalářskému projektu, který se zabývá vývojem **webové aplikace pro efektivní správu a monitorování chytré domácnosti**.

Projekt využívá **mikro-framework Flask** k vytvoření kompletního full-stack řešení, které efektivně zpracovává data z externích IoT zařízení (M5Stack, ESP) zasílaná přes API. Cílem je vytvořit aplikaci, která je schopna sbírat, ukládat, statisticky zpracovávat a vizualizovat tato data, a zároveň poskytovat rozhraní pro přímé ovládání modulů.

---

## 🛠️ Technologie a Architektura (Full-Stack Python)

Projekt je postaven na lehkém a flexibilním Python stacku:

| Komponenta | Technologie | Popis |
| :--- | :--- | :--- |
| **Full-Stack** | Python 🐍 & **Flask** | Jediný framework pro Backend API, business logiku i renderování Frontendu. |
| **Sběr dat** | Vlastní API Endpoints | Flask API slouží jako příjemce dat (HTTP POST) z M5Stack a ESP zařízení. |
| **Frontend** | Jinja2 Templates & JavaScript | Flask renderuje UI (Jinja2) a JS knihovny (např. Chart.js) zajišťují vizualizaci. |
| **Databáze** | **SQLite** (s modulem `sqlite3`) | **Lehká, souborová databáze** pro ukládání dat ze senzorů. Použití čistého SQL. |
| **Hardware** | M5Stack, ESP32/8266 (Simulace) | Zařízení simulují senzory a komunikují s Flask API přes Ethernet/Wi-Fi. |

---

## ✨ Klíčové Funkce

Webová aplikace implementuje následující klíčové moduly, které tvoří jádro funkcionality chytré domácnosti:

1.  **Sběr a Ukládání Dat přes API:** Příjem a bezpečné uložení naměřených dat (teplota, vlhkost atd.) z IoT zařízení.
2.  **Statistické Zpracování:** Provádění analýz a výpočet časových statistik nad uloženými daty.
3.  **Dynamická Vizualizace:** Zobrazování dat v přehledných grafech a interaktivních dashboardech.
4.  **Ovládání Výstupů (Aktuátory):** Možnost vzdáleně odesílat příkazy zpět do zařízení (např. spínání relé).

---

## 📋 Plán Implementace (Zadání)

Implementace je striktně řízena body v zadání práce:

1.  Vypracování rozvahy možných řešení a frameworků.
2.  **Výběr Flasku s SQLite** jako nejvhodnějšího řešení.
3.  Návrh blokového schématu propojení komponent.
4.  Vytvoření vývojového diagramu a realizace aplikace.
5.  **Tvorba databáze (s čistým SQL)**, statistické zpracování a vizualizace dat.
6.  Implementace ovládání výstupů a nastavení parametrů senzorů.
7.  Otestování aplikace a zhodnocení dosažených parametrů.

---

## 🎓 Informace o Práci

* **ID Projektu:** 2713
* **Student:** Martin Těhník
* **Vedoucí práce:** Ing. Petr Bílek Ph.D.
* **Akademický rok:** 2025/2026
* **Obor:** Bakalářské obory -> Informační technologie

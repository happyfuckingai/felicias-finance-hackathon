#!/usr/bin/env python3
"""
🚀 Run AI Trading Command Center

Startar den ultimata integrerade instrumentpanelen där allt händer samtidigt:
- AI Chat Partner (vänster)
- Live Portfolio & Market View (höger)
- Real-time updates och interaktioner
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Kontrollera att nödvändiga paket är installerade"""
    required_packages = [
        'streamlit>=1.28.0',
        'plotly>=5.15.0',
        'pandas>=2.0.0',
        'numpy>=1.24.0'
    ]

    missing_packages = []
    for package in required_packages:
        package_name = package.split('>=')[0]
        try:
            __import__(package_name.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("🚨 Saknar följande paket. Installerar...")
        print(f"📦 Paket: {', '.join(missing_packages)}")

        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--quiet'
            ] + missing_packages)
            print("✅ Alla paket installerade!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Misslyckades installera paket: {e}")
            print("Försök manuellt: pip install streamlit plotly pandas numpy")
            return False

    return True

def start_command_center():
    """Starta AI Trading Command Center"""
    command_center_path = Path(__file__).parent / "ai_command_center.py"

    if not command_center_path.exists():
        print(f"❌ Hittar inte ai_command_center.py på {command_center_path}")
        return False

    print("🚀 STARTAR AI TRADING COMMAND CENTER")
    print("=" * 60)
    print("🎯 Detta är den ultimata integrerade instrumentpanelen!")
    print()
    print("🎮 Vad du kommer att uppleva:")
    print("• 🤖 AI Chat Partner - prata naturligt på svenska")
    print("• 📊 Live Portfolio - realtidsuppdateringar")
    print("• 🎯 AI Trading Signals - smarta rekommendationer")
    print("• 🛡️ Risk Radar - avancerade riskberäkningar")
    print("• 🌍 Market Intelligence - live sentimentanalys")
    print()
    print("💡 Prova dessa kommandon:")
    print("• 'Visa risk för ethereum'")
    print("• 'Analysera bitcoin'")
    print("• 'Heta signaler'")
    print("• 'Portfolio status'")
    print()
    print("⚡ Quick Actions:")
    print("• 📊 Portfolio Status - översikt")
    print("• 🎯 Hot Signals - aktuella signaler")
    print("• 🛡️ Risk Check - riskanalys")
    print()
    print("🎯 Layout:")
    print("• Vänster: AI Chat Partner (permanent)")
    print("• Höger: Live Dashboard (allt synligt samtidigt)")
    print("• Inga flikar - allt händer live!")
    print()
    print("⏹️ Tryck Ctrl+C för att stoppa")
    print("=" * 60)

    try:
        # Starta command center med rätt inställningar
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent)

        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run',
            str(command_center_path),
            '--server.headless', 'true',
            '--server.address', '0.0.0.0',
            '--server.port', '8501',
            '--browser.gatherUsageStats', 'false'
        ], env=env, check=True)

    except KeyboardInterrupt:
        print("\n⏹️ AI Trading Command Center stoppad av användare")
        print("🎉 Tack för att du upplevde framtiden av trading!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Misslyckades starta Command Center: {e}")
        return False
    except FileNotFoundError:
        print("❌ Streamlit är inte installerat eller hittas inte")
        print("Installera med: pip install streamlit")
        return False

    return True

def main():
    """Huvudfunktion"""
    print("🚀 AI TRADING COMMAND CENTER")
    print("=" * 50)
    print("Den ultimata integrerade instrumentpanelen där allt händer samtidigt!")
    print()

    # Kontrollera requirements
    if not check_requirements():
        return False

    print("✅ Alla dependencies klara!")
    print()

    # Starta command center
    success = start_command_center()

    if success:
        print("\n✅ Command Center avslutad!")
        print("🎉 Du upplevde hela kraften av AI-driven trading!")
    else:
        print("\n❌ Något gick fel.")
        print("Försök felsöka:")
        print("1. pip install -r requirements.txt")
        print("2. Kontrollera att ai_command_center.py finns")
        print("3. python -c \"import streamlit; print('Streamlit OK')\"")
        return False

    return True

if __name__ == "__main__":
    # Ändra till rätt directory
    os.chdir(Path(__file__).parent)

    try:
        main()
    except Exception as e:
        print(f"❌ Oväntat fel: {e}")
        print("Försök: python ai_command_center.py direkt")
        sys.exit(1)
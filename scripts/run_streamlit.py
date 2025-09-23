#!/usr/bin/env python3
"""
🚀 Quick Start Script for AI Crypto Trading Demo

Denna fil gör det superenkelt att starta Streamlit-appen för demo av
den AI-driven crypto trading plattformen.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Kontrollera att nödvändiga paket är installerade"""
    required_packages = [
        'streamlit',
        'plotly',
        'pandas',
        'numpy',
        'aiohttp'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("🚨 Saknar följande paket. Installerar...")
        print(f"📦 Paket: {', '.join(missing_packages)}")

        # Installera saknade paket
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--quiet'
            ] + missing_packages)
            print("✅ Alla paket installerade!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Misslyckades installera paket: {e}")
            print("Försök manuellt: pip install -r requirements.txt")
            return False

    return True

def start_streamlit():
    """Starta Streamlit-appen"""
    streamlit_path = Path(__file__).parent / "streamlit_app.py"

    if not streamlit_path.exists():
        print(f"❌ Hittar inte streamlit_app.py på {streamlit_path}")
        return False

    print("⚠️  OBS: Denna version har flikar.")
    print("🚀 För den ultimata upplevelsen, använd istället:")
    print("python crypto/run_command_center.py")
    print()
    print("Den versionen har:")
    print("• 🤖 AI Chat permanent synlig (ingen flikar)")
    print("• 📊 Live Dashboard alltid uppdaterad")
    print("• 🎯 Allt händer samtidigt i realtid")
    print("• ⚡ Interaktiva AI-svar med knappar")
    print()
    print("Men du kan fortsätta med denna version om du vill...")
    print("=" * 50)
    print("📱 Öppna din webbläsare på: http://localhost:8501")
    print("🎯 Traditionell flik-baserad demo")
    print("=" * 50)
    print()
    print("💡 Vad du kan göra:")
    print("• 🟢 Klicka på 'Initialize AI Trader' för att starta systemet")
    print("• 💬 Prata naturligt med AI:n (t.ex. 'analysera bitcoin')")
    print("• 📊 Kolla Portfolio Dashboard för realtidsdata")
    print("• 🎯 Se AI Trading Signals")
    print("• 🛡️ Utforska Risk Analytics")
    print("• ⚙️ Justera riskinställningar i vänster sidebar")
    print()
    print("⏹️ Tryck Ctrl+C för att stoppa")
    print("=" * 50)

    try:
        # Starta streamlit med rätt working directory
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent)

        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run',
            str(streamlit_path),
            '--server.headless', 'true',
            '--server.address', '0.0.0.0',
            '--server.port', '8501'
        ], env=env, check=True)

    except KeyboardInterrupt:
        print("\n⏹️ Stoppad av användare")
    except subprocess.CalledProcessError as e:
        print(f"❌ Misslyckades starta Streamlit: {e}")
        print("Försök installera dependencies: pip install -r requirements.txt")
        return False
    except FileNotFoundError:
        print("❌ Streamlit är inte installerat eller hittas inte")
        print("Installera med: pip install streamlit")
        return False

    return True

def main():
    """Huvudfunktion"""
    print("🤖 AI-Driven Crypto Trading Platform - Demo")
    print("=" * 50)

    # Kontrollera requirements
    if not check_requirements():
        return False

    # Starta appen
    success = start_streamlit()

    if success:
        print("\n✅ Demo avslutad!")
        print("🎉 Tack för att du testade AI-driven crypto trading!")
    else:
        print("\n❌ Något gick fel. Kontrollera ovanstående felmeddelanden.")
        return False

    return True

if __name__ == "__main__":
    # Ändra till rätt directory
    os.chdir(Path(__file__).parent)

    try:
        main()
    except Exception as e:
        print(f"❌ Oväntat fel: {e}")
        sys.exit(1)
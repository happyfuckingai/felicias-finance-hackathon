"""
Wallet Handler för HappyOS Crypto - Wallet-hantering och transaktioner.
"""
import logging
import os
from typing import Dict, Any
from datetime import datetime
from eth_account import Account
from web3 import Web3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ..core.integrations.contracts import ContractDeployer, BASE_TESTNET_CONFIG

logger = logging.getLogger(__name__)

class WalletHandler:
    """Hanterar wallet-operationer."""
    
    def __init__(self):
        """Initialize WalletHandler."""
        logger.info("WalletHandler initialiserad")
    
    async def handle(self, handler_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle wallet-relaterade kommandon.
        
        Args:
            handler_input: Input från CryptoSkill
            
        Returns:
            Result av wallet-operationen
        """
        action = handler_input.get('action', 'default')
        fields = handler_input.get('fields', {})
        command = handler_input.get('command', '')
        
        try:
            if action in ['skapa', 'create', 'new']:
                return await self._create_wallet()
            elif action in ['visa', 'show', 'balance', 'saldo']:
                return await self._show_balance(fields)
            elif action in ['skicka', 'send', 'transfer']:
                return await self._send_transaction(fields)
            elif action in ['importera', 'import']:
                return await self._import_wallet(fields)
            else:
                return await self._show_help()
                
        except Exception as e:
            logger.error(f"Fel i WalletHandler: {e}")
            return {
                'message': f'Ett fel uppstod vid wallet-operationen: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _create_wallet(self) -> Dict[str, Any]:
        """
        Skapa ny wallet.
        
        Returns:
            Ny wallet-information
        """
        try:
            # Skapa ny account
            account = Account.create()
            
            message = "🎉 **Ny Wallet Skapad!**\n\n"
            message += f"📍 **Adress:** `{account.address}`\n"
            message += f"🔐 **Private Key:** `{account.key.hex()}`\n\n"
            message += "⚠️ **VIKTIGT:** Spara private key säkert!\n"
            message += "🔒 Lägg till i .env som CRYPTO_PRIVATE_KEY"
            
            return {
                'message': message,
                'data': {
                    'address': account.address,
                    'private_key': account.key.hex(),
                    'warning': 'Spara private key säkert!'
                },
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Wallet creation error: {e}")
            return {
                'message': f'Kunde inte skapa wallet: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _show_balance(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Visa wallet-saldo.
        
        Args:
            fields: Extraherade fält
            
        Returns:
            Wallet balance information
        """
        private_key = os.getenv('CRYPTO_PRIVATE_KEY')
        if not private_key:
            return {
                'message': 'CRYPTO_PRIVATE_KEY inte satt i environment',
                'data': {'error': 'Missing private key'},
                'status': 'error'
            }
        
        try:
            account = Account.from_key(private_key)
            w3 = Web3(Web3.HTTPProvider(BASE_TESTNET_CONFIG['rpc_url']))
            
            # Hämta ETH balance
            balance_wei = w3.eth.get_balance(account.address)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            
            message = f"💰 **Wallet Balance:**\n\n"
            message += f"📍 Adress: `{account.address}`\n"
            message += f"💎 ETH: {balance_eth:.6f}\n"
            message += f"🔗 Chain: {BASE_TESTNET_CONFIG['name']}\n"
            message += f"🔍 Explorer: {BASE_TESTNET_CONFIG['explorer']}/address/{account.address}"
            
            return {
                'message': message,
                'data': {
                    'address': account.address,
                    'balance_eth': float(balance_eth),
                    'balance_wei': balance_wei,
                    'chain': BASE_TESTNET_CONFIG['name']
                },
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return {
                'message': f'Kunde inte hämta saldo: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _send_transaction(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Skicka transaktion.
        
        Args:
            fields: Extraherade fält med to_address och amount
            
        Returns:
            Transaction result
        """
        private_key = os.getenv('CRYPTO_PRIVATE_KEY')
        if not private_key:
            return {
                'message': 'CRYPTO_PRIVATE_KEY inte satt i environment',
                'data': {'error': 'Missing private key'},
                'status': 'error'
            }
        
        to_address = fields.get('to_address')
        amount_eth = fields.get('amount', 0)
        
        if not to_address:
            return {
                'message': 'Mottagaradress saknas. Ange "skicka X ETH till 0x..."',
                'data': {'error': 'Missing to_address'},
                'status': 'error'
            }
        
        if amount_eth <= 0:
            return {
                'message': 'Ogiltigt belopp. Ange "skicka 0.01 ETH till adress"',
                'data': {'error': 'Invalid amount'},
                'status': 'error'
            }
        
        try:
            deployer = ContractDeployer(BASE_TESTNET_CONFIG['rpc_url'], private_key)
            amount_wei = Web3.to_wei(amount_eth, 'ether')
            
            result = await deployer.send_transaction(to_address, amount_wei)
            
            if result['success']:
                message = f"✅ **Transaktion Skickad!**\n\n"
                message += f"📤 Till: `{to_address}`\n"
                message += f"💰 Belopp: {amount_eth} ETH\n"
                message += f"🔗 TX: `{result['transaction_hash']}`\n"
                message += f"⛽ Gas: {result['gas_used']}\n"
                message += f"🔍 Explorer: {BASE_TESTNET_CONFIG['explorer']}/tx/{result['transaction_hash']}"
                
                return {
                    'message': message,
                    'data': result,
                    'status': 'success'
                }
            else:
                return {
                    'message': f'Transaktion misslyckades: {result["error"]}',
                    'data': result,
                    'status': 'error'
                }
                
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            return {
                'message': f'Transaktion misslyckades: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _import_wallet(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Importera wallet från private key.
        
        Args:
            fields: Extraherade fält med private_key
            
        Returns:
            Import result
        """
        private_key = fields.get('private_key')
        
        if not private_key:
            return {
                'message': 'Private key saknas för import',
                'data': {'error': 'Missing private key'},
                'status': 'error'
            }
        
        try:
            account = Account.from_key(private_key)
            
            message = f"✅ **Wallet Importerad!**\n\n"
            message += f"📍 Adress: `{account.address}`\n"
            message += f"🔒 Lägg till i .env som CRYPTO_PRIVATE_KEY"
            
            return {
                'message': message,
                'data': {
                    'address': account.address,
                    'imported': True
                },
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Import error: {e}")
            return {
                'message': f'Kunde inte importera wallet: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _show_help(self) -> Dict[str, Any]:
        """Visa hjälp för wallet-kommandon."""
        help_text = """
💰 **Wallet Kommandon:**

**Skapa wallet:**
- "Skapa ny wallet"
- "Generera wallet"

**Visa saldo:**
- "Visa wallet saldo"
- "Kolla balance"

**Skicka transaktion:**
- "Skicka 0.01 ETH till 0x123..."
- "Transfer 0.5 ETH till adress"

**Importera wallet:**
- "Importera wallet med private key"

**Säkerhet:**
- Spara alltid private key säkert
- Använd endast testnet för utveckling
- Lägg till CRYPTO_PRIVATE_KEY i .env
        """
        
        return {
            'message': help_text,
            'data': {
                'supported_chains': ['Base Testnet'],
                'examples': [
                    'Skapa ny wallet',
                    'Visa wallet saldo',
                    'Skicka 0.01 ETH till 0x123...'
                ]
            },
            'status': 'info'
        }

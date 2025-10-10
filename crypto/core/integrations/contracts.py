"""
Smart contract templates och deployment för HappyOS Crypto.
"""
import json
from web3 import Web3
from eth_account import Account
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ContractDeployer:
    """Hanterar deployment av smart contracts."""
    
    # ERC20 contract template
    ERC20_BYTECODE = "0x608060405234801561001057600080fd5b506040516109c43803806109c48339818101604052810190610032919061028d565b8181600390805190602001906100499291906100f1565b5080600490805190602001906100609291906100f1565b50505080600560006101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555080600081905550806000808373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020819055505050610380565b8280546100fd90610322565b90600052602060002090601f01602090048101928261011f5760008555610166565b82601f1061013857805160ff1916838001178555610166565b82800160010185558215610166579182015b8281111561016557825182559160200191906001019061014a565b5b5090506101739190610177565b5090565b5b80821115610190576000816000905550600101610178565b5090565b6000604051905090565b600080fd5b600080fd5b600080fd5b600080fd5b6000601f19601f8301169050919050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052604160045260246000fd5b6101fb826101b2565b810181811067ffffffffffffffff8211171561021a576102196101c3565b5b80604052505050565b600061022d610194565b905061023982826101f2565b919050565b600067ffffffffffffffff821115610259576102586101c3565b5b610262826101b2565b9050602081019050919050565b60005b8381101561028d578082015181840152602081019050610272565b8381111561029c576000848401525b50505050565b60006102b56102b08461023e565b610223565b9050828152602081018484840111156102d1576102d06101ad565b5b6102dc84828561026f565b509392505050565b600082601f8301126102f9576102f86101a8565b5b81516103098482602086016102a2565b91505092915050565b60008115159050919050565b61032781610312565b811461033257600080fd5b50565b6000815190506103448161031e565b92915050565b6000806040838503121561036157610360610194565b5b600083015167ffffffffffffffff81111561037f5761037e610199565b5b61038b858286016102e4565b925050602061039c85828601610335565b9150509250929050565b6106358061038f6000396000f3fe608060405234801561001057600080fd5b50600436106100885760003560e01c8063a9059cbb1161005b578063a9059cbb146101145780638da5cb5b14610144578063dd62ed3e14610162578063f2fde38b1461019257610088565b8063095ea7b31461008d57806318160ddd146100bd57806323b872dd146100db57806370a082311461010b57610088565b600080fd5b6100a760048036038101906100a29190610456565b6101ae565b6040516100b491906104b1565b60405180910390f35b6100c56102a0565b6040516100d291906104db565b60405180910390f35b6100f560048036038101906100f091906104f6565b6102a6565b60405161010291906104b1565b60405180910390f35b61011361010e366004610549565b610455565b005b61012e60048036038101906101299190610456565b61047b565b60405161013b91906104b1565b60405180910390f35b61014c610568565b6040516101599190610585565b60405180910390f35b61017c600480360381019061017791906105a0565b61058e565b60405161018991906104db565b60405180910390f35b6101ac60048036038101906101a79190610549565b610615565b005b60008160016000858152602001908152602001600020819055508273ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff167f8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b92584604051610225919061064f565b60405180910390a36001905092915050565b60005481565b600081600160008673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020541015610331576000905061044e565b81600160008673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060008282546103bd919061069f565b9250508190555081600080008673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000206000828254610413919061069f565b9250508190555081600080008573ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825461046991906106d3565b92505081905550600190505b9392505050565b600081600080003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205410156104cb576000905061055f565b81600080003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000206000828254610519919061069f565b9250508190555081600080008573ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825461056f91906106d3565b925050819055508273ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff167fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef846040516105d3919061064f565b60405180910390a3600190505b92915050565b600560009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b6001600080008473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060008373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020549050929150505056fea2646970667358221220c7b4d4b4d4b4d4b4d4b4d4b4d4b4d4b4d4b4d4b4d4b4d4b4d4b4d4b4d4b4d4b464736f6c63430008070033"
    
    ERC20_ABI = [
        {
            "inputs": [
                {"internalType": "string", "name": "_name", "type": "string"},
                {"internalType": "string", "name": "_symbol", "type": "string"},
                {"internalType": "uint256", "name": "_totalSupply", "type": "uint256"},
                {"internalType": "address", "name": "_owner", "type": "address"}
            ],
            "stateMutability": "nonpayable",
            "type": "constructor"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    def __init__(self, rpc_url: str, private_key: str):
        """
        Initialisera contract deployer.
        
        Args:
            rpc_url: RPC URL för blockchain (t.ex. Base testnet)
            private_key: Private key för deployment wallet
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.w3.eth.default_account = self.account.address
        
        logger.info(f"ContractDeployer initialiserad för {self.account.address}")
    
    async def deploy_erc20_token(
        self, 
        name: str, 
        symbol: str, 
        total_supply: int,
        gas_price_gwei: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Deploya ERC20 token på blockchain.
        
        Args:
            name: Token namn (t.ex. "HappyToken")
            symbol: Token symbol (t.ex. "HAPPY")
            total_supply: Total supply (t.ex. 1000000)
            gas_price_gwei: Gas price i Gwei (None = auto)
            
        Returns:
            Dict med contract address, transaction hash, etc.
        """
        try:
            # Förbered constructor arguments
            constructor_args = [name, symbol, total_supply, self.account.address]
            
            # Skapa contract instance
            contract = self.w3.eth.contract(
                abi=self.ERC20_ABI,
                bytecode=self.ERC20_BYTECODE
            )
            
            # Estimera gas
            gas_estimate = contract.constructor(*constructor_args).estimate_gas()
            
            # Sätt gas price
            if gas_price_gwei:
                gas_price = self.w3.to_wei(gas_price_gwei, 'gwei')
            else:
                gas_price = self.w3.eth.gas_price
            
            # Bygg transaction
            transaction = contract.constructor(*constructor_args).build_transaction({
                'from': self.account.address,
                'gas': gas_estimate + 50000,  # Buffer
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Signera transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            
            # Skicka transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Vänta på receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            contract_address = tx_receipt.contractAddress
            
            logger.info(f"ERC20 token {name} ({symbol}) deployad på {contract_address}")
            
            return {
                'success': True,
                'contract_address': contract_address,
                'transaction_hash': tx_hash.hex(),
                'gas_used': tx_receipt.gasUsed,
                'token_name': name,
                'token_symbol': symbol,
                'total_supply': total_supply,
                'deployer': self.account.address
            }
            
        except Exception as e:
            logger.error(f"Fel vid deployment av ERC20 token: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_transaction(
        self, 
        to_address: str, 
        amount_wei: int,
        gas_price_gwei: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Skicka ETH-transaktion.
        
        Args:
            to_address: Mottagaradress
            amount_wei: Belopp i wei
            gas_price_gwei: Gas price i Gwei
            
        Returns:
            Transaction result
        """
        try:
            # Sätt gas price
            if gas_price_gwei:
                gas_price = self.w3.to_wei(gas_price_gwei, 'gwei')
            else:
                gas_price = self.w3.eth.gas_price
            
            # Bygg transaction
            transaction = {
                'to': to_address,
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            }
            
            # Signera och skicka
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Vänta på receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Transaktion skickad: {tx_hash.hex()}")
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'gas_used': tx_receipt.gasUsed,
                'from_address': self.account.address,
                'to_address': to_address,
                'amount_wei': amount_wei
            }
            
        except Exception as e:
            logger.error(f"Fel vid transaktion: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Base Testnet konfiguration
BASE_TESTNET_CONFIG = {
    'rpc_url': 'https://goerli.base.org',
    'chain_id': 84531,
    'explorer': 'https://goerli.basescan.org',
    'name': 'Base Goerli Testnet'
}

# Polygon Mumbai konfiguration  
POLYGON_TESTNET_CONFIG = {
    'rpc_url': 'https://rpc-mumbai.maticvigil.com',
    'chain_id': 80001,
    'explorer': 'https://mumbai.polygonscan.com',
    'name': 'Polygon Mumbai Testnet'
}

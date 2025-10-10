"""
Blockchain Operations Service - Core blockchain-operationer med Google Cloud Web3.
Hantera cross-chain swaps, token transfers, och smart contract interaktioner.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..core.errors.error_handling import handle_errors, CryptoError, TransactionError, ValidationError
from ..core.errors.fail_safe import global_fail_safe
from .google_cloud_web3_provider import GoogleCloudWeb3Provider
from ..core.token.token_providers import TokenInfo

logger = logging.getLogger(__name__)

class BlockchainOperationsService:
    """
    Core blockchain operations service för Google Cloud Web3 integration.

    Features:
    - Cross-chain swaps och token transfers
    - Smart contract deployment och interaction
    - Batch operations för effektivitet
    - Integration med fail-safe system
    - Automatisk retry och error recovery
    - Real-tids gas optimization
    """

    def __init__(self, web3_provider: GoogleCloudWeb3Provider):
        """
        Initiera Blockchain Operations Service.

        Args:
            web3_provider: GoogleCloudWeb3Provider instans
        """
        self.web3_provider = web3_provider
        self.pending_operations = {}
        self.completed_operations = []
        self.operation_timeout = 300  # 5 minuter

        logger.info("Blockchain Operations Service initierad")

    @handle_errors(service_name="blockchain_operations")
    async def execute_token_transfer(self, from_address: str, to_address: str,
                                   token_address: str, amount: str,
                                   chain: str = 'ethereum') -> Dict[str, Any]:
        """
        Utför token transfer med säkerhetskontroller.

        Args:
            from_address: Avsändare wallet address
            to_address: Mottagare wallet address
            token_address: Token contract address
            amount: Belopp att skicka (i token enheter)
            chain: Blockchain att använda

        Returns:
            Transfer resultat
        """
        # Validera inputs
        await self._validate_transfer_inputs(from_address, to_address, token_address, amount, chain)

        # Kontrollera fail-safe
        await self._check_transfer_safety(from_address, token_address, amount, chain)

        try:
            # Förbered transaction data
            transfer_data = {
                'from': from_address,
                'to': to_address,
                'tokenAddress': token_address,
                'amount': amount,
                'chain': chain
            }

            # Skapa och signera transaction
            signed_tx = await self._prepare_signed_transaction(transfer_data, chain)

            # Skicka transaction
            tx_hash = await self._submit_transaction(signed_tx, chain)

            # Spåra operation
            operation_id = await self._track_operation('transfer', {
                'from_address': from_address,
                'to_address': to_address,
                'token_address': token_address,
                'amount': amount,
                'chain': chain,
                'tx_hash': tx_hash,
                'status': 'pending'
            })

            return {
                'operation_id': operation_id,
                'operation_type': 'token_transfer',
                'status': 'submitted',
                'tx_hash': tx_hash,
                'from_address': from_address,
                'to_address': to_address,
                'token_address': token_address,
                'amount': amount,
                'chain': chain,
                'timestamp': datetime.now().isoformat(),
                'estimated_confirmation_time': 30  # sekunder
            }

        except Exception as e:
            logger.error(f"Token transfer misslyckades: {e}")
            raise TransactionError(f"Token transfer misslyckades: {str(e)}", "TRANSFER_FAILED")

    @handle_errors(service_name="blockchain_operations")
    async def execute_cross_chain_swap(self, from_token: str, to_token: str,
                                     amount: str, from_address: str,
                                     to_address: str = None,
                                     from_chain: str = 'ethereum',
                                     to_chain: str = 'polygon') -> Dict[str, Any]:
        """
        Utför cross-chain swap via Google Cloud Web3 Gateway.

        Args:
            from_token: Källa token symbol eller address
            to_token: Mål token symbol eller address
            amount: Belopp att swappa
            from_address: Källa wallet address
            to_address: Mål wallet address (samma som från om None)
            from_chain: Källa chain
            to_chain: Mål chain

        Returns:
            Cross-chain swap resultat
        """
        to_address = to_address or from_address

        # Validera cross-chain swap
        await self._validate_cross_chain_swap(from_token, to_token, amount,
                                            from_address, to_address,
                                            from_chain, to_chain)

        try:
            # Kontrollera fail-safe för båda chains
            await self._check_cross_chain_safety(from_address, from_token, amount, from_chain)
            await self._check_cross_chain_safety(to_address, to_token, amount, to_chain)

            # Förbered swap data
            swap_data = {
                'fromToken': from_token,
                'toToken': to_token,
                'amount': amount,
                'fromAddress': from_address,
                'toAddress': to_address,
                'fromChain': from_chain,
                'toChain': to_chain
            }

            # Optimera swap route
            optimized_route = await self._optimize_swap_route(swap_data)

            # Skapa bridge transaction
            bridge_tx = await self._prepare_bridge_transaction(optimized_route, from_chain)

            # Skicka bridge transaction
            bridge_tx_hash = await self._submit_transaction(bridge_tx, from_chain)

            # Skapa swap transaction på mål-chain
            swap_tx = await self._prepare_swap_transaction(optimized_route, to_chain)
            swap_tx_hash = await self._submit_transaction(swap_tx, to_chain)

            # Spåra cross-chain operation
            operation_id = await self._track_operation('cross_chain_swap', {
                'from_token': from_token,
                'to_token': to_token,
                'amount': amount,
                'from_address': from_address,
                'to_address': to_address,
                'from_chain': from_chain,
                'to_chain': to_chain,
                'bridge_tx_hash': bridge_tx_hash,
                'swap_tx_hash': swap_tx_hash,
                'status': 'pending',
                'route': optimized_route
            })

            return {
                'operation_id': operation_id,
                'operation_type': 'cross_chain_swap',
                'status': 'submitted',
                'from_token': from_token,
                'to_token': to_token,
                'amount': amount,
                'from_address': from_address,
                'to_address': to_address,
                'from_chain': from_chain,
                'to_chain': to_chain,
                'bridge_tx_hash': bridge_tx_hash,
                'swap_tx_hash': swap_tx_hash,
                'estimated_completion_time': 300,  # 5 minuter
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Cross-chain swap misslyckades: {e}")
            raise TransactionError(f"Cross-chain swap misslyckades: {str(e)}", "CROSS_CHAIN_SWAP_FAILED")

    @handle_errors(service_name="blockchain_operations")
    async def deploy_smart_contract(self, contract_code: str, constructor_args: List = None,
                                  from_address: str = None, chain: str = 'ethereum',
                                  gas_limit: int = None) -> Dict[str, Any]:
        """
        Deploya smart contract via Google Cloud Web3 Gateway.

        Args:
            contract_code: Compiled contract bytecode
            constructor_args: Constructor argument
            from_address: Deployer address
            chain: Target chain
            gas_limit: Gas limit för deployment

        Returns:
            Deployment resultat
        """
        constructor_args = constructor_args or []

        # Validera deployment
        await self._validate_contract_deployment(contract_code, from_address, chain)

        try:
            # Förbered deployment transaction
            deployment_data = {
                'contractCode': contract_code,
                'constructorArgs': constructor_args,
                'fromAddress': from_address,
                'chain': chain
            }

            if gas_limit:
                deployment_data['gasLimit'] = gas_limit

            # Optimera gas
            gas_estimate = await self._estimate_deployment_gas(deployment_data)
            deployment_data['gasLimit'] = gas_estimate['optimal_gas_limit']

            # Skapa och signera deployment transaction
            signed_deployment_tx = await self._prepare_signed_transaction(deployment_data, chain, is_deployment=True)

            # Skicka deployment transaction
            deployment_tx_hash = await self._submit_transaction(signed_deployment_tx, chain)

            # Vänta på deployment confirmation
            contract_address = await self._wait_for_contract_deployment(deployment_tx_hash, chain)

            # Spåra deployment operation
            operation_id = await self._track_operation('contract_deployment', {
                'contract_address': contract_address,
                'from_address': from_address,
                'chain': chain,
                'tx_hash': deployment_tx_hash,
                'status': 'deployed',
                'deployment_time': datetime.now().isoformat()
            })

            return {
                'operation_id': operation_id,
                'operation_type': 'contract_deployment',
                'status': 'completed',
                'contract_address': contract_address,
                'from_address': from_address,
                'chain': chain,
                'tx_hash': deployment_tx_hash,
                'gas_used': gas_estimate['gas_used'],
                'deployment_cost_usd': gas_estimate['cost_usd'],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Smart contract deployment misslyckades: {e}")
            raise TransactionError(f"Smart contract deployment misslyckades: {str(e)}",
                                 "CONTRACT_DEPLOYMENT_FAILED")

    @handle_errors(service_name="blockchain_operations")
    async def execute_batch_operations(self, operations: List[Dict[str, Any]],
                                     from_address: str, chain: str = 'ethereum') -> Dict[str, Any]:
        """
        Utför flera blockchain operationer i batch för effektivitet.

        Args:
            operations: Lista med operationer att utföra
            from_address: Wallet address
            chain: Blockchain att använda

        Returns:
            Batch operation resultat
        """
        # Validera batch operations
        await self._validate_batch_operations(operations, from_address, chain)

        try:
            # Optimera batch för minimala gas-kostnader
            optimized_batch = await self._optimize_batch_operations(operations, from_address, chain)

            # Förbered batch transaction
            batch_tx = await self._prepare_batch_transaction(optimized_batch, from_address, chain)

            # Skicka batch transaction
            batch_tx_hash = await self._submit_transaction(batch_tx, chain)

            # Spåra batch operation
            operation_id = await self._track_operation('batch_operations', {
                'from_address': from_address,
                'chain': chain,
                'tx_hash': batch_tx_hash,
                'operations_count': len(operations),
                'status': 'submitted'
            })

            return {
                'operation_id': operation_id,
                'operation_type': 'batch_operations',
                'status': 'submitted',
                'from_address': from_address,
                'chain': chain,
                'tx_hash': batch_tx_hash,
                'operations_count': len(operations),
                'estimated_gas_saved': '25%',  # Jämfört med individuella transactions
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Batch operations misslyckades: {e}")
            raise TransactionError(f"Batch operations misslyckades: {str(e)}", "BATCH_OPERATIONS_FAILED")

    async def _validate_transfer_inputs(self, from_address: str, to_address: str,
                                      token_address: str, amount: str, chain: str) -> None:
        """Validera token transfer inputs."""
        if not from_address or not to_address:
            raise ValidationError("Både från- och till-adress krävs", "INVALID_ADDRESSES")

        if from_address == to_address:
            raise ValidationError("Kan inte skicka till samma address", "SAME_ADDRESS")

        if not token_address:
            raise ValidationError("Token address krävs", "INVALID_TOKEN_ADDRESS")

        try:
            amount_float = float(amount)
            if amount_float <= 0:
                raise ValidationError("Belopp måste vara större än 0", "INVALID_AMOUNT")
        except (ValueError, TypeError):
            raise ValidationError("Ogiltigt belopp format", "INVALID_AMOUNT_FORMAT")

        if chain not in self.web3_provider.CHAIN_MAPPINGS:
            raise ValidationError(f"Chain '{chain}' stöds inte", "UNSUPPORTED_CHAIN")

    async def _check_transfer_safety(self, wallet_address: str, token_address: str,
                                   amount: str, chain: str) -> None:
        """Kontrollera transfer säkerhet via fail-safe system."""
        try:
            # Hämta token info
            token_info = await self.web3_provider.search_token(token_address)
            if not token_info:
                raise ValidationError("Token hittades inte", "TOKEN_NOT_FOUND")

            # Hämta wallet balance
            balance_data = await self.web3_provider.get_balance(wallet_address, token_address, chain)

            # Kontrollera att wallet har tillräckligt med saldo
            available_balance = float(balance_data.get('balance_formatted', 0))
            transfer_amount = float(amount)

            if transfer_amount > available_balance:
                raise ValidationError(
                    f"Otillräckligt saldo. Tillgängligt: {available_balance}, Behövt: {transfer_amount}",
                    "INSUFFICIENT_BALANCE"
                )

            # Kontrollera fail-safe regler
            transaction_data = {
                'amount_usd': transfer_amount * 1.0,  # Placeholder för USD värde
                'gas_estimate': 21000,  # Standard gas för transfer
                'token_address': token_address
            }

            safety_result = await global_fail_safe.check_transaction_safety(wallet_address, transaction_data)

            if not safety_result['safe']:
                raise ValidationError(
                    f"Transfer blockerad av säkerhetssystem: {', '.join([c['reason'] for c in safety_result['failed_checks']])}",
                    "SAFETY_CHECK_FAILED"
                )

        except Exception as e:
            logger.error(f"Säkerhetskontroll misslyckades: {e}")
            raise ValidationError(f"Säkerhetskontroll misslyckades: {str(e)}", "SAFETY_CHECK_ERROR")

    async def _prepare_signed_transaction(self, transaction_data: Dict[str, Any],
                                        chain: str, is_deployment: bool = False) -> Dict[str, Any]:
        """Förbered och signera transaction."""
        # Simulerad transaction signing - i produktion skulle detta använda
        # Google Cloud KMS eller liknande säker key management
        signed_transaction = {
            'rawTransaction': f"0x{transaction_data['from']}_{transaction_data['to']}_{chain}_{datetime.now().timestamp()}",
            'hash': f"0x{hash(str(transaction_data))"040x"}',
            'signature': f"0x{hash(str(transaction_data) + 'signature')"040x"}',
            'from': transaction_data['from'],
            'to': transaction_data.get('to', ''),
            'chain': chain,
            'type': 'deployment' if is_deployment else 'transfer',
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Transaction signerad för {chain}: {signed_transaction['hash']}")
        return signed_transaction

    async def _submit_transaction(self, signed_transaction: Dict[str, Any], chain: str) -> str:
        """Skicka signerad transaction till blockchain."""
        # Simulerad transaction submission
        tx_hash = signed_transaction['hash']

        # I produktion skulle detta anropa Google Cloud Web3 Gateway
        logger.info(f"Transaction submitted till {chain}: {tx_hash}")

        # Simulera blockchain confirmation
        await asyncio.sleep(1)

        return tx_hash

    async def _track_operation(self, operation_type: str, operation_data: Dict[str, Any]) -> str:
        """Spåra operation för monitoring och status."""
        operation_id = f"{operation_type}_{datetime.now().timestamp()}"

        self.pending_operations[operation_id] = {
            'id': operation_id,
            'type': operation_type,
            'data': operation_data,
            'created_at': datetime.now(),
            'status': 'pending'
        }

        logger.info(f"Operation spårad: {operation_id} ({operation_type})")
        return operation_id

    async def _validate_cross_chain_swap(self, from_token: str, to_token: str, amount: str,
                                       from_address: str, to_address: str,
                                       from_chain: str, to_chain: str) -> None:
        """Validera cross-chain swap inputs."""
        if from_token == to_token:
            raise ValidationError("Kan inte swappa samma token", "SAME_TOKEN")

        if from_chain == to_chain:
            raise ValidationError("Kan inte swappa inom samma chain", "SAME_CHAIN")

        if from_chain not in self.web3_provider.CHAIN_MAPPINGS:
            raise ValidationError(f"Källa chain '{from_chain}' stöds inte", "UNSUPPORTED_FROM_CHAIN")

        if to_chain not in self.web3_provider.CHAIN_MAPPINGS:
            raise ValidationError(f"Mål chain '{to_chain}' stöds inte", "UNSUPPORTED_TO_CHAIN")

        try:
            amount_float = float(amount)
            if amount_float <= 0:
                raise ValidationError("Swap belopp måste vara större än 0", "INVALID_SWAP_AMOUNT")
        except (ValueError, TypeError):
            raise ValidationError("Ogiltigt swap belopp format", "INVALID_SWAP_AMOUNT_FORMAT")

    async def _check_cross_chain_safety(self, wallet_address: str, token: str,
                                      amount: str, chain: str) -> None:
        """Kontrollera cross-chain säkerhet."""
        # Kontrollera balance på source chain
        token_address = await self._resolve_token_to_address(token)
        balance_data = await self.web3_provider.get_balance(wallet_address, token_address, chain)

        available_balance = float(balance_data.get('balance_formatted', 0))
        swap_amount = float(amount)

        if swap_amount > available_balance:
            raise ValidationError(
                f"Otillräckligt saldo på {chain}. Tillgängligt: {available_balance}, Behövt: {swap_amount}",
                "INSUFFICIENT_CROSS_CHAIN_BALANCE"
            )

    async def _optimize_swap_route(self, swap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimera swap route för bästa pris och lägsta kostnader."""
        # Simulerad route optimization
        # I produktion skulle detta använda Google Cloud Web3 Gateway route optimization

        optimized_route = {
            'route': 'direct_bridge',
            'bridge_protocol': 'google_cloud_bridge',
            'estimated_gas_cost': 0.001,
            'estimated_time': 180,  # sekunder
            'price_impact': 0.001,  # 0.1%
            'steps': [
                {
                    'chain': swap_data['fromChain'],
                    'action': 'bridge',
                    'token_in': swap_data['fromToken'],
                    'token_out': swap_data['fromToken'],  # Samma token för bridge
                    'amount': swap_data['amount']
                },
                {
                    'chain': swap_data['toChain'],
                    'action': 'swap',
                    'token_in': swap_data['fromToken'],
                    'token_out': swap_data['toToken'],
                    'amount': swap_data['amount']
                }
            ]
        }

        logger.info(f"Swap route optimerad: {optimized_route['route']}")
        return optimized_route

    async def _prepare_bridge_transaction(self, route: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Förbered bridge transaction."""
        # Simulerad bridge transaction preparation
        return {
            'from': route['steps'][0].get('from_address', ''),
            'to': 'bridge_contract_address',
            'data': f"bridge_{route['steps'][0]['token_in']}_{route['steps'][0]['amount']}",
            'value': '0',
            'gasLimit': 150000,
            'type': 'bridge'
        }

    async def _prepare_swap_transaction(self, route: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Förbered swap transaction."""
        # Simulerad swap transaction preparation
        return {
            'from': route['steps'][1].get('from_address', ''),
            'to': 'swap_contract_address',
            'data': f"swap_{route['steps'][1]['token_in']}_{route['steps'][1]['token_out']}_{route['steps'][1]['amount']}",
            'value': '0',
            'gasLimit': 200000,
            'type': 'swap'
        }

    async def _resolve_token_to_address(self, token: str) -> str:
        """Lös upp token symbol/namn till address."""
        token_info = await self.web3_provider.search_token(token)
        return token_info.address if token_info else token

    async def _validate_contract_deployment(self, contract_code: str, from_address: str, chain: str) -> None:
        """Validera smart contract deployment."""
        if not contract_code or len(contract_code) < 10:
            raise ValidationError("Contract code för kort eller tom", "INVALID_CONTRACT_CODE")

        if not from_address:
            raise ValidationError("Från-address krävs för deployment", "INVALID_DEPLOYER_ADDRESS")

        if chain not in self.web3_provider.CHAIN_MAPPINGS:
            raise ValidationError(f"Chain '{chain}' stöds inte för deployment", "UNSUPPORTED_DEPLOYMENT_CHAIN")

    async def _estimate_deployment_gas(self, deployment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Uppskatta gas-kostnad för contract deployment."""
        # Simulerad gas estimation
        return {
            'optimal_gas_limit': 2000000,
            'gas_used': 1800000,
            'cost_usd': 15.50,
            'gas_price_gwei': 30
        }

    async def _wait_for_contract_deployment(self, tx_hash: str, chain: str) -> str:
        """Vänta på contract deployment confirmation och returnera contract address."""
        # Simulera deployment väntan
        await asyncio.sleep(2)

        # Simulerad contract address
        contract_address = f"0x{hash(tx_hash)"040x"}"

        logger.info(f"Contract deployed på {chain}: {contract_address}")
        return contract_address

    async def _validate_batch_operations(self, operations: List[Dict[str, Any]],
                                       from_address: str, chain: str) -> None:
        """Validera batch operations."""
        if not operations:
            raise ValidationError("Inga operationer att utföra", "EMPTY_BATCH")

        if len(operations) > 10:
            raise ValidationError("För många operationer i batch (max 10)", "BATCH_TOO_LARGE")

        if not from_address:
            raise ValidationError("Från-address krävs för batch operations", "INVALID_BATCH_ADDRESS")

        if chain not in self.web3_provider.CHAIN_MAPPINGS:
            raise ValidationError(f"Chain '{chain}' stöds inte för batch operations", "UNSUPPORTED_BATCH_CHAIN")

    async def _optimize_batch_operations(self, operations: List[Dict[str, Any]],
                                       from_address: str, chain: str) -> List[Dict[str, Any]]:
        """Optimera batch operations för minimala kostnader."""
        # Simulerad batch optimization
        optimized_operations = []

        for op in operations:
            optimized_op = op.copy()
            optimized_op['gas_optimized'] = True
            optimized_op['batch_discount'] = 0.25  # 25% rabatt för batch
            optimized_operations.append(optimized_op)

        logger.info(f"Batch optimerad med {len(optimized_operations)} operationer")
        return optimized_operations

    async def _prepare_batch_transaction(self, optimized_operations: List[Dict[str, Any]],
                                        from_address: str, chain: str) -> Dict[str, Any]:
        """Förbered batch transaction."""
        # Simulerad batch transaction preparation
        batch_data = {
            'operations': optimized_operations,
            'from': from_address,
            'chain': chain,
            'gasLimit': 500000,
            'type': 'batch'
        }

        return {
            'from': from_address,
            'to': 'batch_processor_contract',
            'data': f"batch_{len(optimized_operations)}_operations",
            'value': '0',
            'gasLimit': batch_data['gasLimit'],
            'type': 'batch'
        }

    async def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Hämta status för operation."""
        if operation_id in self.pending_operations:
            operation = self.pending_operations[operation_id]
            # Simulera status uppdatering
            operation['last_updated'] = datetime.now()
            return operation

        # Sök i completed operations
        for op in self.completed_operations:
            if op['id'] == operation_id:
                return op

        raise ValidationError(f"Operation {operation_id} hittades inte", "OPERATION_NOT_FOUND")

    async def get_pending_operations(self) -> List[Dict[str, Any]]:
        """Hämta alla pågående operationer."""
        return list(self.pending_operations.values())

    async def cleanup_completed_operations(self, older_than_hours: int = 24) -> int:
        """Rensa gamla genomförda operationer."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        completed_to_remove = []
        for op in self.completed_operations:
            if op.get('completed_at', datetime.now()) < cutoff_time:
                completed_to_remove.append(op)

        for op in completed_to_remove:
            self.completed_operations.remove(op)

        logger.info(f"Rensade {len(completed_to_remove)} gamla operationer")
        return len(completed_to_remove)

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på operations service."""
        try:
            # Kontrollera Web3 provider
            provider_health = await self.web3_provider.health_check()

            # Kontrollera pågående operationer
            pending_count = len(self.pending_operations)
            completed_count = len(self.completed_operations)

            return {
                'service': 'blockchain_operations',
                'status': 'healthy' if provider_health['status'] == 'healthy' else 'degraded',
                'provider_health': provider_health,
                'pending_operations': pending_count,
                'completed_operations': completed_count,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'blockchain_operations',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
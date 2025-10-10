"""
Automatisk Trading Bot för trend-following strategi.
Övervakar marknaden, genererar signaler och utför trades automatiskt via DEX.
"""
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal
import json
import aiofiles
import time

from .trend_signal_generator import TrendSignalGenerator
from .dex_integration import RealDexIntegration
from .analytics import MarketAnalyzer
from .error_handling import ErrorHandler

logger = logging.getLogger(__name__)

class Position:
    """Representerar en öppen trading position."""

    def __init__(self, token_id: str, side: str, entry_price: float, quantity: float, timestamp: datetime):
        self.token_id = token_id
        self.side = side  # 'BUY' eller 'SELL'
        self.entry_price = entry_price
        self.quantity = quantity
        self.timestamp = timestamp
        self.stop_loss = None
        self.take_profit = None
        self.current_price = entry_price
        self.unrealized_pnl = 0.0
        self.status = 'open'

    def update_price(self, current_price: float):
        """Uppdatera position med aktuellt pris och beräkna P&L."""
        self.current_price = current_price

        if self.side == 'BUY':
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:  # SELL
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity

    def check_stop_conditions(self) -> Optional[str]:
        """Kontrollera om stop loss eller take profit ska aktiveras."""
        if self.stop_loss and self.side == 'BUY' and self.current_price <= self.stop_loss:
            return 'stop_loss'
        elif self.stop_loss and self.side == 'SELL' and self.current_price >= self.stop_loss:
            return 'stop_loss'
        elif self.take_profit and self.side == 'BUY' and self.current_price >= self.take_profit:
            return 'take_profit'
        elif self.take_profit and self.side == 'SELL' and self.current_price <= self.take_profit:
            return 'take_profit'

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertera position till dict för serialisering."""
        return {
            'token_id': self.token_id,
            'side': self.side,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'timestamp': self.timestamp.isoformat(),
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'status': self.status
        }

class AutomaticTrader:
    """Automatisk trading bot som följer trend-following strategi."""

    def __init__(self):
        self.signal_generator = TrendSignalGenerator()
        self.dex_integration = RealDexIntegration()
        self.market_analyzer = MarketAnalyzer()
        self.error_handler = ErrorHandler()

        # Bot konfiguration
        self.config = {
            'check_interval': 300,      # 5 minuter mellan kontroller
            'max_positions': 5,         # Max 5 öppna positioner
            'min_confidence': 0.7,      # Minsta confidence för trade
            'max_risk_per_trade': 0.02, # 2% risk per trade
            'max_total_risk': 0.1,      # 10% total risk
            'take_profit_multiplier': 2.0,  # 2:1 risk-reward ratio
            'stop_loss_percentage': 0.05,   # 5% stop loss
            'trading_enabled': False,   # Säkerhetsflagga
            'allowed_tokens': ['ethereum', 'bitcoin', 'solana', 'avalanche-2', 'polygon-pos'],
            'min_liquidity_usd': 5000000,  # Min $5M likviditet
            'max_slippage': 0.005      # 0.5% max slippage
        }

        # Bot state
        self.positions: Dict[str, Position] = {}
        self.portfolio_balance = 0.0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.is_running = False
        self.last_check = None

        # Trading history
        self.trade_history: List[Dict[str, Any]] = []

        # Säkerhetsflaggor
        self.emergency_stop = False
        self.max_daily_loss = 0.05  # 5% max daily loss

        logger.info("Automatic Trader initialized")

    async def initialize(self, private_key: Optional[str] = None, rpc_url: Optional[str] = None):
        """Initiera bot med nödvändiga credentials."""
        try:
            # Initiera DEX trader med verkliga credentials
            if private_key and rpc_url:
                from web3 import Web3
                web3_provider = Web3(Web3.HTTPProvider(rpc_url))
                self.dex_integration = RealDexIntegration(web3_provider, private_key)
                self.config['trading_enabled'] = True
                logger.info("Live trading enabled with DEX integration")
            else:
                logger.warning("No trading credentials provided - running in simulation mode")

            # Ladda tidigare state om tillgängligt
            await self.load_state()

            logger.info("Automatic Trader initialization complete")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize trader: {e}")
            return False

    async def start_trading(self):
        """Starta automatisk trading loop."""
        if self.is_running:
            logger.warning("Trading bot is already running")
            return

        self.is_running = True
        logger.info("Starting automatic trading bot...")

        try:
            while self.is_running and not self.emergency_stop:
                try:
                    await self.trading_cycle()
                    await asyncio.sleep(self.config['check_interval'])

                except Exception as e:
                    logger.error(f"Error in trading cycle: {e}")
                    await self.error_handler.handle_error(e, "trading_cycle")
                    await asyncio.sleep(60)  # Vila efter fel

        except KeyboardInterrupt:
            logger.info("Trading bot stopped by user")
        finally:
            self.is_running = False
            await self.save_state()
            logger.info("Trading bot stopped")

    async def stop_trading(self):
        """Stoppa trading bot."""
        logger.info("Stopping trading bot...")
        self.is_running = False

    async def trading_cycle(self):
        """En komplett trading cykel."""
        try:
            self.last_check = datetime.now()
            logger.info(f"Starting trading cycle at {self.last_check}")

            # 1. Uppdatera alla öppna positioner
            await self.update_positions()

            # 2. Kontrollera risk limits
            if not await self.check_risk_limits():
                logger.warning("Risk limits exceeded - skipping new trades")
                return

            # 3. Generera signaler för alla tillåtna tokens
            signals = await self.generate_signals()

            # 4. Filtrera och ranka signaler
            valid_signals = await self.filter_signals(signals)

            # 5. Utför trades baserat på signaler
            await self.execute_trades(valid_signals)

            # 6. Hantera position exits
            await self.handle_exits()

            # 7. Uppdatera portfolio status
            await self.update_portfolio_status()

            # 8. Spara state
            await self.save_state()

            logger.info(f"Trading cycle completed - {len(valid_signals)} valid signals found")

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            await self.error_handler.handle_error(e, "trading_cycle")

    async def generate_signals(self) -> List[Dict[str, Any]]:
        """Generera trading signaler för alla tillåtna tokens."""
        signals = []

        for token_id in self.config['allowed_tokens']:
            try:
                # Kontrollera om vi redan har en position i denna token
                if token_id in self.positions:
                    continue

                signal = await self.signal_generator.generate_trend_signal(token_id, use_llm=False)

                if signal['success']:
                    signals.append(signal)

                # Undvik att överbelasta API:et
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error generating signal for {token_id}: {e}")
                continue

        logger.info(f"Generated {len(signals)} signals")
        return signals

    async def filter_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtrera och ranka signaler baserat på kriterier."""
        valid_signals = []

        for signal in signals:
            try:
                token_id = signal['token_id']
                recommendation = signal['trading_recommendation']
                dex_data = signal['dex_data']

                # Grundläggande filtrering
                if recommendation['action'] == 'HOLD':
                    continue

                if recommendation['confidence'] < self.config['min_confidence']:
                    continue

                # Kontrollera DEX likviditet
                if not dex_data.get('success', False):
                    continue

                total_liquidity = dex_data.get('total_liquidity', 0)
                if total_liquidity < self.config['min_liquidity_usd']:
                    continue

                # Kontrollera att vi inte överskrider max positioner
                if len(self.positions) >= self.config['max_positions']:
                    break

                valid_signals.append(signal)

            except Exception as e:
                logger.error(f"Error filtering signal for {signal.get('token_id', 'unknown')}: {e}")
                continue

        # Ranka signaler efter confidence
        valid_signals.sort(key=lambda x: x['trading_recommendation']['confidence'], reverse=True)

        logger.info(f"Filtered to {len(valid_signals)} valid signals")
        return valid_signals

    async def execute_trades(self, signals: List[Dict[str, Any]]):
        """Utför trades baserat på giltiga signaler."""
        for signal in signals:
            try:
                token_id = signal['token_id']
                recommendation = signal['trading_recommendation']

                # Beräkna position size
                position_size = self.calculate_position_size(
                    recommendation['confidence'],
                    signal['market_data']['current_price']
                )

                if position_size <= 0:
                    continue

                # Utför trade
                success = await self.execute_single_trade(signal, position_size)

                if success:
                    logger.info(f"Successfully executed {recommendation['action']} trade for {token_id}")
                else:
                    logger.warning(f"Failed to execute trade for {token_id}")

                # Pausa mellan trades för att undvika rate limits
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error executing trade for {signal.get('token_id', 'unknown')}: {e}")
                continue

    async def execute_single_trade(self, signal: Dict[str, Any], position_size: float) -> bool:
        """Utför en enskild trade."""
        try:
            token_id = signal['token_id']
            recommendation = signal['trading_recommendation']
            current_price = signal['market_data']['current_price']

            if not self.config['trading_enabled']:
                # Simulera trade
                logger.info(f"SIMULATION: Would execute {recommendation['action']} {position_size} of {token_id} at ${current_price}")
                await self.create_simulated_position(signal, position_size)
                return True

            # Verklig trade execution
            if recommendation['action'] == 'BUY':
                # Köp token mot USDC/ETH/WETH
                success = await self.dex_integration.execute_swap(
                    token_in='usdc',
                    token_out=token_id,
                    amount_in=position_size,
                    dex_preference='uniswap_v3'
                )
            else:  # SELL
                # Sälj token mot USDC
                success = await self.dex_integration.execute_swap(
                    token_in=token_id,
                    token_out='usdc',
                    amount_in=position_size,
                    dex_preference='uniswap_v3'
                )

            if success and success.get('success', False):
                # Skapa position tracking
                await self.create_position(signal, position_size, success)
                return True
            else:
                logger.error(f"Trade execution failed: {success.get('error', 'Unknown error') if success else 'No response'}")
                return False

        except Exception as e:
            logger.error(f"Error in single trade execution: {e}")
            return False

    async def create_simulated_position(self, signal: Dict[str, Any], position_size: float):
        """Skapa simulerad position för testning."""
        token_id = signal['token_id']
        current_price = signal['market_data']['current_price']
        recommendation = signal['trading_recommendation']

        # Beräkna stop loss och take profit
        if recommendation['action'] == 'BUY':
            stop_loss = current_price * (1 - self.config['stop_loss_percentage'])
            take_profit = current_price * (1 + self.config['take_profit_multiplier'] * self.config['stop_loss_percentage'])
        else:
            stop_loss = current_price * (1 + self.config['stop_loss_percentage'])
            take_profit = current_price * (1 - self.config['take_profit_multiplier'] * self.config['stop_loss_percentage'])

        position = Position(
            token_id=token_id,
            side=recommendation['action'],
            entry_price=current_price,
            quantity=position_size,
            timestamp=datetime.now()
        )

        position.stop_loss = stop_loss
        position.take_profit = take_profit

        self.positions[token_id] = position
        logger.info(f"Created simulated position: {position.side} {position.quantity} {token_id} at ${position.entry_price}")

    async def create_position(self, signal: Dict[str, Any], position_size: float, trade_result: Dict[str, Any]):
        """Skapa verklig position baserat på trade result."""
        token_id = signal['token_id']
        current_price = signal['market_data']['current_price']

        position = Position(
            token_id=token_id,
            side=signal['trading_recommendation']['action'],
            entry_price=current_price,
            quantity=position_size,
            timestamp=datetime.now()
        )

        # Sätt stop loss och take profit
        if position.side == 'BUY':
            position.stop_loss = current_price * (1 - self.config['stop_loss_percentage'])
            position.take_profit = current_price * (1 + self.config['take_profit_multiplier'] * self.config['stop_loss_percentage'])
        else:
            position.stop_loss = current_price * (1 + self.config['stop_loss_percentage'])
            position.take_profit = current_price * (1 - self.config['take_profit_multiplier'] * self.config['stop_loss_percentage'])

        self.positions[token_id] = position

        # Logga trade i historik
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'token_id': token_id,
            'action': position.side,
            'price': current_price,
            'quantity': position_size,
            'value': current_price * position_size,
            'tx_hash': trade_result.get('transaction_hash'),
            'stop_loss': position.stop_loss,
            'take_profit': position.take_profit
        }

        self.trade_history.append(trade_record)
        logger.info(f"Created position: {position.side} {position.quantity} {token_id} at ${position.entry_price}")

    def calculate_position_size(self, confidence: float, current_price: float) -> float:
        """Beräkna position size baserat på confidence och risk management."""
        try:
            # Base size på tillgängligt kapital (simplifierat)
            available_capital = 1000.0  # $1000 som exempel

            # Risk per trade
            risk_amount = available_capital * self.config['max_risk_per_trade']

            # Justera för confidence
            confidence_multiplier = confidence

            # Beräkna position size
            position_value = risk_amount * confidence_multiplier

            # Konvertera till token quantity
            if current_price > 0:
                position_size = position_value / current_price
            else:
                position_size = 0

            # Säkerhetsgränser
            max_position_value = available_capital * self.config['max_total_risk']
            position_size = min(position_size, max_position_value / current_price)

            return max(0, position_size)

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0

    async def update_positions(self):
        """Uppdatera alla öppna positioner med aktuella priser."""
        for token_id, position in list(self.positions.items()):
            try:
                # Hämta aktuellt pris
                price_data = await self.market_analyzer.get_token_price(token_id)

                if price_data['success']:
                    current_price = price_data['price']
                    position.update_price(current_price)

                    # Kontrollera exit conditions
                    exit_reason = position.check_stop_conditions()
                    if exit_reason:
                        await self.close_position(token_id, exit_reason)

            except Exception as e:
                logger.error(f"Error updating position for {token_id}: {e}")
                continue

    async def handle_exits(self):
        """Hantera automatiska exits för positioner."""
        # Detta implementeras när vi har exit signaler
        pass

    async def close_position(self, token_id: str, reason: str):
        """Stäng en position."""
        if token_id not in self.positions:
            return

        position = self.positions[token_id]

        try:
            # Beräkna P&L
            pnl = position.unrealized_pnl
            self.daily_pnl += pnl
            self.total_pnl += pnl

            # Logga avslutad trade
            close_record = {
                'timestamp': datetime.now().isoformat(),
                'token_id': token_id,
                'action': 'CLOSE',
                'entry_price': position.entry_price,
                'exit_price': position.current_price,
                'quantity': position.quantity,
                'pnl': pnl,
                'reason': reason,
                'hold_time': (datetime.now() - position.timestamp).total_seconds() / 3600  # timmar
            }

            self.trade_history.append(close_record)

            logger.info(f"Closed position {token_id}: P&L ${pnl:.2f} ({reason})")

            # Ta bort position
            del self.positions[token_id]

        except Exception as e:
            logger.error(f"Error closing position {token_id}: {e}")

    async def check_risk_limits(self) -> bool:
        """Kontrollera att risk limits inte överskrids."""
        try:
            # Kontrollera max positioner
            if len(self.positions) >= self.config['max_positions']:
                return False

            # Kontrollera daily loss limit
            if self.daily_pnl < -self.max_daily_loss * 1000:  # Antag $1000 startkapital
                self.emergency_stop = True
                logger.error("Daily loss limit exceeded - emergency stop activated")
                return False

            # Kontrollera total risk
            total_exposure = sum(pos.current_price * pos.quantity for pos in self.positions.values())
            if total_exposure > 1000 * self.config['max_total_risk']:  # Antag $1000 startkapital
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return False

    async def update_portfolio_status(self):
        """Uppdatera portfolio status."""
        try:
            total_value = 1000.0  # Base kapital
            unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())

            self.portfolio_balance = total_value + self.total_pnl + unrealized_pnl

            logger.info(f"Portfolio status: Balance ${self.portfolio_balance:.2f}, "
                       f"P&L ${self.total_pnl:.2f}, Unrealized ${unrealized_pnl:.2f}")

        except Exception as e:
            logger.error(f"Error updating portfolio status: {e}")

    async def save_state(self):
        """Spara bot state till fil."""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'positions': {k: v.to_dict() for k, v in self.positions.items()},
                'portfolio_balance': self.portfolio_balance,
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.total_pnl,
                'trade_history': self.trade_history[-100:],  # Spara senaste 100 trades
                'config': self.config
            }

            async with aiofiles.open('crypto_trader_state.json', 'w') as f:
                await f.write(json.dumps(state, indent=2, default=str))

        except Exception as e:
            logger.error(f"Error saving state: {e}")

    async def load_state(self):
        """Ladda bot state från fil."""
        try:
            if os.path.exists('crypto_trader_state.json'):
                async with aiofiles.open('crypto_trader_state.json', 'r') as f:
                    state = json.loads(await f.read())

                # Återskapa positioner
                for token_id, pos_data in state.get('positions', {}).items():
                    position = Position(
                        token_id=pos_data['token_id'],
                        side=pos_data['side'],
                        entry_price=pos_data['entry_price'],
                        quantity=pos_data['quantity'],
                        timestamp=datetime.fromisoformat(pos_data['timestamp'])
                    )
                    position.stop_loss = pos_data.get('stop_loss')
                    position.take_profit = pos_data.get('take_profit')
                    position.current_price = pos_data.get('current_price', pos_data['entry_price'])
                    position.status = pos_data.get('status', 'open')

                    self.positions[token_id] = position

                self.portfolio_balance = state.get('portfolio_balance', 0.0)
                self.daily_pnl = state.get('daily_pnl', 0.0)
                self.total_pnl = state.get('total_pnl', 0.0)
                self.trade_history = state.get('trade_history', [])

                logger.info(f"Loaded state with {len(self.positions)} positions")

        except Exception as e:
            logger.error(f"Error loading state: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Returnera bot status."""
        return {
            'is_running': self.is_running,
            'trading_enabled': self.config['trading_enabled'],
            'positions_count': len(self.positions),
            'portfolio_balance': self.portfolio_balance,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'emergency_stop': self.emergency_stop,
            'positions': [pos.to_dict() for pos in self.positions.values()],
            'recent_trades': self.trade_history[-5:] if self.trade_history else []
        }
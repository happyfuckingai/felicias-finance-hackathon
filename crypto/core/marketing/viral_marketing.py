"""
AI-Driven Viral Marketing för HappyOS Crypto - Automatiserad community och hype-generering.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import random

logger = logging.getLogger(__name__)

class ViralContentGenerator:
    """Genererar viral content med AI."""
    
    def __init__(self):
        self.content_templates = {
            'moon_posts': [
                "🚀 {token} is about to MOON! 📈 Just deployed on {chain} with {features}! #DeFi #Crypto",
                "💎 DIAMOND HANDS ONLY! {token} showing massive potential 🔥 {metrics} #ToTheMoon",
                "🌙 {token} breaking resistance! Next stop: MOON 🚀 {analysis} #CryptoGems",
                "⚡ FLASH: {token} volume exploding! 📊 {volume_data} Don't miss out! #AltSeason"
            ],
            'technical_analysis': [
                "📊 {token} Technical Analysis:\n• RSI: {rsi}\n• MACD: {macd}\n• Support: ${support}\n• Target: ${target} 🎯",
                "🔍 Deep dive into {token}:\n• Market Cap: ${market_cap}\n• Liquidity: ${liquidity}\n• Holders: {holders}\n• Bullish signals detected! 📈",
                "⚡ {token} showing strong momentum:\n• 24h: +{change_24h}%\n• Volume: ${volume}\n• Next resistance: ${resistance}"
            ],
            'community_building': [
                "🔥 {token} community is GROWING! Join us:\n• Discord: {discord}\n• Telegram: {telegram}\n• Twitter: {twitter}\n#CryptoCommunity",
                "💪 {token} holders are the strongest community in crypto! 🦍\n• Diamond hands: {diamond_hands}%\n• Average hold time: {hold_time} days",
                "🎉 {token} just hit {milestone}! Celebrating with the best community in DeFi! 🥳"
            ],
            'fomo_inducing': [
                "⏰ LAST CHANCE: {token} presale ending in {time_left}! Don't miss the next 100x! 🚀",
                "🔥 {token} just got listed on {exchange}! Price already up {pump}%! FOMO is real! 📈",
                "💥 BREAKING: Whale just bought {amount} {token}! Smart money is accumulating! 🐋"
            ]
        }
        
        self.hashtag_pools = {
            'general': ['#Crypto', '#DeFi', '#Web3', '#Blockchain', '#ToTheMoon', '#HODL'],
            'trading': ['#Trading', '#TechnicalAnalysis', '#CryptoTrading', '#AltSeason', '#BullRun'],
            'community': ['#CryptoCommunity', '#DiamondHands', '#CryptoFamily', '#WAGMI'],
            'hype': ['#Moonshot', '#100x', '#GEM', '#EarlyBird', '#NextBigThing']
        }
    
    async def generate_viral_post(
        self,
        token_data: Dict[str, Any],
        post_type: str = 'moon_posts',
        sentiment: str = 'bullish'
    ) -> Dict[str, Any]:
        """
        Generera viral post för en token.
        
        Args:
            token_data: Token information
            post_type: Typ av post att generera
            sentiment: Sentiment (bullish, bearish, neutral)
            
        Returns:
            Generated post data
        """
        try:
            templates = self.content_templates.get(post_type, self.content_templates['moon_posts'])
            template = random.choice(templates)
            
            # Fyll i template med token data
            post_content = template.format(
                token=token_data.get('symbol', 'TOKEN'),
                chain=token_data.get('chain', 'Base'),
                features=self._generate_features_text(token_data),
                metrics=self._generate_metrics_text(token_data),
                analysis=self._generate_analysis_text(token_data),
                volume_data=self._generate_volume_text(token_data),
                rsi=token_data.get('rsi', random.randint(30, 70)),
                macd=random.choice(['Bullish', 'Bearish', 'Neutral']),
                support=token_data.get('support_level', random.uniform(0.5, 2.0)),
                target=token_data.get('target_price', random.uniform(2.0, 10.0)),
                market_cap=token_data.get('market_cap', random.randint(100000, 10000000)),
                liquidity=token_data.get('liquidity', random.randint(50000, 1000000)),
                holders=token_data.get('holders', random.randint(100, 10000)),
                change_24h=token_data.get('change_24h', random.uniform(-10, 50)),
                volume=token_data.get('volume_24h', random.randint(10000, 1000000)),
                resistance=token_data.get('resistance_level', random.uniform(1.5, 5.0))
            )
            
            # Lägg till hashtags
            hashtags = self._generate_hashtags(post_type, sentiment)
            post_content += f"\n\n{' '.join(hashtags)}"
            
            # Lägg till emojis för engagement
            post_content = self._add_engagement_emojis(post_content)
            
            return {
                'content': post_content,
                'type': post_type,
                'sentiment': sentiment,
                'hashtags': hashtags,
                'engagement_score': self._calculate_engagement_score(post_content),
                'platforms': ['twitter', 'telegram', 'discord'],
                'optimal_time': self._get_optimal_posting_time(),
                'target_audience': self._get_target_audience(post_type)
            }
            
        except Exception as e:
            logger.error(f"Error generating viral post: {e}")
            return {
                'content': f"🚀 {token_data.get('symbol', 'TOKEN')} is going to the moon! #Crypto #ToTheMoon",
                'error': str(e)
            }
    
    def _generate_features_text(self, token_data: Dict[str, Any]) -> str:
        """Generera features text."""
        features = [
            "Auto-liquidity",
            "Deflationary tokenomics", 
            "Community-driven",
            "AI-powered trading",
            "Cross-chain compatibility",
            "Yield farming",
            "NFT integration"
        ]
        return ", ".join(random.sample(features, random.randint(2, 4)))
    
    def _generate_metrics_text(self, token_data: Dict[str, Any]) -> str:
        """Generera metrics text."""
        return f"Volume: ${random.randint(10000, 500000):,}, Holders: {random.randint(500, 5000):,}"
    
    def _generate_analysis_text(self, token_data: Dict[str, Any]) -> str:
        """Generera analysis text."""
        analyses = [
            "Golden cross forming",
            "Breaking key resistance",
            "Bullish divergence detected",
            "Accumulation phase complete",
            "Whale activity increasing"
        ]
        return random.choice(analyses)
    
    def _generate_volume_text(self, token_data: Dict[str, Any]) -> str:
        """Generera volume text."""
        return f"24h volume: ${random.randint(50000, 1000000):,} (+{random.randint(50, 300)}%)"
    
    def _generate_hashtags(self, post_type: str, sentiment: str) -> List[str]:
        """Generera relevanta hashtags."""
        hashtags = []
        
        # Lägg till general hashtags
        hashtags.extend(random.sample(self.hashtag_pools['general'], 2))
        
        # Lägg till type-specific hashtags
        if post_type in ['moon_posts', 'fomo_inducing']:
            hashtags.extend(random.sample(self.hashtag_pools['hype'], 2))
        elif post_type == 'technical_analysis':
            hashtags.extend(random.sample(self.hashtag_pools['trading'], 2))
        elif post_type == 'community_building':
            hashtags.extend(random.sample(self.hashtag_pools['community'], 2))
        
        return hashtags[:6]  # Max 6 hashtags
    
    def _add_engagement_emojis(self, content: str) -> str:
        """Lägg till emojis för ökad engagement."""
        engagement_emojis = ['🔥', '💎', '🚀', '📈', '⚡', '💪', '🌙', '🎯']
        
        # Lägg till random emojis
        for _ in range(random.randint(1, 3)):
            emoji = random.choice(engagement_emojis)
            if emoji not in content:
                content += f" {emoji}"
        
        return content
    
    def _calculate_engagement_score(self, content: str) -> float:
        """Beräkna förväntad engagement score."""
        score = 0.5  # Base score
        
        # Emoji bonus
        emoji_count = len([c for c in content if ord(c) > 127])
        score += min(emoji_count * 0.1, 0.3)
        
        # Hashtag bonus
        hashtag_count = content.count('#')
        score += min(hashtag_count * 0.05, 0.2)
        
        # Length penalty/bonus
        if 50 <= len(content) <= 200:
            score += 0.1
        elif len(content) > 280:
            score -= 0.2
        
        # Hype words bonus
        hype_words = ['moon', 'rocket', 'diamond', 'gem', '100x', 'bullish']
        for word in hype_words:
            if word.lower() in content.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def _get_optimal_posting_time(self) -> str:
        """Få optimal posting time baserat på target audience."""
        # Crypto community är mest aktiv 14-16 och 20-22 UTC
        optimal_hours = [14, 15, 16, 20, 21, 22]
        hour = random.choice(optimal_hours)
        return f"{hour:02d}:00 UTC"
    
    def _get_target_audience(self, post_type: str) -> List[str]:
        """Få target audience för post type."""
        audiences = {
            'moon_posts': ['retail_investors', 'meme_traders', 'fomo_buyers'],
            'technical_analysis': ['technical_traders', 'experienced_investors'],
            'community_building': ['community_members', 'long_term_holders'],
            'fomo_inducing': ['retail_investors', 'quick_profit_seekers']
        }
        return audiences.get(post_type, ['general_crypto_audience'])

class SocialMediaAutomation:
    """Automatiserar social media posting och engagement."""
    
    def __init__(self):
        self.content_generator = ViralContentGenerator()
        self.posting_schedule = {}
        self.engagement_metrics = {}
    
    async def schedule_viral_campaign(
        self,
        token_data: Dict[str, Any],
        campaign_duration_hours: int = 24,
        posts_per_hour: int = 2
    ) -> Dict[str, Any]:
        """
        Schemalägg viral kampanj för en token.
        
        Args:
            token_data: Token information
            campaign_duration_hours: Kampanjens längd i timmar
            posts_per_hour: Antal posts per timme
            
        Returns:
            Campaign schedule
        """
        try:
            campaign_id = f"campaign_{token_data.get('symbol', 'TOKEN')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generera posting schedule
            schedule = []
            start_time = datetime.now()
            
            for hour in range(campaign_duration_hours):
                for post_num in range(posts_per_hour):
                    post_time = start_time + timedelta(
                        hours=hour,
                        minutes=random.randint(0, 59)
                    )
                    
                    # Variera post types
                    post_types = ['moon_posts', 'technical_analysis', 'community_building', 'fomo_inducing']
                    weights = [0.4, 0.2, 0.2, 0.2]  # Mer moon posts
                    post_type = random.choices(post_types, weights=weights)[0]
                    
                    # Generera content
                    post_content = await self.content_generator.generate_viral_post(
                        token_data, post_type
                    )
                    
                    schedule.append({
                        'post_id': f"{campaign_id}_post_{len(schedule)}",
                        'scheduled_time': post_time.isoformat(),
                        'content': post_content,
                        'platforms': ['twitter', 'telegram', 'discord'],
                        'status': 'scheduled'
                    })
            
            # Spara schedule
            self.posting_schedule[campaign_id] = {
                'campaign_id': campaign_id,
                'token': token_data.get('symbol', 'TOKEN'),
                'start_time': start_time.isoformat(),
                'duration_hours': campaign_duration_hours,
                'total_posts': len(schedule),
                'schedule': schedule,
                'status': 'active'
            }
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'total_posts_scheduled': len(schedule),
                'estimated_reach': self._estimate_campaign_reach(schedule),
                'estimated_engagement': self._estimate_campaign_engagement(schedule)
            }
            
        except Exception as e:
            logger.error(f"Error scheduling viral campaign: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_scheduled_posts(self, campaign_id: str) -> Dict[str, Any]:
        """
        Utför schemalagda posts för en kampanj.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Execution results
        """
        try:
            if campaign_id not in self.posting_schedule:
                return {
                    'success': False,
                    'error': 'Campaign not found'
                }
            
            campaign = self.posting_schedule[campaign_id]
            executed_posts = []
            failed_posts = []
            
            for post in campaign['schedule']:
                scheduled_time = datetime.fromisoformat(post['scheduled_time'])
                
                # Kontrollera om det är dags att posta
                if datetime.now() >= scheduled_time and post['status'] == 'scheduled':
                    try:
                        # Simulera posting till olika plattformar
                        post_results = await self._post_to_platforms(post)
                        
                        post['status'] = 'posted'
                        post['posted_time'] = datetime.now().isoformat()
                        post['results'] = post_results
                        
                        executed_posts.append(post)
                        
                        logger.info(f"Posted {post['post_id']} to {len(post['platforms'])} platforms")
                        
                    except Exception as e:
                        post['status'] = 'failed'
                        post['error'] = str(e)
                        failed_posts.append(post)
                        logger.error(f"Failed to post {post['post_id']}: {e}")
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'executed_posts': len(executed_posts),
                'failed_posts': len(failed_posts),
                'total_reach': sum([p.get('results', {}).get('estimated_reach', 0) for p in executed_posts]),
                'total_engagement': sum([p.get('results', {}).get('estimated_engagement', 0) for p in executed_posts])
            }
            
        except Exception as e:
            logger.error(f"Error executing scheduled posts: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _post_to_platforms(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Posta till olika plattformar (simulerat)."""
        results = {}
        
        for platform in post['platforms']:
            # Simulera posting
            await asyncio.sleep(0.1)  # Simulera API call
            
            # Simulera engagement baserat på content quality
            engagement_score = post['content'].get('engagement_score', 0.5)
            
            if platform == 'twitter':
                estimated_reach = random.randint(100, 1000) * (1 + engagement_score)
                estimated_engagement = estimated_reach * random.uniform(0.02, 0.08)
            elif platform == 'telegram':
                estimated_reach = random.randint(50, 500) * (1 + engagement_score)
                estimated_engagement = estimated_reach * random.uniform(0.05, 0.15)
            elif platform == 'discord':
                estimated_reach = random.randint(20, 200) * (1 + engagement_score)
                estimated_engagement = estimated_reach * random.uniform(0.10, 0.25)
            else:
                estimated_reach = 100
                estimated_engagement = 10
            
            results[platform] = {
                'posted': True,
                'estimated_reach': int(estimated_reach),
                'estimated_engagement': int(estimated_engagement),
                'post_url': f"https://{platform}.com/post/{random.randint(100000, 999999)}"
            }
        
        return results
    
    def _estimate_campaign_reach(self, schedule: List[Dict[str, Any]]) -> int:
        """Estimera total reach för kampanj."""
        total_reach = 0
        
        for post in schedule:
            engagement_score = post['content'].get('engagement_score', 0.5)
            platforms_count = len(post['platforms'])
            
            # Base reach per platform
            base_reach = {
                'twitter': 500,
                'telegram': 200,
                'discord': 100
            }
            
            post_reach = 0
            for platform in post['platforms']:
                post_reach += base_reach.get(platform, 100) * (1 + engagement_score)
            
            total_reach += post_reach
        
        return int(total_reach)
    
    def _estimate_campaign_engagement(self, schedule: List[Dict[str, Any]]) -> int:
        """Estimera total engagement för kampanj."""
        total_engagement = 0
        
        for post in schedule:
            engagement_score = post['content'].get('engagement_score', 0.5)
            
            # Engagement rates per platform
            engagement_rates = {
                'twitter': 0.05,
                'telegram': 0.10,
                'discord': 0.20
            }
            
            for platform in post['platforms']:
                base_reach = 500 if platform == 'twitter' else 200 if platform == 'telegram' else 100
                reach = base_reach * (1 + engagement_score)
                engagement = reach * engagement_rates.get(platform, 0.05)
                total_engagement += engagement
        
        return int(total_engagement)
    
    async def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Hämta kampanj-analytics."""
        if campaign_id not in self.posting_schedule:
            return {'error': 'Campaign not found'}
        
        campaign = self.posting_schedule[campaign_id]
        
        # Beräkna statistik
        total_posts = len(campaign['schedule'])
        posted_count = len([p for p in campaign['schedule'] if p['status'] == 'posted'])
        failed_count = len([p for p in campaign['schedule'] if p['status'] == 'failed'])
        
        total_reach = 0
        total_engagement = 0
        
        for post in campaign['schedule']:
            if post['status'] == 'posted' and 'results' in post:
                for platform_result in post['results'].values():
                    total_reach += platform_result.get('estimated_reach', 0)
                    total_engagement += platform_result.get('estimated_engagement', 0)
        
        return {
            'campaign_id': campaign_id,
            'token': campaign['token'],
            'status': campaign['status'],
            'total_posts': total_posts,
            'posted_count': posted_count,
            'failed_count': failed_count,
            'success_rate': posted_count / total_posts if total_posts > 0 else 0,
            'total_reach': total_reach,
            'total_engagement': total_engagement,
            'engagement_rate': total_engagement / total_reach if total_reach > 0 else 0,
            'roi_estimate': self._calculate_campaign_roi(total_reach, total_engagement)
        }
    
    def _calculate_campaign_roi(self, reach: int, engagement: int) -> Dict[str, Any]:
        """Beräkna kampanj ROI."""
        # Simulerade värden
        cost_per_post = 5  # $5 per post
        value_per_engagement = 0.10  # $0.10 per engagement
        
        total_cost = len(self.posting_schedule) * cost_per_post
        total_value = engagement * value_per_engagement
        
        roi = (total_value - total_cost) / total_cost if total_cost > 0 else 0
        
        return {
            'total_cost': total_cost,
            'total_value': total_value,
            'roi_percentage': roi * 100,
            'break_even_engagement': total_cost / value_per_engagement
        }

# Global viral marketing instance
global_viral_marketing = SocialMediaAutomation()

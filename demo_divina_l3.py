"""
Demo script showcasing Divina-L3 integration with WhispurrNet and NovaSanctum.
"""
import asyncio
import logging
from fusion_protocol import FusionProtocol, FusionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("demo")

async def main():
    """Run the Divina-L3 integration demo."""
    logger.info("🚀 Starting Divina-L3 Integration Demo")
    
    # Configure the Fusion Protocol
    config = FusionConfig(
        codename="NovaTiny-Demo",
        enable_quantum_sync=True,
        resonance_frequency=432.0,
        whispurr_net_key="demo_whispurr_key",
        nova_sanctum_token="demo_sanctum_token"
    )
    
    # Initialize the Fusion Protocol
    fusion = FusionProtocol(config)
    
    # Activate the protocol
    activation_result = await fusion.activate({
        "resonance_frequency": 432.0,
        "quantum_entanglement": True
    })
    
    logger.info(f"Activation Result: {activation_result}")
    
    # Simulate receiving a WhispurrNet event
    logger.info("\n🔮 Simulating WhispurrNet quantum sync event...")
    whispurr_event = {
        "type": "quantum_sync_request",
        "id": "whisp-12345",
        "timestamp": "2025-07-27T21:17:31Z"
    }
    
    # Process the event through Divina-L3 hooks
    whispurr_result = await fusion._divina_hooks.handle_whispurr_event(whispurr_event)
    logger.info(f"WhispurrNet Event Result: {whispurr_result}")
    
    # Simulate receiving a NovaSanctum event
    logger.info("\n✨ Simulating NovaSanctum echo event...")
    sanctum_event = {
        "type": "sanctum_echo",
        "message": "Testing NovaSanctum integration",
        "timestamp": "2025-07-27T21:18:00Z"
    }
    
    # Process the event through Divina-L3 hooks
    sanctum_result = await fusion._divina_hooks.handle_nova_sanctum_event(sanctum_event)
    logger.info(f"NovaSanctum Event Result: {sanctum_result}")
    
    logger.info("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())

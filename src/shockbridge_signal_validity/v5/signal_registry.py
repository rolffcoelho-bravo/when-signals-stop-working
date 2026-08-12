from src.shockbridge_signal_validity.v5.signal_microstructure import MicrostructureSignals

# In V3, signal registry mapped classical signals like Bollinger, RSI, MACD.
# In v5, we map the new institutional signals.

v5_SIGNAL_REGISTRY = {
    'microstructure': MicrostructureSignals
}

def get_v5_signals():
    """
    Returns the instantiated v5 signals ready for feature generation.
    """
    instances = {}
    for name, signal_class in v5_SIGNAL_REGISTRY.items():
        instances[name] = signal_class()
    return instances

from src.shockbridge_signal_validity.v4.signal_microstructure import MicrostructureSignals

# In V3, signal registry mapped classical signals like Bollinger, RSI, MACD.
# In V4, we map the new institutional signals.

V4_SIGNAL_REGISTRY = {
    'microstructure': MicrostructureSignals
}

def get_v4_signals():
    """
    Returns the instantiated V4 signals ready for feature generation.
    """
    instances = {}
    for name, signal_class in V4_SIGNAL_REGISTRY.items():
        instances[name] = signal_class()
    return instances

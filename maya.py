from core.dimensions import MayaDimensions
from core.heartbeat import MayaHeartbeat
from core.state import MayaStateManager
from core.logger import DataLogger
from visualization.mindscape import Mindscape

dimensions    = MayaDimensions()
state_manager = MayaStateManager()
state_manager.load(dimensions)

logger   = DataLogger()
heartbeat = MayaHeartbeat(dimensions, logger=logger)

# Run experiment before launching Mindscape
heartbeat.run_experiment()

mindscape = Mindscape(heartbeat)

try:
    mindscape.run()
finally:
    state_manager.save(dimensions)
    logger.close()
    print("--- MAYA RESTS ---")
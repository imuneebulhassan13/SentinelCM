from state.state_manager import load_state
from state.state_manager import save_state

print(load_state())

save_state("Application", 500)

print(load_state())
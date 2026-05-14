# Research: PRISM Layer 3+4 (Digital Twin & RL Optimizer)

## Decision 1: ODE Solver Choice
- **Decision**: Use `torchdiffeq` with the `dopri5` (Runge-Kutta 4/5) solver and the adjoint method.
- **Rationale**: The adjoint method (Chen et al. 2018) allows for memory-efficient backpropagation through the ODE solver, which is critical for the long trajectories expected in patient health modeling. `dopri5` provides a good balance between speed and accuracy for non-stiff systems.
- **Alternatives Considered**: `torchsde` (only if modeling stochastic dynamics, which adds unnecessary complexity for v1), `euler` (too inaccurate for medical trajectories).

## Decision 2: RL Algorithm for Intervention Optimization
- **Decision**: Proximal Policy Optimization (PPO) via `stable-baselines3`.
- **Rationale**: PPO is stable, reliable, and handles discrete action spaces well. Our intervention space (15 actions) is discrete, and PPO's clipping mechanism prevents drastic policy updates that could lead to clinical instability in simulations.
- **Alternatives Considered**: DQN (can be unstable in high-dimensional state spaces), SAC (typically for continuous actions).

## Decision 3: Handling Irregular Time Series
- **Decision**: Latent ODE architecture (ODE-RNN encoder).
- **Rationale**: Standard RNNs assume fixed time steps. Patient visits are irregular. ODE-RNNs evolve the hidden state continuously between observations, capturing the natural "decay" or "evolution" of physiological states during unobserved intervals.
- **Alternatives Considered**: Masking/Padding in standard GRU (loses the temporal distance information), Time-delta features in GRU (better, but doesn't model the underlying continuous dynamics).

## Decision 4: Edge Deployment (Android)
- **Decision**: TFLite conversion with `flex` operators or ONNX Runtime Mobile.
- **Rationale**: Neural ODEs involve complex control flow (loops in the solver). TFLite's core kernels may not support all ODE solvers. We will research ONNX Runtime as a fallback if TFLite's `flex` operators add too much binary size.
- **NEEDS CLARIFICATION**: Does the target Android hardware have NPU support for these architectures? (Assumption: No, focusing on CPU/GPU optimization).

## Decision 5: Reward Function Design
- **Decision**: Quality-Adjusted Life Years (QALY) gain minus normalized cost.
- **Rationale**: Aligning with international health economics standards. Using the Ayushman Bharat database ensures the cost-benefit analysis is grounded in the Indian healthcare context.
- **Alternatives Considered**: Simple accuracy of prediction (doesn't account for health outcome).

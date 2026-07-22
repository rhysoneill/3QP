"""
Belief type constants and drift coefficients for 3QP twin engine.

All belief update equations must reference named constants from this file.
No magic numbers in belief update logic.

DESIGN CONTRACT:
    All coefficients must be explainable in plain language.
    No time-indexed terms — all drift equations are driven by perception inputs.
    Coefficients are calibration targets — they may be tuned against real data.
"""

# ---------------------------------------------------------------------------
# Inertia coefficients — how sticky each belief is
# Higher = slower to change (0.0 = no memory, 1.0 = never changes)
# ---------------------------------------------------------------------------

INERTIA_COFFEE_SCARCITY       = 0.65   # Daily experience updates this fairly quickly
INERTIA_DISTRIBUTION_FAIRNESS = 0.80   # Fairness beliefs are stickier — harder to dislodge
INERTIA_RESUPPLY_RELIABILITY  = 0.70   # Updates on comms/arrival events
INERTIA_MC_SUPPORT            = 0.75   # Trust in institution changes slowly
INERTIA_CREW_COHESION         = 0.85   # Crew relationship beliefs are very sticky
INERTIA_MISSION_VIABILITY     = 0.88   # Hope/resignation shifts slowly

# ---------------------------------------------------------------------------
# MC communication impact on beliefs (immediate, per communication received)
# ---------------------------------------------------------------------------

MC_SUPPORT_BOOST_REASSURANCE   = 0.12
MC_SUPPORT_BOOST_ACKNOWLEDGMENT = 0.07
MC_SUPPORT_BOOST_DIRECTION      = 0.04
MC_SUPPORT_BOOST_SUPPORT        = 0.14
MC_SUPPORT_BOOST_DEFAULT        = 0.05

MC_RELIABILITY_BOOST_PROMISE   = 0.15   # When resupply is promised
MC_RELIABILITY_BOOST_ARRIVAL   = 0.20   # When resupply actually arrives on time

# ---------------------------------------------------------------------------
# Overdue resupply decay — per day past ETA
# ---------------------------------------------------------------------------

MC_RELIABILITY_DECAY_OVERDUE   = 0.04   # Per day past promised arrival
MC_SUPPORT_DECAY_OVERDUE       = 0.03   # Per day past promised arrival

# ---------------------------------------------------------------------------
# Mission viability drivers
# ---------------------------------------------------------------------------

VIABILITY_SCARCITY_WEIGHT      = 0.35   # High scarcity belief pulls viability down
VIABILITY_FAIRNESS_WEIGHT      = 0.25   # Low fairness belief pulls viability down
VIABILITY_MC_SUPPORT_WEIGHT    = 0.25   # Low MC support belief pulls viability down
VIABILITY_COHESION_WEIGHT      = 0.15   # Low crew cohesion pulls viability down

# ---------------------------------------------------------------------------
# Personality modulation of inertia
# Neuroticism reduces inertia (more reactive)
# Conscientiousness increases inertia (more evidence required to update)
# ---------------------------------------------------------------------------

NEUROTICISM_INERTIA_FACTOR     = 0.12   # Per unit above/below 0.5
CONSCIENTIOUSNESS_INERTIA_FACTOR = 0.08

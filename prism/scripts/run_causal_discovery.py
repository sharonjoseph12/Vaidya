"""T016 - CLI entry point for running causal discovery."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PRISM Layer 2 — Run causal discovery pipeline (PCMCI + FCI)"
    )
    parser.add_argument("--panel", required=True, help="Path to panel_dataset.pkl")
    parser.add_argument("--nfhs", default=None, help="Path to nfhs_india.pkl (optional)")
    parser.add_argument("--output-dir", default="layer2_reason/graphs", help="Output directory for graphs")
    parser.add_argument("--diseases", nargs="+",
                        default=["tb", "anemia", "heart_failure", "general"],
                        help="Disease cohorts to run PCMCI on")
    parser.add_argument("--tau-max", type=int, default=20, help="Maximum time lag (PCMCI)")
    parser.add_argument("--no-validate", action="store_true", help="Skip medical knowledge validation")

    args = parser.parse_args()

    panel_path = Path(args.panel)
    if not panel_path.exists():
        logger.error("Panel file not found: %s", panel_path)
        sys.exit(1)

    logger.info("Starting causal discovery pipeline")
    logger.info("  Panel: %s", panel_path)
    logger.info("  NFHS: %s", args.nfhs)
    logger.info("  Output: %s", args.output_dir)
    logger.info("  Diseases: %s", args.diseases)
    logger.info("  Tau max: %d", args.tau_max)

    from layer2_reason.causal_discovery.discovery_pipeline import run_discovery_pipeline

    graphs = run_discovery_pipeline(
        panel_path=panel_path,
        nfhs_path=args.nfhs,
        graphs_dir=args.output_dir,
        diseases=args.diseases,
        tau_max=args.tau_max,
        validate=not args.no_validate,
    )

    logger.info("✓ Discovery complete | %d graphs saved to %s", len(graphs), args.output_dir)
    for disease, G in graphs.items():
        logger.info("  %s: %d nodes, %d edges", disease, G.number_of_nodes(), G.number_of_edges())


if __name__ == "__main__":
    main()

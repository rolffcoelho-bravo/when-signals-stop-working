from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .adapters import build_adapter
from .data_contract import CanonicalMarketFrame


def run_data_adapter(
    config: Mapping[str, Any],
    output_directory: str | Path,
) -> CanonicalMarketFrame:
    adapter_type = str(config.get("adapter_type", "file"))
    adapter_config = config.get("adapter")
    if not isinstance(adapter_config, Mapping):
        raise ValueError("Configuration requires an 'adapter' mapping.")

    adapter = build_adapter(adapter_type)
    result = adapter.load(adapter_config)

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    result.frame.to_csv(output / "canonical_market_data.csv", index=False)
    (output / "source_manifest.json").write_text(
        json.dumps(
            {
                **result.manifest.to_dict(),
                "manifest_sha256": result.manifest.manifest_sha256,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "validation_report.json").write_text(
        json.dumps(result.validation.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result.require_valid()
    return result

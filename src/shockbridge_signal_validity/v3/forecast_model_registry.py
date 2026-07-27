from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import itertools
import json
from pathlib import Path
from typing import Any, Iterable

from .forecast_contract import ForecastProtocolViolation


TARGET_TASKS = {
    "direction": "CLASSIFICATION",
    "expected_return": "REGRESSION",
    "large_move_probability": "CLASSIFICATION",
}


@dataclass(frozen=True)
class ForecastPipelineSpec:
    pipeline_spec_id: str
    target_name: str
    task_type: str
    model_family: str
    role: str
    window_id: str
    window_observations: int | None
    hyperparameters: tuple[tuple[str, object], ...]
    executable: bool
    ineligibility_status: str | None
    complexity_rank: int

    def parameter_dict(self) -> dict[str, object]:
        return dict(self.hyperparameters)

    def manifest_record(self) -> dict[str, object]:
        return {
            "pipeline_spec_id": self.pipeline_spec_id,
            "target_name": self.target_name,
            "task_type": self.task_type,
            "model_family": self.model_family,
            "role": self.role,
            "window_id": self.window_id,
            "window_observations": self.window_observations,
            "hyperparameters": self.parameter_dict(),
            "executable": self.executable,
            "ineligibility_status": self.ineligibility_status,
            "complexity_rank": self.complexity_rank,
            "automatic_selection_performed": False,
        }


def _pipeline_id(payload: dict[str, object]) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "v3g5pipe:" + sha256(material.encode("utf-8")).hexdigest()


def _spec(
    *,
    target_name: str,
    task_type: str,
    model_family: str,
    role: str,
    window_id: str,
    window_observations: int | None,
    hyperparameters: dict[str, object],
    executable: bool,
    ineligibility_status: str | None,
    complexity_rank: int,
) -> ForecastPipelineSpec:
    payload: dict[str, object] = {
        "target_name": target_name,
        "task_type": task_type,
        "model_family": model_family,
        "role": role,
        "window_id": window_id,
        "window_observations": window_observations,
        "hyperparameters": hyperparameters,
        "executable": executable,
        "ineligibility_status": ineligibility_status,
        "complexity_rank": complexity_rank,
    }
    return ForecastPipelineSpec(
        pipeline_spec_id=_pipeline_id(payload),
        target_name=target_name,
        task_type=task_type,
        model_family=model_family,
        role=role,
        window_id=window_id,
        window_observations=window_observations,
        hyperparameters=tuple(sorted(hyperparameters.items())),
        executable=executable,
        ineligibility_status=ineligibility_status,
        complexity_rank=complexity_rank,
    )


def _family_configurations(
    forecast_contract: dict[str, Any],
    target_name: str,
) -> list[tuple[str, str, dict[str, object], bool, str | None, int]]:
    task_type = TARGET_TASKS[target_name]
    model_families = forecast_contract["model_families"]
    values: list[tuple[str, str, dict[str, object], bool, str | None, int]] = []

    regularized = model_families["regularized_linear"]
    parameter_name = "C" if task_type == "CLASSIFICATION" else "alpha"
    source_name = "classification_C" if task_type == "CLASSIFICATION" else "regression_alpha"
    for parameter in regularized[source_name]:
        values.append(
            (
                "regularized_linear",
                str(regularized["role"]),
                {parameter_name: float(parameter)},
                True,
                None,
                1,
            )
        )

    spline = model_families["spline_regularized"]
    spline_source = "classification_C" if task_type == "CLASSIFICATION" else "regression_alpha"
    for knots, parameter in itertools.product(spline["n_knots"], spline[spline_source]):
        values.append(
            (
                "spline_regularized",
                str(spline["role"]),
                {
                    "degree": int(spline["degree"]),
                    "n_knots": int(knots),
                    parameter_name: float(parameter),
                },
                True,
                None,
                2,
            )
        )

    boosting = model_families["shallow_hist_gradient_boosting"]
    for learning_rate, leaves, iterations, minimum_leaf, regularization in itertools.product(
        boosting["learning_rate"],
        boosting["max_leaf_nodes"],
        boosting["max_iter"],
        boosting["min_samples_leaf"],
        boosting["l2_regularization"],
    ):
        values.append(
            (
                "shallow_hist_gradient_boosting",
                str(boosting["role"]),
                {
                    "learning_rate": float(learning_rate),
                    "max_leaf_nodes": int(leaves),
                    "max_iter": int(iterations),
                    "min_samples_leaf": int(minimum_leaf),
                    "l2_regularization": float(regularization),
                },
                True,
                None,
                3,
            )
        )

    dynamic = model_families["time_varying_regularized_glm"]
    for forgetting_factor in dynamic["forgetting_factors"]:
        values.append(
            (
                "time_varying_regularized_glm",
                str(dynamic["role"]),
                {
                    "forgetting_factor": float(forgetting_factor),
                    "minimum_training_observations": int(
                        dynamic["minimum_training_observations"]
                    ),
                },
                True,
                None,
                4,
            )
        )

    gated = model_families["state_space_or_markov_switching"]
    values.append(
        (
            "state_space_or_markov_switching",
            str(gated["role"]),
            {
                "minimum_regime_occupancy": int(gated["minimum_regime_occupancy"]),
                "identifiability_required": bool(gated["identifiability_required"]),
                "automatic_state_count_selection_prohibited": bool(
                    gated["automatic_state_count_selection_prohibited"]
                ),
            },
            False,
            "INELIGIBLE_IMPLEMENTATION_NOT_AUTHORIZED",
            5,
        )
    )
    return values


def build_pipeline_registry(
    forecast_contract: dict[str, Any],
    implementation_contract: dict[str, Any],
) -> list[ForecastPipelineSpec]:
    expected_targets = set(TARGET_TASKS)
    if set(forecast_contract.get("targets", {})) != expected_targets:
        raise ForecastProtocolViolation("Gate V3-5 target registry changed.")
    windows = implementation_contract.get("window_schemes")
    if not isinstance(windows, list) or len(windows) != 3:
        raise ForecastProtocolViolation("Gate V3-5 window-scheme registry changed.")

    records: list[ForecastPipelineSpec] = []
    for target_name, task_type in TARGET_TASKS.items():
        configurations = _family_configurations(forecast_contract, target_name)
        if sum(bool(item[3]) for item in configurations) != 17:
            raise ForecastProtocolViolation(
                f"Executable model configuration identity failed for {target_name}."
            )
        for window in windows:
            window_id = str(window["window_id"])
            observations = window.get("observations")
            window_observations = None if observations is None else int(observations)
            for family, role, parameters, executable, status, rank in configurations:
                records.append(
                    _spec(
                        target_name=target_name,
                        task_type=task_type,
                        model_family=family,
                        role=role,
                        window_id=window_id,
                        window_observations=window_observations,
                        hyperparameters=parameters,
                        executable=executable,
                        ineligibility_status=status,
                        complexity_rank=rank,
                    )
                )

    if len(records) != 162:
        raise ForecastProtocolViolation(
            f"Pipeline registry identity failed: expected 162, observed {len(records)}."
        )
    if len({record.pipeline_spec_id for record in records}) != len(records):
        raise ForecastProtocolViolation("Pipeline specification identifiers are not unique.")
    if sum(record.executable for record in records) != 153:
        raise ForecastProtocolViolation("Executable pipeline specification count changed.")
    if sum(not record.executable for record in records) != 9:
        raise ForecastProtocolViolation("Gated pipeline specification count changed.")
    return sorted(
        records,
        key=lambda record: (
            record.target_name,
            record.window_id,
            record.complexity_rank,
            record.model_family,
            record.pipeline_spec_id,
        ),
    )


def load_contracts(
    forecast_contract_path: str | Path,
    implementation_contract_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    forecast = json.loads(Path(forecast_contract_path).read_text(encoding="utf-8"))
    implementation = json.loads(
        Path(implementation_contract_path).read_text(encoding="utf-8")
    )
    if not isinstance(forecast, dict) or not isinstance(implementation, dict):
        raise ForecastProtocolViolation("V3-5 model contracts must be JSON objects.")
    if implementation.get("status") != "IMPLEMENTATION_CONTRACT_FROZEN":
        raise ForecastProtocolViolation("V3-5 model implementation contract is not frozen.")
    if implementation.get("real_development_model_fitting_authorized") is not False:
        raise ForecastProtocolViolation("Real development model fitting was authorized early.")
    return forecast, implementation


def pipeline_registry_manifest(specs: Iterable[ForecastPipelineSpec]) -> dict[str, object]:
    records = list(specs)
    return {
        "schema_version": "v3.g5-pipeline-registry.v1",
        "pipeline_specifications": len(records),
        "executable_pipeline_specifications": sum(record.executable for record in records),
        "gated_pipeline_specifications": sum(not record.executable for record in records),
        "targets": sorted({record.target_name for record in records}),
        "model_families": sorted({record.model_family for record in records}),
        "window_schemes": sorted({record.window_id for record in records}),
        "automatic_selection_performed": False,
        "real_development_model_fitting_performed": False,
        "records": [record.manifest_record() for record in records],
    }

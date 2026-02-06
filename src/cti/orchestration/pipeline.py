from __future__ import annotations

from typing import Any, Dict, List
import logging


class Pipeline:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        pipeline_cfg = config.get("pipeline", {})
        self.stages: List[str] = pipeline_cfg.get("stages", [])
        self.fail_fast: bool = bool(pipeline_cfg.get("fail_fast", True))

        self._handlers = {
            "ingestion": self._run_ingestion,
            "preprocessing": self._run_preprocessing,
            "ioc_extraction": self._run_ioc_extraction,
            "analysis": self._run_analysis,
            "correlation": self._run_correlation,
            "scoring": self._run_scoring,
            "storage": self._run_storage,
            "reporting": self._run_reporting,
        }

    def run(self) -> None:
        self.logger.info("Pipeline start")
        for stage in self.stages:
            handler = self._handlers.get(stage)
            if not handler:
                self._handle_error(ValueError(f"Unknown stage: {stage}"))
                continue

            self.logger.info(f"Stage start: {stage}")
            try:
                handler()
                self.logger.info(f"Stage complete: {stage}")
            except Exception as exc:  # noqa: BLE001 - pipeline needs controlled fail fast
                self._handle_error(exc)
        self.logger.info("Pipeline complete")

    def _handle_error(self, exc: Exception) -> None:
        if self.fail_fast:
            raise exc
        self.logger.error(str(exc))

    def _run_ingestion(self) -> None:
        from cti.ingestion.manager import IngestionManager
        from cti.ingestion.writer import write_raw_events

        ingestion_cfg = self.config.get("ingestion", {})
        output_path = ingestion_cfg.get("output_raw_path", "data/raw_events.jsonl")

        manager = IngestionManager(config=self.config, logger=self.logger)
        events = manager.collect()
        count = write_raw_events(events, output_path)
        self.logger.info("Ingestion output saved path=%s count=%d", output_path, count)

    def _run_preprocessing(self) -> None:
        from cti.preprocessing.manager import PreprocessingManager
        from cti.preprocessing.writer import write_normalized_events

        preprocessing_cfg = self.config.get("preprocessing", {})
        ingestion_cfg = self.config.get("ingestion", {})

        input_path = preprocessing_cfg.get(
            "input_raw_path", ingestion_cfg.get("output_raw_path", "data/raw_events.jsonl")
        )
        output_path = preprocessing_cfg.get("output_normalized_path", "data/normalized_events.jsonl")

        manager = PreprocessingManager(config=self.config, logger=self.logger)
        events = manager.read_input(input_path)
        normalized = manager.normalize(events)
        count = write_normalized_events(normalized, output_path)
        self.logger.info("Preprocessing output saved path=%s count=%d", output_path, count)

    def _run_ioc_extraction(self) -> None:
        from cti.ioc_extraction.manager import IOCExtractionManager
        from cti.ioc_extraction.reader import read_normalized_events
        from cti.ioc_extraction.writer import write_iocs

        extraction_cfg = self.config.get("ioc_extraction", {})
        preprocessing_cfg = self.config.get("preprocessing", {})

        input_path = extraction_cfg.get(
            "input_normalized_path",
            preprocessing_cfg.get("output_normalized_path", "data/normalized_events.jsonl"),
        )
        output_path = extraction_cfg.get("output_iocs_path", "data/iocs.jsonl")

        events = read_normalized_events(input_path)
        manager = IOCExtractionManager(config=self.config, logger=self.logger)
        iocs = manager.extract(events)
        count = write_iocs(iocs, output_path)
        self.logger.info("IOC extraction output saved path=%s count=%d", output_path, count)

    def _run_analysis(self) -> None:
        from cti.analysis.manager import AnalysisManager
        from cti.analysis.reader import read_normalized_events
        from cti.analysis.writer import write_analysis_results

        analysis_cfg = self.config.get("analysis", {})
        preprocessing_cfg = self.config.get("preprocessing", {})

        input_path = analysis_cfg.get(
            "input_normalized_path",
            preprocessing_cfg.get("output_normalized_path", "data/normalized_events.jsonl"),
        )
        output_path = analysis_cfg.get("output_analysis_path", "data/analysis_results.jsonl")

        events = read_normalized_events(input_path)
        manager = AnalysisManager(config=self.config, logger=self.logger)
        results = manager.analyze(events)
        count = write_analysis_results(results, output_path)
        self.logger.info("Analysis output saved path=%s count=%d", output_path, count)

    def _run_correlation(self) -> None:
        from cti.correlation.analysis_reader import read_analysis_results
        from cti.correlation.ioc_reader import read_iocs
        from cti.correlation.manager import CorrelationManager
        from cti.correlation.writer import write_campaigns, write_correlation_results
        from cti.analysis.reader import read_normalized_events as read_norm_for_corr

        correlation_cfg = self.config.get("correlation", {})
        analysis_cfg = self.config.get("analysis", {})
        preprocessing_cfg = self.config.get("preprocessing", {})
        ioc_cfg = self.config.get("ioc_extraction", {})

        input_analysis_path = correlation_cfg.get(
            "input_analysis_path",
            analysis_cfg.get("output_analysis_path", "data/analysis_results.jsonl"),
        )
        input_iocs_path = correlation_cfg.get(
            "input_iocs_path",
            ioc_cfg.get("output_iocs_path", "data/iocs.jsonl"),
        )
        input_normalized_path = correlation_cfg.get(
            "input_normalized_path",
            preprocessing_cfg.get("output_normalized_path", "data/normalized_events.jsonl"),
        )
        output_correlation_path = correlation_cfg.get("output_correlation_path", "data/correlation_results.jsonl")
        output_campaigns_path = correlation_cfg.get("output_campaigns_path", "data/campaigns.jsonl")

        events = list(read_norm_for_corr(input_normalized_path))
        analyses = list(read_analysis_results(input_analysis_path))
        iocs = list(read_iocs(input_iocs_path))

        manager = CorrelationManager(config=self.config, logger=self.logger)
        results, campaigns = manager.correlate(events=events, iocs=iocs, analyses=analyses)

        count_results = write_correlation_results(results, output_correlation_path)
        count_campaigns = write_campaigns(campaigns, output_campaigns_path)
        self.logger.info(
            "Correlation output saved results=%s (%d) campaigns=%s (%d)",
            output_correlation_path,
            count_results,
            output_campaigns_path,
            count_campaigns,
        )

    def _run_scoring(self) -> None:
        from cti.scoring.analysis_reader import read_analysis_results
        from cti.scoring.correlation_reader import read_correlation_results
        from cti.scoring.ioc_counter import count_iocs_by_event
        from cti.scoring.manager import ScoringManager
        from cti.scoring.writer import write_scores

        scoring_cfg = self.config.get("scoring", {})
        analysis_cfg = self.config.get("analysis", {})
        correlation_cfg = self.config.get("correlation", {})
        ioc_cfg = self.config.get("ioc_extraction", {})

        input_analysis_path = scoring_cfg.get(
            "input_analysis_path",
            analysis_cfg.get("output_analysis_path", "data/analysis_results.jsonl"),
        )
        input_correlation_path = scoring_cfg.get(
            "input_correlation_path",
            correlation_cfg.get("output_correlation_path", "data/correlation_results.jsonl"),
        )
        input_iocs_path = scoring_cfg.get(
            "input_iocs_path",
            ioc_cfg.get("output_iocs_path", "data/iocs.jsonl"),
        )
        output_scores_path = scoring_cfg.get("output_scores_path", "data/scores.jsonl")

        analyses = list(read_analysis_results(input_analysis_path))
        correlations = list(read_correlation_results(input_correlation_path))
        ioc_counts = count_iocs_by_event(input_iocs_path)

        manager = ScoringManager(config=self.config, logger=self.logger)
        scores = manager.score(analyses=analyses, correlations=correlations, iocs_by_event=ioc_counts)
        count = write_scores(scores, output_scores_path)
        self.logger.info("Scoring output saved path=%s count=%d", output_scores_path, count)

    def _run_storage(self) -> None:
        from cti.storage.manager import StorageManager

        manager = StorageManager(config=self.config, logger=self.logger)
        manager.store()

    def _run_reporting(self) -> None:
        from cti.reporting.manager import ReportingManager

        manager = ReportingManager(config=self.config, logger=self.logger)
        bundle = manager.generate()
        manager.write(bundle)

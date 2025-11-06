import loguru
from prefect import Flow, State, get_run_logger
from prefect.flow_runs import FlowRun


def capture_crash_info(flow: Flow, flow_run: FlowRun, state: State) -> State:
    if state.is_crashed():

        try:
            logger = get_run_logger()
        except Exception:
            # case where the flow is not yet initialized
            logger = loguru.logger

        logger.error("_--- Crash details ---_")
        logger.error(flow_run.model_dump(mode="json"))
        logger.error(state.model_dump(mode="json"))
        logger.error("_--- End crash details ---_")
    return state

try:
    from Src.core.prompt import PromptBuilder
except ModuleNotFoundError:
    from core.prompt import PromptBuilder

try:
    from .state import AgentState
except ImportError:
    from state import AgentState


class Agent:
    def __init__(self, llm, executor, prompt_builder=None, max_steps=5, logger_factory=None, skill_registry=None):
        self.llm = llm
        self.executor = executor
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.max_steps = max_steps
        self.logger_factory = logger_factory
        self.skill_registry = skill_registry
        self.last_state = None

    def prepare_state(self, user_input=None, context=None, state=None):
        state = state or AgentState(max_steps=self.max_steps)
        state.max_steps = self.max_steps

        if context:
            state.context.update(context)

        system_prompt = self.prompt_builder.build(
            context=state.context,
            tools=self.executor.schemas(),
            skills=self.skill_registry.entries() if self.skill_registry else []
        )
        state.set_system_prompt(system_prompt)

        if user_input is not None:
            state.add_user_message(user_input)

        return state

    def run(self, user_input, context=None, state=None, return_state=False):
        state = self.prepare_state(user_input=user_input, context=context, state=state)
        logger = self.logger_factory() if self.logger_factory else None
        system_prompt = state.messages[0]["content"] if state.messages and state.messages[0]["role"] == "system" else ""

        if logger:
            state.metadata["log_id"] = logger.log_id
            state.metadata["log_path"] = str(logger.log_path)
            logger.log_run_start(user_input, context=state.context)
            if system_prompt:
                logger.log_system_prompt(system_prompt)

        while state.step < state.max_steps:
            resp = self.llm.chat(state.messages, tools=self.executor.schemas())
            state.add_assistant_message(content=resp.content, tool_calls=resp.tool_calls)

            if logger:
                logger.log_llm_response(state.step, resp.content, resp.tool_calls)

            if not resp.tool_calls:
                state.mark_finished(resp.content or "", reason="completed")
                if logger:
                    logger.log_finish(state.stop_reason, state.final_output or "")
                self.last_state = state
                return state if return_state else state.final_output

            for call in resp.tool_calls:
                result = self.executor.execute(call)
                state.add_tool_result(
                    tool_name=result.tool_name,
                    content=result.content,
                    tool_call_id=result.tool_call_id,
                    success=result.success,
                    raw=result.raw
                )
                if logger:
                    logger.log_tool_result(
                        state.step,
                        tool_name=result.tool_name,
                        tool_call_id=result.tool_call_id,
                        success=result.success,
                        content=result.content
                    )

            state.step += 1

        state.mark_finished("max steps reached", reason="max_steps")
        if logger:
            logger.log_finish(state.stop_reason, state.final_output or "")
        self.last_state = state
        return state if return_state else state.final_output

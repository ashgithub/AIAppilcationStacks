import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dynamic_app.ui_agents_graph.ui_orchestrator_agent import UIOrchestrator
from dynamic_app.configs.common_struct import UIOrchestratorOutput, Skill


@pytest.fixture
def mock_gen_ai_provider():
    """Mock GenAIProvider to avoid real API calls."""
    mock_provider = MagicMock()
    mock_client = MagicMock()
    mock_provider.build_oci_client.return_value = mock_client
    return mock_provider


@pytest.fixture
def mock_create_agent():
    """Mock langchain create_agent function."""
    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock()
    return mock_agent


@pytest.fixture
def sample_state():
    """Sample state for testing agent calls."""
    return {
        "user_query": "Show me sales data as a bar chart",
        "data_summary": "Sales data includes revenue, units sold, and dates",
        "available_skills": [
            {
                "name": "bar_graph_skill",
                "description": "Create bar charts for data visualization",
                "content": "Detailed instructions for bar graph creation"
            },
            {
                "name": "timeline_skill",
                "description": "Create timeline visualizations",
                "content": "Detailed instructions for timeline creation"
            }
        ]
    }


class TestUIOrchestrator:
    """Test suite for UIOrchestrator agent."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_gen_ai_provider):
        """Test that UIOrchestrator initializes correctly."""
        with patch('dynamic_app.ui_agents_graph.ui_orchestrator_agent.GenAIProvider',
                   return_value=mock_gen_ai_provider):
            orchestrator = UIOrchestrator()

            assert orchestrator.gen_ai_provider == mock_gen_ai_provider
            assert orchestrator.agent_name == "ui_orchestrator"
            assert orchestrator.system_prompt == UIOrchestrator.AGENT_INSTRUCTIONS
            assert orchestrator.agent is None

            # Check that client is built with correct parameters
            mock_gen_ai_provider.build_oci_client.assert_called_once_with(
                model_kwargs={"temperature": 0.7}
            )

    @pytest.mark.asyncio
    async def test_initialize_builds_agent(self, mock_gen_ai_provider, mock_create_agent):
        """Test that initialize() builds the agent successfully."""
        with patch('dynamic_app.ui_agents_graph.ui_orchestrator_agent.GenAIProvider',
                   return_value=mock_gen_ai_provider), \
             patch('dynamic_app.ui_agents_graph.ui_orchestrator_agent.create_agent',
                   return_value=mock_create_agent) as mock_create_agent_func:

            orchestrator = UIOrchestrator()
            await orchestrator.initialize()

            # Check that agent was created
            assert orchestrator.agent == mock_create_agent

            # Check create_agent was called with correct parameters
            mock_create_agent_func.assert_called_once()
            call_args = mock_create_agent_func.call_args
            assert call_args[1]['model'] == mock_gen_ai_provider.build_oci_client.return_value
            assert call_args[1]['system_prompt'] == orchestrator.system_prompt
            assert 'middleware' in call_args[1]
            assert call_args[1]['response_format'] == UIOrchestratorOutput
            # Note: agent_name is not defined in the class, this might be a bug

    @pytest.mark.asyncio
    async def test_call_invokes_agent(self, mock_gen_ai_provider, mock_create_agent, sample_state):
        """Test that __call__ invokes the agent with the state."""
        expected_output = UIOrchestratorOutput(
            widgets=[
                Skill(name="bar_graph_skill", description="Create bar charts", content="...")
            ]
        )
        mock_create_agent.ainvoke.return_value = expected_output

        with patch('dynamic_app.ui_agents_graph.ui_orchestrator_agent.GenAIProvider',
                   return_value=mock_gen_ai_provider), \
             patch('dynamic_app.ui_agents_graph.ui_orchestrator_agent.create_agent',
                   return_value=mock_create_agent):

            orchestrator = UIOrchestrator()
            await orchestrator.initialize()

            result = await orchestrator(sample_state)

            # Check that agent was invoked with the state
            mock_create_agent.ainvoke.assert_called_once_with(sample_state)

            # Check that result is returned correctly
            assert result == expected_output

    @pytest.mark.asyncio
    async def test_server_deploy_simulation(self, mock_gen_ai_provider, mock_create_agent, sample_state):
        """Integration test simulating server deployment scenario.

        This test simulates what happens when the server is deployed and
        the UIOrchestrator is initialized and processes a request.
        """
        # Setup expected response
        expected_output = UIOrchestratorOutput(
            widgets=[
                Skill(name="bar_graph_skill",
                      description="Create bar charts for data visualization",
                      content="Detailed instructions for bar graph creation"),
                Skill(name="timeline_skill",
                      description="Create timeline visualizations",
                      content="Detailed instructions for timeline creation")
            ]
        )
        mock_create_agent.ainvoke.return_value = expected_output

        with patch('dynamic_app.ui_agents_graph.ui_orchestrator_agent.GenAIProvider',
                   return_value=mock_gen_ai_provider), \
             patch('dynamic_app.ui_agents_graph.ui_orchestrator_agent.create_agent',
                   return_value=mock_create_agent):

            # Simulate server startup - initialize orchestrator
            orchestrator = UIOrchestrator()
            await orchestrator.initialize()

            # Simulate incoming request
            result = await orchestrator(sample_state)

            print(result)

            # Verify the orchestrator processed the request correctly
            assert isinstance(result, UIOrchestratorOutput)
            assert result.widgets[0]["name"] == "bar_graph_skill"
            assert result.widgets[1]['name'] == "timeline_skill"

            # Verify agent interactions
            mock_create_agent.ainvoke.assert_called_once_with(sample_state)

    @pytest.mark.asyncio
    async def test_agent_not_initialized_error(self, mock_gen_ai_provider, sample_state):
        """Test that calling agent before initialization raises appropriate error."""
        with patch('dynamic_app.ui_agents_graph.ui_orchestrator_agent.GenAIProvider',
                   return_value=mock_gen_ai_provider):

            orchestrator = UIOrchestrator()

            # Should raise AttributeError since agent is None
            with pytest.raises(AttributeError):
                await orchestrator(sample_state)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__])
"""
crew.py — CrewAI crew definitions for the Citizen's Charter Assistant.

Five crews:

  MatcherCrew             (fast / cheap)
    matcher_agent uses TransactionSearchTool to identify 2–5 candidate
    transactions that match the citizen's plain-language description.
    Returns a JSON array so the UI can show a confirmation step.

  CharterCrew             (thorough / accurate)
    requirements_agent uses TransactionDetailTool to retrieve the full
    charter text for one confirmed transaction and formats a citizen-
    friendly requirements summary.

  LetterDraftingCrew      (formal writing)
    letter_drafting_agent composes a print-ready formal letter request
    addressed to the Bureau of Immigration Commissioner, using the
    applicant's personal details and the chosen transaction as context.

  VisaInfoCrew            (visa deep-dive)
    visa_info_agent uses TransactionSearchTool to find all relevant BI
    transactions for a given visa type, then produces a comprehensive
    guide covering validity, maintenance requirements, and common pitfalls.

  VisaRecommendationCrew  (personalised visa advice)
    visa_rec_agent takes the user's nationality, purpose, duration, and
    circumstances, recommends the most suitable Philippine visa type, and
    lists the relevant BI transactions they will need.

Environment variables
---------------------
  MATCHER_MODEL      LiteLLM model string for MatcherCrew
                     Default: anthropic/claude-haiku-4-5-20251001
  REQUIREMENTS_MODEL LiteLLM model string for CharterCrew
                     Default: anthropic/claude-opus-4-5
  LETTER_MODEL       LiteLLM model string for LetterDraftingCrew
                     Default: same as REQUIREMENTS_MODEL
  VISA_MODEL         LiteLLM model string for VisaInfoCrew and
                     VisaRecommendationCrew
                     Default: same as REQUIREMENTS_MODEL
  ANTHROPIC_API_KEY  Required for all crews
"""

import os

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from crewai_tools import ScrapeWebsiteTool

from tools.index_tool import TransactionDetailTool, TransactionSearchTool

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
try:
    if "MATCHER_MODEL" in st.secrets:
        os.environ["MATCHER_MODEL"] = st.secrets["MATCHER_MODEL"]
    if "REQUIREMENTS_MODEL" in st.secrets:
        os.environ["REQUIREMENTS_MODEL"] = st.secrets["REQUIREMENTS_MODEL"]
    if "LETTER_MODEL" in st.secrets:
        os.environ["LETTER_MODEL"] = st.secrets["LETTER_MODEL"]
    if "VISA_MODEL" in st.secrets:
        os.environ["VISA_MODEL"] = st.secrets["VISA_MODEL"]
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    pass

DEFAULT_MATCHER_MODEL      = "anthropic/claude-haiku-4-5-20251001"
DEFAULT_REQUIREMENTS_MODEL = "anthropic/claude-opus-4-5"
DEFAULT_LETTER_MODEL       = DEFAULT_REQUIREMENTS_MODEL
DEFAULT_VISA_MODEL         = DEFAULT_REQUIREMENTS_MODEL


# ── MatcherCrew ───────────────────────────────────────────────────────────────

@CrewBase
class MatcherCrew:
    """Identifies 2–5 candidate transactions from a plain-language query."""

    agents_config = "config/matcher_agents.yaml"
    tasks_config  = "config/matcher_tasks.yaml"

    @agent
    def matcher_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["matcher_agent"],
            tools=[TransactionSearchTool()],
            llm=LLM(
                model=os.environ['MATCHER_MODEL'],
                api_key=os.environ["ANTHROPIC_API_KEY"],
                #model=os.getenv("MATCHER_MODEL", DEFAULT_MATCHER_MODEL),
                #api_key=os.getenv("ANTHROPIC_API_KEY"),
            ),
            verbose=False,
        )

    @task
    def match_transactions_task(self) -> Task:
        return Task(config=self.tasks_config["match_transactions_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )


# ── CharterCrew ───────────────────────────────────────────────────────────────

@CrewBase
class CharterCrew:
    """Citizens Charter crew — handles transaction requirements queries."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ── Agents ────────────────────────────────────────────────────────────────

    @agent
    def requirements_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["requirements_agent"],
            tools=[TransactionDetailTool()],
            llm=LLM(
                model=os.environ["REQUIREMENTS_MODEL"], 
                api_key=os.environ["ANTHROPIC_API_KEY"]

                #model=os.getenv("REQUIREMENTS_MODEL", DEFAULT_REQUIREMENTS_MODEL),
                #api_key=os.getenv("ANTHROPIC_API_KEY"),
            ),
            verbose=False,
        )

    # ── Tasks ─────────────────────────────────────────────────────────────────

    @task
    def get_requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config["get_requirements_task"],
        )

    # ── Crew ──────────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )


# ── LetterDraftingCrew ────────────────────────────────────────────────────────

@CrewBase
class LetterDraftingCrew:
    """Drafts a formal letter request to the BI Commissioner."""

    agents_config = "config/letter_agents.yaml"
    tasks_config  = "config/letter_tasks.yaml"

    @agent
    def letter_drafting_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["letter_drafting_agent"],
            tools=[ScrapeWebsiteTool()],
            llm=LLM(
                model=os.environ["LETTER_MODEL"],
                api_key=os.environ["ANTHROPIC_API_KEY"],
                #model=os.getenv(
                #    "LETTER_MODEL",
                #    os.getenv("REQUIREMENTS_MODEL", DEFAULT_LETTER_MODEL),
                #),
                #api_key=os.getenv("ANTHROPIC_API_KEY"),                
            ),
            verbose=False,
        )

    @task
    def draft_letter_task(self) -> Task:
        return Task(config=self.tasks_config["draft_letter_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )


# ── VisaInfoCrew ──────────────────────────────────────────────────────────────

@CrewBase
class VisaInfoCrew:
    """Deep-dive guide for a specific Philippine visa type."""

    agents_config = "config/visa_info_agents.yaml"
    tasks_config  = "config/visa_info_tasks.yaml"

    @agent
    def visa_info_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["visa_info_agent"],
            tools=[TransactionSearchTool()],
            llm=LLM(
                #model=os.getenv(
                #    "VISA_MODEL",
                #    os.getenv("REQUIREMENTS_MODEL", DEFAULT_VISA_MODEL),
                #),
                #api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.environ["VISA_MODEL"],
                api_key=os.environ["ANTHROPIC_API_KEY"],

            ),
            verbose=False,
        )

    @task
    def visa_info_task(self) -> Task:
        return Task(config=self.tasks_config["visa_info_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )


# ── VisaRecommendationCrew ────────────────────────────────────────────────────

@CrewBase
class VisaRecommendationCrew:
    """Recommends the right Philippine visa based on the user's situation."""

    agents_config = "config/visa_rec_agents.yaml"
    tasks_config  = "config/visa_rec_tasks.yaml"

    @agent
    def visa_rec_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["visa_rec_agent"],
            tools=[TransactionSearchTool()],
            llm=LLM(
                #model=os.getenv(
                #    "VISA_MODEL",
                #    os.getenv("REQUIREMENTS_MODEL", DEFAULT_VISA_MODEL),
                #),
                #api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.environ["VISA_MODEL"],
                api_key=os.environ["ANTHROPIC_API_KEY"],
            ),
            verbose=False,
        )

    @task
    def visa_rec_task(self) -> Task:
        return Task(config=self.tasks_config["visa_rec_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )

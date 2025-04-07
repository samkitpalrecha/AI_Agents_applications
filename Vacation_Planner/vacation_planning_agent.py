from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

# Load the LLaMA model
# llama_model = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"))

# Initialize the OpenAI model
llama_model = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.6,
    model_name="gpt-4"
)

from langchain.tools import tool
from crewai_tools import SeleniumScrapingTool
from crewai_tools import SerperDevTool

search_tool = SerperDevTool(n_results=3)
scraping_tool = SeleniumScrapingTool()

from langchain.tools import tool

class CalculatorTools():

    @tool("Make a calculation")
    def calculate(operation):
        """Useful to perform any mathematical calculations,
        like sumation, subtraction, multiplication, division, etc.
        The input to this tool should be a mathematical
        expression, a couple examples are `200*7` or `5000/2*10`
        """
        try:
            return eval(operation)
        except SyntaxError:
            return "Error: Invalid syntax in mathematical expression"

from crewai import Agent

class TripAgents():

    def city_selection_agent(self):
        return Agent(
            role='Global Destination Strategist',
            goal='Analyze destination options based on weather, seasonal activities, and budget constraints to provide tailored city recommendations for a perfect trip.',
            backstory="""A travel strategist with extensive experience in curating city recommendations.
                         Uses real-time data on weather conditions, cultural events, and cost factors
                         to provide data-driven, personalized travel advice for an unforgettable experience.""",
            tools=[
                search_tool,
                scraping_tool,
            ],
            verbose=True,
            llm=llama_model,
            allow_delegation=False,
            max_iter=2
        )

    def local_expert(self):
        return Agent(
            role='City Insider and Cultural Guide',
            goal='Provide enriching insights into the culture, hidden gems, and practical tips of the selected city.',
            backstory="""A passionate local specialist who has explored every corner of the city,
            offering unparalleled knowledge about its culture, cuisine, and unique attractions.
            Your expertise ensures visitors enjoy authentic experiences and uncover the city's true spirit.""",
            tools=[
                search_tool,
                scraping_tool,
            ],
            verbose=True,
            llm=llama_model,
            allow_delegation=False,
            max_iter=2
        )

    def travel_concierge(self):
        return Agent(
            role='Personalized Travel Planner Extraordinaire',
            goal="""Craft seamless and unforgettable travel itineraries with detailed budgets,
            packing suggestions, and tailored activity plans.""",
            backstory="""A highly-regarded travel planner trusted for blending luxury, efficiency,
            and practicality. With years of experience, you ensure stress-free travel planning
            tailored to each traveler's unique preferences and constraints.""",
            tools=[
                search_tool,
                scraping_tool,
                CalculatorTools.calculate,
            ],
            verbose=True,
            llm=llama_model,
            allow_delegation=False,
            max_iter=2
        )

from datetime import date
from crewai import Task
from textwrap import dedent

class TripTasks:
    def identify_task(self, agent, origin, city, budget, num_days, start_date):
        return Task(
            description=dedent(f"""
                Collect and analyze essential information for the destination city - {city} for the upcoming trip:
                1. **Weather**: Provide a forecast and highlight any significant weather patterns during the trip, specifically around the starting date of {start_date}.
                2. **Seasonal Events**: Identify key festivals, holidays, or cultural events happening during the travel period.
                3. **Costs**: Estimate flight, accommodation, and daily expenses within the provided budget, considering local price variations.

                Summarize the city's appeal based on these factors and explain why it is a great choice for this trip. Ensure to cover:
                - A snapshot of the weather and major events during the trip.
                - A realistic budget breakdown for flights and accommodation.
                - Top attractions or unique experiences to highlight.

                **Trip Information**:
                - Departure: {origin}
                - Destination: {city}
                - Duration: {num_days} days
                - Budget: Rs. {budget}

                Structure the response with clear headings for weather, events, costs, and attractions for easy readability.
            """),
            agent=agent,
            expected_output="Concise, well-organized report with headings for weather, costs, and key activities, staying within token limits."
        )

    def gather_task(self, agent, origin, city, budget, num_days):
        return Task(
            description=dedent(f"""
                Create an in-depth travel guide for {city}, focusing on:
                - Must-See Attractions: Include major landmarks and unique spots.
                - Local Culture: Highlight customs, food, or traditions.
                - Hidden Gems: At least one or two less-known but fascinating spot.
                - Practical Information: Weather forecast, high-level costs, and travel tips.

                Organize the guide into clear sections with a concise yet informative style.

                **Details**:
                - Trip Duration: {num_days} days
                - Budget: Rs. {budget}
                - Destination: {city}

                The output should feel like a professional travel blog entry.
            """),
            agent=agent,
            expected_output="Comprehensive travel guide with clear sections for attractions, culture, and practical information."
        )

    def plan_task(self, agent, origin, city, budget, num_days):
        return Task(
            description=dedent(f"""
                Develop a detailed travel itinerary for a {num_days}-day trip to {city}.
                The plan should include:
                - Daily Activities: Morning, afternoon, and evening plans.
                - Dining Options: Recommend places to eat each day.
                - Accommodation: Include specific suggestions.
                - Packing List: Tailored to weather conditions and planned activities.
                - Budget Breakdown: Approximate costs per day. Try to be precise.

                **Details**:
                - Starting Location: {origin}
                - Destination: {city}
                - Budget: ${budget}

                Format the itinerary with clear day-by-day entries, making it easy to follow.
            """),
            agent=agent,
            expected_output="Detailed daily itinerary including activities, dining, accommodation, and costs."
        )

    def __tip_section(self):
        return "If you do your BEST WORK, I'll tip you $100!"

from crewai import Crew, Process

class TripCrew:

  def __init__(self, origin, city, num_days, budget, start_date):
    self.city = city
    self.origin = origin
    self.budget = budget
    self.num_days = num_days
    self.start_date = start_date

  def run(self):
    agents = TripAgents()
    tasks = TripTasks()

    city_selector_agent = agents.city_selection_agent()
    local_expert_agent = agents.local_expert()
    travel_concierge_agent = agents.travel_concierge()

    identify_task = tasks.identify_task(
      city_selector_agent,
      self.origin,
      self.city,
      self.budget,
      self.num_days,
      self.start_date
    )
    gather_task = tasks.gather_task(
      local_expert_agent,
      self.origin,
      self.city,
      self.budget,
      self.num_days
    )
    plan_task = tasks.plan_task(
      travel_concierge_agent,
      self.origin,
      self.city,
      self.budget,
      self.num_days
    )

    crew = Crew(
      agents=[
        city_selector_agent, local_expert_agent, travel_concierge_agent
      ],
      tasks=[identify_task, gather_task, plan_task],
      Process=Process.sequential,
      verbose=True,
      memory=True
    )

    result = crew.kickoff()
    return result

if __name__ == "__main__":
  print("## Welcome to Trip Planner Crew")
  print('-------------------------------')
  origin = input(
    dedent("""
      From where will you be traveling from?
    """))
  city = input(
    dedent("""
      What city you are interested in visiting/travelling?
    """))
  start_date = input(
    dedent("""
        What is the start date of your trip
    """))
  num_days = input(
    dedent("""
      Number of days you are interested in traveling?
    """))
  Budget = input(
    dedent("""
      What is the budget of your trip?
    """))

  trip_crew = TripCrew(origin, city, num_days, Budget, start_date)
  result = trip_crew.run()
  print("\n\n########################")
  print("## Here is you Trip Plan")
  print("########################\n")
  print(result)
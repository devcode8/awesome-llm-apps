## AI Job Search Agent

An AI-powered job search agent built using the **uAgents** framework and **[ASI1 LLM](https://asi1.ai/)** with real-time web search capabilities. This agent helps users find relevant, currently active job listings from major job boards through natural language queries, with session-based conversation memory for context-aware follow-up searches.

### Features

- **Real-Time Job Search**: Searches major job boards (LinkedIn, Indeed, Naukri, Glassdoor, company career pages) for active listings using ASI1's web search
- **Context-Aware Conversations**: Maintains session history (RAG) so users can ask follow-up questions like "show me similar jobs but remote" or "same skills but in Bangalore"
- **Smart Query Classification**: Automatically detects query intent — new search, refinement (remote, location, salary, experience), or context analysis of previous results
- **Context Analysis**: Answer questions about previously fetched results without making new searches (e.g., "shortlist top 3", "what skills are mentioned across these jobs")
- **Structured Output**: Returns formatted job listings with title, company, location, experience, skills, salary, and apply links
- **Chat Protocol**: Uses the standard uAgents chat protocol, making it compatible with Agentverse and other uAgents-based systems

### Project Structure

```
ai_job_search_agent/
├── agent.py        # Agent setup, funding, startup event, and entry point
├── protocol.py     # Chat protocol, message handlers, job search logic, session management, and query classification
├── requirements.txt
└── README.md
```

### How to Get Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/starter_ai_agents/ai_job_search_agent
   ```

2. **Install the required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   - Get your ASI1 API key from [ASI1](https://asi1.ai)
   - Create a `.env` file and set `ASI1_API_KEY=your_key_here`

4. **Run the agent**
   ```bash
   python agent.py
   ```

5. **Open the Agent Inspector**

   After running the agent, you should see something similar in your terminal output:

   ```
   INFO:     [Alice]: Starting agent with address: agent1qw8jn3nfl2fyyhe7v4x8pfmsge4hs9zqrqw9eq7h7hluzmd0da8z7j0uacx
   INFO:     [Alice]: Agent inspector available at https://Agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000&address=agent1q0nrj45ah0e53424n9uqc83d9xxs6534jug7j6ka4z6wnrsx7ex2kwx86t4
   INFO:     [Alice]: Starting server on http://0.0.0.0:8002 (Press CTRL+C to quit)
   INFO:     [Alice]: Starting mailbox client for https://Agentverse.ai
   INFO:     [Alice]: Mailbox access token acquired
   INFO:     [Alice]: Registration on Almanac API successful
   INFO:     [Alice]: Registering on almanac contract...
   INFO:     [Alice]: Registering on almanac contract...complete
   ```

   Click the **Agent Inspector URL** from the terminal output to open the Inspector UI in your browser.

6. **Publish your agent on Agentverse (Optional)**

   To publish your agent on the Agentverse, add the `publish=True` parameter and a `README.md` path while defining the agent:

   ```python
   # Now your agent is ready to join the Agentverse!
   agent = Agent(
       name="alice",
       port=8000,
       mailbox=True,
       publish_agent_details=True,
       readme_path="README.md"
   )
   ```

   This will publish the agent details (like name) on the Agentverse.

   > **Warning: Local Network Access Permission (Chrome Update)**
   >
   > Recent Chrome (v142+) and Brave updates introduced a Local Network Access permission prompt. If this permission is not granted, the browser cannot detect locally running agents.
   >
   > **Solution:** When prompted with "Allow this site to access devices on your local network", click **Allow**. If you missed the prompt, you can manually enable it in: Chrome Settings → Privacy and Security → Site Settings → Additional permissions → Local network access.
   >
   > Reference: [Chrome For Developers Blog – Local Network Access Update](https://developer.chrome.com/blog/local-network-access-update)

7. **Create a Mailbox in Agentverse**

   Now that your local Agent is running, you can connect it to Agentverse via a Mailbox:

   1. Make sure your Agent is running
   2. Click on the **Local Agent Inspector URL** provided in your terminal output — you will be redirected to the Inspector UI where you can see details about this local Agent
   3. Click the **Connect** button

      ![Mailbox Connect](https://innovationlab.fetch.ai/resources/assets/images/mailbox-connect-1de25d2539f6f386fe2b17fb777ee8cb.png)

   4. You will be presented with 3 choices: **Mailbox**, **Proxy**, and **Custom** — select **Mailbox**

      ![Mailbox Options](https://innovationlab.fetch.ai/resources/img/uagents/mailbox-options.png)

      ![Mailbox Done](https://innovationlab.fetch.ai/resources/img/uagents/mailbox-done.png)

   5. You will see some code details for the Agent — you do not need to do anything, just click **Finish**

### View your Agent on Agentverse

Once you connect your Agent via Mailbox, click on **Agent Profile** and navigate to the **Overview** section of the Agent. Your Agent will appear under local agents on Agentverse.

![Agent Profile](https://innovationlab.fetch.ai/resources/assets/images/agent-profile-ad2d027033e8cf9d7f1e75c0728f480f.png)

### Chat with your Agent on ASI1 UI

Click the **Chat with Agent** button to start chatting with your agent on the ASI1 UI.

![Chat with Agent](https://res.cloudinary.com/doesqlfyi/image/upload/v1770976139/jobImage_mojlwh.png)

![ASI1 UI](https://res.cloudinary.com/doesqlfyi/image/upload/v1770976138/jobasi1UI_k99nmt.png)

### Usage

Once the agent is running, it registers on the uAgents network and can be interacted with via the chat protocol. You can connect to it through Agentverse or any compatible uAgents client.

**Example queries:**
- "Backend developer jobs in India using Python and FastAPI"
- "Remote React developer positions posted this week"
- "Data Science jobs with 2+ years experience"

**Follow-up queries:**
- "Show me more" — finds additional jobs matching previous criteria
- "Same but remote" — adds remote filter to previous search
- "Shortlist the top 3" — analyzes previous results without a new search


### Sample Chat

![Sample Chat](https://res.cloudinary.com/doesqlfyi/image/upload/v1770977622/Screenshot_2026-02-13_at_3.43.11_PM_ppzoss.png)

![Sample Chat](https://res.cloudinary.com/doesqlfyi/image/upload/v1770977623/Screenshot_2026-02-13_at_3.43.38_PM_aigjqv.png)


## AI Adaptive Tutor Agent

An AI-powered adaptive tutoring agent built using the **uAgents** framework and **ASI1 LLM**. This agent helps learners achieve mastery through personalized learning plans, interactive teaching, adaptive quizzes, and continuous performance-based adjustments. It enables natural language learning experiences with session-based memory for context-aware follow-up interactions.

### Features

- **Personalized Learning Plans**: Creates structured, time-bound roadmaps tailored to learner goals, deadlines, and pace  
- **Context-Aware Conversations**: Maintains session history so learners can continue learning seamlessly across sessions  
- **Multi-Agent Workflow**: Uses specialized agents for research, planning, teaching, assessment, and adaptation  
- **Adaptive Teaching**: Adjusts difficulty and content based on learner performance and knowledge gaps  
- **Interactive Learning**: Explains concepts step by step with examples and real-world applications  
- **Smart Assessment**: Generates adaptive quizzes with multiple question types  
- **Performance Tracking**: Identifies weak areas and provides detailed feedback  
- **Persistent Memory**: Stores progress, learner profile, and roadmap for long-term learning  
- **Structured Output**: Returns organized learning plans, quizzes, and feedback  
- **Chat Protocol**: Uses the standard uAgents chat protocol, making it compatible with Agentverse and other uAgents-based systems  

### Project Structure

```bash
adaptive_tutor_agent/
├── agent.py
├── protocol.py
├── tutor_agent/
│   ├── orchestrator.py
│   ├── research.py
│   ├── planner.py
│   ├── explainer.py
│   ├── quiz.py
│   ├── evaluator.py
│   ├── adaptive.py
│   ├── chat.py
│   ├── context.py
│   ├── store.py
│   ├── common_tools.py
│   └── asi1.py
├── requirements.txt
└── README.md
```

### How to Get Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/adaptive_tutor_agent.git
   cd adaptive_tutor_agent
   ```

2.	**Install the required dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.	**Configure API Key**
	- Get your ASI1 or LLM provider API key
	- Create a .env file and set:
        ```bash
        ASI1_API_KEY=your_asi1_api_key_here
        ASI1_BASE_URL=https://api.asi1.ai/v1
        ASI1_MODEL=asi1
        ```

4.	**Run the agent**

    ```bash
    python agent.py
    ```


5.	**Open the Agent Inspector**
    After running the agent, you should see something similar in your terminal output:

    ```bash
    INFO:     [Tutor]: Starting agent with address: agent1...
    INFO:     [Tutor]: Agent inspector available at https://Agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000
    INFO:     [Tutor]: Starting server on http://0.0.0.0:8002
    ```

    Click the **Agent Inspector URL** from the terminal output to open the Inspector UI in your browser.

6.	**Publish your agent on Agentverse (Optional)**
    To publish your agent on the Agentverse, add the `publish=True` parameter and a `README.md` path while defining the agent:

    ```python
    agent = Agent(
        name="adaptive-tutor",
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

7.	**Create a Mailbox in Agentverse**

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

## Chat with your Agent on ASI1 UI

Click the **Chat with Agent** button to start interacting.

![Chat with Agent](https://res.cloudinary.com/doesqlfyi/image/upload/v1771257538/image_copy_rtl3nm.png)

![ASI1 UI](https://res.cloudinary.com/doesqlfyi/image/upload/v1771257538/image_copy_3_wrvucn.png)

### Usage

Once the agent is running, it registers on the uAgents network and can be interacted with via the chat protocol.

**Example queries**:
- “I want to prepare for the AWS Solutions Architect exam in 3 months.”
- “Teach me about binary search trees.”
- “Give me a quiz on recursion.”
- “I am struggling with dynamic programming. Can you help?”

**Follow-up queries**:
- “Show my weak areas.”
- “Revise last week’s topics.”
- “Increase difficulty.”
- “Focus more on problem solving.”

### Sample Chat

![Sample Chat](https://res.cloudinary.com/doesqlfyi/image/upload/v1771257539/image_copy_5_lxm8cu.png)
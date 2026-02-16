## AI Contract Risk Scanner

An AI-powered contract analysis agent built using the **uAgents** framework and **ASI1 LLM**. This agent helps users understand legal agreements, terms of service, and privacy policies by breaking them into clauses, flagging risks, and delivering clear, actionable reports. It enables natural language interactions with session-based memory for context-aware follow-up questions.

### Features

- **Comprehensive Contract Analysis**: Analyzes contracts, terms of service, privacy policies, and legal agreements  
- **Multi-Source Fetching**: Automatically discovers and merges linked legal pages (privacy, refund, DPA, etc.)  
- **Context-Aware Conversations**: Maintains session history for seamless follow-up questions  
- **Intelligent Tool Workflow**: Uses specialized tools for fetching, validating, extracting, and reporting  
- **Clause Extraction**: Identifies and summarizes the most important clauses with risk levels  
- **Risk Scoring**: Assigns 🟢 low, 🟡 medium, or 🔴 high risk levels to each clause  
- **Smart Pre-Check**: Validates legal content before full analysis  
- **Adaptive Reports**: Default concise reports or detailed analysis on request  
- **Key Risk Flagging**: Highlights financial, arbitration, data, auto-renewal, and termination clauses  
- **Persistent Memory**: Caches analyses for instant retrieval of previously analyzed contracts  
- **Structured Output**: Returns professional, scannable risk reports in Markdown  
- **Chat Protocol**: Uses the standard uAgents chat protocol, making it compatible with Agentverse and other uAgents-based systems  

### Project Structure

```bash
contract_risk_scanner/
├── agent.py
├── protocol.py
├── asi1.py
├── context.md
├── requirements.txt
├── pyproject.toml
└── README.md
```

### How to Get Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/contract_risk_scanner.git
   cd contract_risk_scanner
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
    INFO:     [contract_risk_scanner_agent]: Starting agent with address: agent1...
    INFO:     [contract_risk_scanner_agent]: Agent inspector available at https://Agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000
    INFO:     [contract_risk_scanner_agent]: Starting server on http://0.0.0.0:8000
    ```

    Click the **Agent Inspector URL** from the terminal output to open the Inspector UI in your browser.

6.	**Publish your agent on Agentverse (Optional)**
    To publish your agent on the Agentverse, add the `publish=True` parameter and a `README.md` path while defining the agent:

    ```python
    agent = Agent(
        name="contract-risk-scanner",
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

![Chat with Agent](https://res.cloudinary.com/doesqlfyi/image/upload/v1771257538/image_iyxo4k.png)

![ASI1 UI](https://res.cloudinary.com/doesqlfyi/image/upload/v1771257538/image_copy_2_zp8iwn.png)

### Usage

Once the agent is running, it registers on the uAgents network and can be interacted with via the chat protocol.

**Example queries**:
- "Check this URL: https://example.com/terms"
- "Analyze this privacy policy: [paste text]"
- "What are the riskiest clauses in this contract?"
- "Is there an arbitration clause?"
- "What's the overall risk level of this agreement?"

**Follow-up queries**:
- "Which clause is riskiest?"
- "Summarize the report in 5 bullets."
- "What does the arbitration clause mean?"
- "Give me the detailed report."
- "Is this safe to sign?"

### Sample Chat

![Sample Chat](https://res.cloudinary.com/doesqlfyi/image/upload/v1771257539/image_copy_4_cgreng.png)
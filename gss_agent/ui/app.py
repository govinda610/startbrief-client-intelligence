import gradio as gr
import os
import json
from gss_agent.core.agents import get_nexus_agent
import time
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import plotly.graph_objects as go

# Custom Nexus Theme Class
class NexusTheme(gr.themes.Base):
    def __init__(self):
        super().__init__(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
            spacing_size="sm",
            radius_size="lg",
            text_size="lg",
        )
        super().set(
            body_background_fill="#0A192F",
            body_text_color="#E0E6ED",
            background_fill_primary="#112240",
            background_fill_secondary="#0A192F",
            border_color_primary="#1E3A8A", # Nexus accents
            border_color_accent="#002856",
            color_accent_soft="#1E3A8A",
            block_background_fill="#112240",
            block_border_width="1px",
            block_label_background_fill="#0A192F",
            input_background_fill="#1E3A8A",
            button_primary_background_fill="linear-gradient(90deg, #007bff, #00d4ff)",
            button_primary_text_color="#FFFFFF",
        )

# Load client names
dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(os.path.dirname(dir_path), "data/clients.json")

with open(data_path, "r") as f:
    clients_data = json.load(f)
    CLIENT_NAMES = [c["name"] for c in clients_data]

agent = get_nexus_agent()

def create_metrics_plot():
    # Create 3 indicators: Relevancy, Risk, Utilization
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode = "gauge+number",
        value = 92,
        title = {'text': "Churn Risk Mitigated", 'font': {'size': 14, 'color': '#A0AEC0'}},
        domain = {'x': [0, 0.3], 'y': [0, 1]},
        gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#00D4FF"}}
    ))

    fig.add_trace(go.Indicator(
        mode = "number+delta",
        value = 98,
        delta = {'reference': 90},
        title = {'text': "Strategic Relevancy", 'font': {'size': 14, 'color': '#A0AEC0'}},
        domain = {'x': [0.35, 0.65], 'y': [0, 1]},
        number = {'suffix': "%"}
    ))

    fig.add_trace(go.Indicator(
        mode = "gauge+number",
        value = 85,
        title = {'text': "Content Utilization", 'font': {'size': 14, 'color': '#A0AEC0'}},
        domain = {'x': [0.7, 1], 'y': [0, 1]},
        gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#007BFF"}}
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "white"},
        height=200,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig

def predict(message, history, client_name):
    thread_id = f"demo-{client_name}-{int(time.time())}"
    full_query = f"Target Client: {client_name}\nRequest: {message}\n\nPlease generate a strategic brief and ask the Critic for approval."
    
    traces = []
    current_response = ""
    
    def format_traces(t_list):
        if not t_list: return ""
        # Adding glassmorphism style to details
        return f"""<details style='background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 10px; margin-bottom: 10px; color: #E2E8F0;'>
        <summary style='cursor: pointer; font-weight: 600; color: #60A5FA;'>🕵️ Agent Reasoning & Tool Traces</summary>
        <div style='margin-top: 10px; white-space: pre-wrap;'>{'<br><br>'.join(t_list)}</div>
        </details><hr style='border-color: rgba(255,255,255,0.1); margin: 20px 0;'>"""

    try:
        config = {"configurable": {"thread_id": thread_id}}
        
        # Stream updates from the agent
        for event in agent.stream(
            {"messages": [HumanMessage(content=full_query)]}, 
            config=config,
            stream_mode="updates"
        ):
            if isinstance(event, dict):
                for node_name, output in event.items():
                    # Handle cases where output is None
                    if output is None:
                        continue
                        
                    if "messages" in output:
                        raw_msgs = output["messages"]
                        
                        # Handle LangGraph Overwrite object if present
                        if hasattr(raw_msgs, "value"):
                            messages = raw_msgs.value
                        else:
                            messages = raw_msgs
                            
                        # Ensure we get the last message
                        msg = messages[-1] if isinstance(messages, list) and len(messages) > 0 else None
                        if not msg: continue

                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tc in msg.tool_calls:
                                    if tc['name'] == 'task':
                                        sub_type = tc['args'].get('subagent_type', 'unknown')
                                        desc = tc['args'].get('description', '')[:60] + "..."
                                        traces.append(f"👨‍💻 **Supervisor** -> Delegating to **{sub_type}**: *{desc}*")
                                    else:
                                        traces.append(f"🛠️ **Tool Call**: `{tc['name']}`")
                            elif msg.content:
                                if node_name == "Supervisor":
                                    current_response = msg.content
                                elif node_name == "Critic":
                                    traces.append(f"🧐 **Critic**: {msg.content}")
                                else:
                                    traces.append(f"💡 **{node_name} Agent**: {msg.content[:100]}...")
            
            yield format_traces(traces) + current_response

    except Exception as e:
        yield f"⚠️ **An error occurred**: {str(e)}"

# CSS for Glassmorphism
custom_css = """
.gradio-container { background-color: #0A192F !important; }
.brief-panel { 
    background: rgba(17, 34, 64, 0.7); 
    backdrop-filter: blur(12px); 
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1); 
    border-radius: 16px; 
    padding: 20px; 
}
h1, h2, h3, h4, p { color: #E2E8F0 !important; }
hr { border-color: rgba(255, 255, 255, 0.1); }
.message-wrap { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(5px); border-radius: 12px; }
"""

with gr.Blocks(theme=NexusTheme(), css=custom_css, title="Nexus Strategic Advisor") as demo:
    gr.HTML("""
    <div style='text-align: center; padding: 20px; margin-bottom: 20px;'>
        <h1 style='color: white; font-size: 2.5rem; font-weight: 700; margin: 0;'>💎 Nexus Strategic Advisor</h1>
        <p style='color: #94A3B8; font-size: 1.1rem;'>AI-Powered Sales Readiness & Value Realization</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=9):
            client_selector = gr.Dropdown(
                choices=CLIENT_NAMES, 
                label="",
                info="Select a client to begin analysis",
                value=CLIENT_NAMES[0],
                interactive=True,
                elem_id="client_selector"
            )
    
    with gr.Row():
        # Chat Interface (Left)
        with gr.Column(scale=7):
            chat = gr.ChatInterface(
                fn=predict,
                additional_inputs=[client_selector],
                examples=[
                    ["Analyze Amazon's retention risk and 2024 trends"],
                    ["Draft a meeting brief for Akamai Technologies"],
                    ["Search for Agentic AI research for David's Bridal"]
                ],
                fill_height=True
            )
            
        # Intelligence Panel (Right)
        with gr.Column(scale=5):
            with gr.Group(elem_classes="brief-panel"):
                gr.Markdown("### 📊 Business Intelligence & ROI")
                
                # Plotly Chart for Metrics
                metrics_plot = gr.Plot(value=create_metrics_plot(), show_label=False, container=False)
                
                gr.HTML("<hr>")
                
                gr.Markdown("#### 📋 Note to Associate")
                gr.Markdown("""
                *The information generated is validated by a dedicated **Critic Agent**. 
                Check the **Reasoning Traces** in the chat to see the verification steps.*
                """)
                
                gr.HTML("<hr>")
                
                gr.Markdown("#### 🔍 Active Realism Audit")
                # Using HTML for neon/led indicators
                gr.HTML("""
                <div style='display: flex; gap: 10px; align-items: center; color: #94A3B8;'>
                    <span style='width: 8px; height: 8px; background: #4ADE80; border-radius: 50%; box-shadow: 0 0 10px #4ADE80;'></span> GLM-4.7 Flash (Low Latency)
                </div>
                <div style='display: flex; gap: 10px; align-items: center; color: #94A3B8; margin-top: 5px;'>
                    <span style='width: 8px; height: 8px; background: #4ADE80; border-radius: 50%; box-shadow: 0 0 10px #4ADE80;'></span> Nexus Knowledge Base
                </div>
                <div style='display: flex; gap: 10px; align-items: center; color: #94A3B8; margin-top: 5px;'>
                    <span style='width: 8px; height: 8px; background: #60A5FA; border-radius: 50%; box-shadow: 0 0 10px #60A5FA;'></span> Synthesis-Critic Loop
                </div>
                """)

if __name__ == "__main__":
    demo.launch(
        share=False
    )

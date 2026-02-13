import json
import os
import time
from datetime import datetime
from collections import defaultdict

class EvalReportEngine:
    """Collects per-case evaluation results and generates rich reports."""
    
    def __init__(self, output_dir="evaluations/results"):
        self.results = []
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def log_case(self, test_name, case_id, query, agent_response,
                 retrieved_context, scores, reasoning, 
                 latency_ms, tokens_used, passed, metadata=None):
        """Append a single test case result to the session results."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "case_id": case_id,
            "query": query,
            "agent_response": agent_response,
            "retrieved_context": retrieved_context,
            "scores": scores,
            "reasoning": reasoning,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used if isinstance(tokens_used, dict) else {},
            "passed": passed,
            "metadata": metadata or {}
        }
        self.results.append(result)
        
        # Verbose terminal feedback
        status_icon = "✅" if passed else "❌"
        score_sum = ""
        if isinstance(scores, dict):
            score_sum = " | ".join([f"{k}:{v}" for k, v in scores.items()])
        
        print(f"{status_icon} [{test_name}] {query[:60]}... ({latency_ms:.0f}ms) {score_sum}")
        
    def generate_json_report(self):
        """Write all results to a JSON file."""
        filename = f"report_{self.run_id}.json"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w") as f:
            json.dump({
                "run_id": self.run_id,
                "generated_at": datetime.now().isoformat(),
                "summary": self._calculate_summary(),
                "results": self.results
            }, f, indent=2, default=str)
        return path

    def _calculate_summary(self):
        """Calculate aggregate metrics across all logged cases."""
        if not self.results:
            return {"total_cases": 0, "passed": 0, "failed": 0}
            
        by_test = defaultdict(list)
        for r in self.results:
            by_test[r["test_name"]].append(r)
        
        latencies = [r["latency_ms"] for r in self.results if r["latency_ms"] > 0]
        total_tokens = sum(r["tokens_used"].get("total", 0) for r in self.results if isinstance(r["tokens_used"], dict))
        
        per_test = {}
        for name, cases in by_test.items():
            passed_count = sum(1 for r in cases if r["passed"])
            case_latencies = [r["latency_ms"] for r in cases if r["latency_ms"] > 0]
            per_test[name] = {
                "count": len(cases),
                "passed": passed_count,
                "failed": len(cases) - passed_count,
                "pass_rate": passed_count / len(cases) if cases else 0,
                "avg_latency": sum(case_latencies) / len(case_latencies) if case_latencies else 0,
            }
            
        return {
            "total_cases": len(self.results),
            "passed": sum(1 for r in self.results if r["passed"]),
            "failed": sum(1 for r in self.results if not r["passed"]),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "total_tokens": total_tokens,
            "per_test_metrics": per_test,
            "test_suites_run": len(by_test),
        }

    def _generate_recommendations(self):
        """Auto-generate improvement recommendations based on failures."""
        recs = []
        by_test = defaultdict(list)
        for r in self.results:
            by_test[r["test_name"]].append(r)
        
        for name, cases in by_test.items():
            failures = [c for c in cases if not c["passed"]]
            if not failures:
                continue
                
            fail_rate = len(failures) / len(cases) * 100
            
            if name == "faithfulness":
                recs.append(f"🔴 **Faithfulness** ({fail_rate:.0f}% failures): Agent is making claims not grounded in retrieved context. Consider: (1) Strengthening the system prompt to only use retrieved evidence, (2) Increasing retrieval K to provide more context, (3) Adding a verification step in the agent workflow.")
            elif name == "answer_relevancy":
                recs.append(f"🔴 **Answer Relevancy** ({fail_rate:.0f}% failures): Responses are not directly addressing user queries. Consider: (1) Improving agent routing logic, (2) Tuning sub-agent prompts to be more focused, (3) Reducing unnecessary preamble in responses.")
            elif name == "context_precision":
                recs.append(f"🔴 **Context Precision** ({fail_rate:.0f}% failures): Retrieved chunks are not useful for answering queries. Consider: (1) Re-chunking documents with better overlap, (2) Tuning ChromaDB embedding model, (3) Adding metadata filters to narrow retrieval.")
            elif name == "retrieval":
                recs.append(f"🔴 **Retrieval** ({fail_rate:.0f}% failures): Expected documents not found in top results. Consider: (1) Re-ingesting with better embeddings, (2) Adjusting chunk sizes, (3) Adding keyword search fallback.")
            elif name == "tool_usage":
                recs.append(f"🔴 **Tool Usage** ({fail_rate:.0f}% failures): Agent not calling expected tools. Consider: (1) Strengthening tool descriptions, (2) Adding few-shot examples to agent prompts, (3) Reviewing tool name conventions.")
            elif name == "response_quality":
                recs.append(f"🔴 **Response Quality** ({fail_rate:.0f}% failures): LLM judge rated responses below threshold. Consider: (1) Improving sub-agent prompts, (2) Adding response formatting guidelines, (3) Testing with different LLM models.")
            elif name == "code_safety":
                recs.append(f"🔴 **Code Safety** ({fail_rate:.0f}% failures): Dangerous code patterns escaping sandbox. CRITICAL: Add stricter regex patterns and consider Docker-based execution.")
            elif name == "data_quality":
                recs.append(f"🟡 **Data Quality** ({fail_rate:.0f}% failures): Some data quality checks failing. Run data regeneration scripts and validate output.")
            elif name == "data_access":
                recs.append(f"🟡 **Data Access** ({fail_rate:.0f}% failures): Tool functions failing to retrieve data. Check JSON file paths and cross-reference integrity.")
            elif name == "executive_tools":
                recs.append(f"🟡 **Executive Tools** ({fail_rate:.0f}% failures): Executive aggregation tools returning incomplete data. Check data linkage between clients, associates, and performance files.")
            else:
                recs.append(f"🟡 **{name}** ({fail_rate:.0f}% failures): {len(failures)} test cases failed. Review the detailed results below for specific issues.")
        
        if not recs:
            recs.append("✅ **All tests passed!** No immediate improvements needed. Consider adding more edge-case test queries to strengthen coverage.")
        
        return recs

    def _generate_improvement_analysis(self):
        """Generate a deep-dive improvement analysis with error patterns and root causes."""
        by_test = defaultdict(list)
        for r in self.results:
            by_test[r["test_name"]].append(r)
        
        failures = [r for r in self.results if not r["passed"]]
        if not failures:
            return {"has_failures": False, "categories": {}, "priority_fixes": [], "failed_cases": []}
        
        # Classify failures into root cause categories
        categories = {
            "Retrieval Issues": [],
            "Prompt/Routing Issues": [],
            "Hallucination/Faithfulness": [],
            "Latency/Performance": [],
            "Data Quality/Access": [],
            "Safety/Sandbox": [],
            "Parse/System Errors": []
        }
        
        for f in failures:
            name = f["test_name"]
            if name in ("retrieval", "retrieval_aggregate", "context_precision"):
                categories["Retrieval Issues"].append(f)
            elif name in ("answer_relevancy", "response_quality", "response_quality_aggregate", "tool_usage", "tool_usage_aggregate"):
                categories["Prompt/Routing Issues"].append(f)
            elif name == "faithfulness":
                categories["Hallucination/Faithfulness"].append(f)
            elif name in ("latency_e2e", "latency_ttft"):
                categories["Latency/Performance"].append(f)
            elif name in ("data_quality", "data_access", "executive_tools"):
                categories["Data Quality/Access"].append(f)
            elif name == "code_safety":
                categories["Safety/Sandbox"].append(f)
            else:
                categories["Parse/System Errors"].append(f)
        
        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}
        
        # Generate priority fix list
        priority_fixes = []
        severity_order = [
            ("Safety/Sandbox", "CRITICAL", "#ef4444"),
            ("Hallucination/Faithfulness", "HIGH", "#f97316"),
            ("Retrieval Issues", "HIGH", "#f97316"),
            ("Prompt/Routing Issues", "MEDIUM", "#eab308"),
            ("Data Quality/Access", "MEDIUM", "#eab308"),
            ("Latency/Performance", "LOW", "#22d3ee"),
            ("Parse/System Errors", "LOW", "#22d3ee"),
        ]
        
        for cat_name, severity, color in severity_order:
            if cat_name in categories:
                count = len(categories[cat_name])
                priority_fixes.append({
                    "category": cat_name,
                    "severity": severity,
                    "color": color,
                    "count": count,
                    "sample_query": categories[cat_name][0]["query"][:60],
                    "sample_reasoning": categories[cat_name][0]["reasoning"][:200] if categories[cat_name][0]["reasoning"] else "N/A"
                })
        
        return {
            "has_failures": True,
            "categories": categories,
            "priority_fixes": priority_fixes,
            "failed_cases": failures,
            "total_failures": len(failures),
            "total_cases": len(self.results)
        }

    def _build_improvement_html(self, improvement):
        """Build the HTML for the Improvement Analysis section."""
        if not improvement.get("has_failures"):
            return """
            <div class="recs" style="border-left: 4px solid #4ade80;">
                <h3>🎉 Improvement Analysis — No Failures Detected</h3>
                <p style="color:#94a3b8;font-size:13px;">All evaluation tests passed. The system is performing within expected thresholds across all metrics. 
                Consider adding edge-case queries, adversarial prompts, or more complex multi-turn interactions to further stress-test the system.</p>
            </div>
            """
        
        # Priority Fix Matrix
        priority_html = ""
        for fix in improvement.get("priority_fixes", []):
            priority_html += f"""
            <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid #1f2937;">
                <span style="background:{fix['color']}20;color:{fix['color']};padding:3px 10px;border-radius:4px;font-size:10px;font-weight:700;border:1px solid {fix['color']}40;min-width:70px;text-align:center;">{fix['severity']}</span>
                <div style="flex:1;">
                    <div style="color:#f8fafc;font-size:13px;font-weight:600;">{fix['category']} ({fix['count']} failures)</div>
                    <div style="color:#64748b;font-size:11px;margin-top:2px;">Sample: {fix['sample_query']}...</div>
                </div>
            </div>
            """
        
        # Failed Case Deep-Dives
        failed_rows = ""
        for i, f in enumerate(improvement.get("failed_cases", [])[:20]):  # Cap at 20
            query_display = str(f["query"]).replace("<", "&lt;").replace(">", "&gt;")[:100]
            resp_display = str(f["agent_response"]).replace("<", "&lt;").replace(">", "&gt;")[:300]
            reasoning_display = str(f["reasoning"]).replace("<", "&lt;").replace(">", "&gt;")[:400]
            scores_display = ""
            if isinstance(f["scores"], dict):
                for k, v in f["scores"].items():
                    scores_display += f"<span style='display:inline-block;background:#ef444420;color:#ef4444;padding:2px 6px;border-radius:3px;font-size:10px;margin:1px 3px 1px 0;border:1px solid #ef444440;'>{k}: {v}</span>"
            
            failed_rows += f"""
            <tr style="border-bottom:1px solid #1f2937;">
                <td style="padding:10px;font-size:11px;color:#94a3b8;vertical-align:top;">{f['test_name']}</td>
                <td style="padding:10px;font-size:11px;color:#e2e8f0;vertical-align:top;max-width:200px;">{query_display}</td>
                <td style="padding:10px;vertical-align:top;">{scores_display}</td>
                <td style="padding:10px;font-size:11px;color:#94a3b8;vertical-align:top;max-width:250px;"><div style="max-height:120px;overflow-y:auto;white-space:pre-wrap;word-break:break-word;">{resp_display}</div></td>
                <td style="padding:10px;font-size:11px;color:#cbd5e1;vertical-align:top;max-width:300px;">{reasoning_display}</td>
            </tr>
            """
        
        return f"""
        <h2 class="section-title">🔬 Improvement Analysis — Deep Dive</h2>
        
        <div class="recs" style="border-left: 4px solid #ef4444;">
            <h3>📊 Priority Fix Matrix</h3>
            <p style="color:#94a3b8;font-size:12px;margin-bottom:12px;">{improvement['total_failures']} failures out of {improvement['total_cases']} total test cases. Ordered by severity.</p>
            {priority_html}
        </div>
        
        <div class="suite-section">
            <div class="suite-header" onclick="this.nextElementSibling.classList.toggle('collapsed')">
                <h3>🔍 Failed Case Deep-Dives (click to expand)</h3>
                <div class="suite-stats">
                    <span class="stat-fail">{improvement['total_failures']} failures</span>
                </div>
            </div>
            <div class="suite-body">
                <table class="case-table">
                    <thead>
                        <tr>
                            <th>Suite</th>
                            <th>Query / Input</th>
                            <th>Scores</th>
                            <th>Agent Response</th>
                            <th>Judge Reasoning / Analysis</th>
                        </tr>
                    </thead>
                    <tbody>
                        {failed_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def generate_html_report(self):
        """Generate a comprehensive HTML dashboard."""
        filename = f"report_{self.run_id}.html"
        path = os.path.join(self.output_dir, filename)
        summary = self._calculate_summary()
        recommendations = self._generate_recommendations()
        improvement = self._generate_improvement_analysis()
        
        by_test = defaultdict(list)
        for r in self.results:
            by_test[r["test_name"]].append(r)
        
        pass_rate_pct = (summary["passed"] / max(summary["total_cases"], 1)) * 100

        # Build per-suite sections
        suite_sections_html = ""
        for suite_name, cases in by_test.items():
            suite_passed = sum(1 for c in cases if c["passed"])
            suite_failed = len(cases) - suite_passed
            suite_status = "✅" if suite_failed == 0 else "❌"
            
            rows_html = ""
            for r in cases:
                status_class = "status-pass" if r["passed"] else "status-fail"
                status_text = "✅ PASS" if r["passed"] else "❌ FAIL"
                
                # Format scores
                scores_html = ""
                if isinstance(r["scores"], dict):
                    for k, v in r["scores"].items():
                        color = "#4ade80" if (isinstance(v, (int, float)) and v >= 0.5) or v == True else "#f97316"
                        scores_html += f'<span style="display:inline-block;background:{color}20;color:{color};padding:2px 8px;border-radius:4px;font-size:11px;margin:2px 4px 2px 0;border:1px solid {color}40;">{k}: {v}</span>'
                
                # Format response (show full, scrollable)
                resp = str(r["agent_response"]).replace("<", "&lt;").replace(">", "&gt;")
                query_display = str(r["query"]).replace("<", "&lt;").replace(">", "&gt;")
                context_display = str(r.get("retrieved_context", "N/A")).replace("<", "&lt;").replace(">", "&gt;")
                reasoning_display = str(r["reasoning"]).replace("<", "&lt;").replace(">", "&gt;")
                
                # Token info
                token_info = ""
                if isinstance(r["tokens_used"], dict) and r["tokens_used"]:
                    for tk, tv in r["tokens_used"].items():
                        token_info += f"{tk}: {tv} "
                
                rows_html += f"""
                <tr class="case-row {'case-fail' if not r['passed'] else ''}">
                    <td><span class="{status_class}">{status_text}</span></td>
                    <td style="min-width:220px;">
                        <div class="query-text">{query_display}</div>
                    </td>
                    <td style="min-width:300px;">
                        <div class="resp-text">{resp}</div>
                    </td>
                    <td style="min-width:180px;">
                        {scores_html}
                        <div class="meta-info">
                            Latency: {r['latency_ms']:.0f}ms<br>
                            {f'Tokens: {token_info}' if token_info else ''}
                        </div>
                    </td>
                    <td style="min-width:250px;">
                        <div class="reasoning-text">{reasoning_display}</div>
                    </td>
                </tr>
"""
            
            suite_sections_html += f"""
            <div class="suite-section">
                <div class="suite-header" onclick="this.nextElementSibling.classList.toggle('collapsed')">
                    <h3>{suite_status} {suite_name.upper().replace('_',' ')}</h3>
                    <div class="suite-stats">
                        <span class="stat-pass">{suite_passed} passed</span>
                        <span class="stat-fail">{suite_failed} failed</span>
                        <span class="stat-total">{len(cases)} total</span>
                    </div>
                </div>
                <div class="suite-body">
                    <table class="case-table">
                        <thead>
                            <tr>
                                <th style="width:80px;">Status</th>
                                <th>Query / Test Input</th>
                                <th>Agent Response / Output</th>
                                <th>Metrics & Scores</th>
                                <th>Reasoning & Analysis</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
"""

        # Build recommendations HTML
        recs_html = "\n".join([f"<li>{r}</li>" for r in recommendations])
        
        # Build summary cards for each suite
        suite_cards_html = ""
        for name, metrics in summary.get("per_test_metrics", {}).items():
            pr = metrics["pass_rate"] * 100
            color = "#4ade80" if pr == 100 else "#f97316" if pr >= 50 else "#ef4444"
            suite_cards_html += f"""
            <div class="suite-card">
                <div class="suite-card-name">{name.upper().replace('_',' ')}</div>
                <div class="suite-card-rate" style="color:{color};">{pr:.0f}%</div>
                <div class="suite-card-detail">{metrics['passed']}/{metrics['count']} passed</div>
                {f'<div class="suite-card-detail">Avg: {metrics["avg_latency"]:.0f}ms</div>' if metrics["avg_latency"] > 0 else ''}
            </div>
"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Nexus Advisor — Evaluation Report {self.run_id}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0a0f1a; color: #e2e8f0; padding: 24px; line-height: 1.6; }}
        
        .header {{ border-bottom: 2px solid #22d3ee; padding-bottom: 16px; margin-bottom: 32px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 22px; color: #f8fafc; }}
        .header small {{ color: #94a3b8; font-size: 12px; }}
        
        .summary-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 32px; }}
        .card {{ background: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 12px; }}
        .card-title {{ color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
        .card-value {{ font-size: 28px; font-weight: 800; }}
        .card-value.good {{ color: #4ade80; }}
        .card-value.warn {{ color: #f97316; }}
        .card-value.bad {{ color: #ef4444; }}
        
        .suite-overview {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 32px; }}
        .suite-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 14px 18px; min-width: 140px; text-align: center; }}
        .suite-card-name {{ font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; margin-bottom: 4px; }}
        .suite-card-rate {{ font-size: 24px; font-weight: 800; }}
        .suite-card-detail {{ font-size: 11px; color: #64748b; }}
        
        .section-title {{ font-size: 18px; font-weight: 700; color: #f8fafc; margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 1px solid #334155; }}
        
        .recs {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 32px; }}
        .recs h3 {{ color: #f8fafc; margin-bottom: 12px; font-size: 16px; }}
        .recs ul {{ list-style: none; padding: 0; }}
        .recs li {{ padding: 8px 0; border-bottom: 1px solid #1e293b; font-size: 13px; line-height: 1.8; }}
        .recs li:last-child {{ border-bottom: none; }}
        
        .suite-section {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; margin-bottom: 20px; overflow: hidden; }}
        .suite-header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #1e293b; cursor: pointer; user-select: none; }}
        .suite-header:hover {{ background: #263243; }}
        .suite-header h3 {{ font-size: 14px; color: #f8fafc; }}
        .suite-stats {{ display: flex; gap: 12px; }}
        .stat-pass {{ color: #4ade80; font-size: 12px; font-weight: 600; }}
        .stat-fail {{ color: #ef4444; font-size: 12px; font-weight: 600; }}
        .stat-total {{ color: #94a3b8; font-size: 12px; }}
        
        .suite-body {{ padding: 0; }}
        .suite-body.collapsed {{ display: none; }}
        
        .case-table {{ width: 100%; border-collapse: collapse; }}
        .case-table th {{ background: #0f172a; text-align: left; padding: 10px 14px; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #64748b; border-bottom: 1px solid #1f2937; }}
        .case-table td {{ padding: 12px 14px; border-bottom: 1px solid #1f2937; font-size: 12px; vertical-align: top; }}
        .case-row:hover {{ background: #1e293b40; }}
        .case-fail {{ background: #ef444410; }}
        .case-fail:hover {{ background: #ef444420; }}
        
        .status-pass {{ color: #4ade80; font-weight: 700; font-size: 11px; }}
        .status-fail {{ color: #ef4444; font-weight: 700; font-size: 11px; }}
        
        .query-text {{ font-weight: 600; color: #e2e8f0; font-size: 12px; line-height: 1.5; }}
        .resp-text {{ color: #94a3b8; font-size: 11px; max-height: 200px; overflow-y: auto; white-space: pre-wrap; word-break: break-word; padding: 8px; background: #0a0f1a; border-radius: 6px; border: 1px solid #1f2937; }}
        .reasoning-text {{ color: #cbd5e1; font-size: 11px; line-height: 1.6; }}
        .meta-info {{ font-size: 10px; color: #64748b; margin-top: 6px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Nexus Strategic Advisor — Evaluation Report</h1>
        <div>
            <small>Run ID: {self.run_id}</small><br>
            <small>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</small>
        </div>
    </div>

    <div class="summary-grid">
        <div class="card">
            <div class="card-title">Pass Rate</div>
            <div class="card-value {'good' if pass_rate_pct == 100 else 'warn' if pass_rate_pct >= 70 else 'bad'}">{summary['passed']}/{summary['total_cases']} ({pass_rate_pct:.1f}%)</div>
        </div>
        <div class="card">
            <div class="card-title">Tests Executed</div>
            <div class="card-value good">{summary['total_cases']}</div>
        </div>
        <div class="card">
            <div class="card-title">Test Suites</div>
            <div class="card-value good">{summary.get('test_suites_run', 0)}</div>
        </div>
        <div class="card">
            <div class="card-title">Avg Latency</div>
            <div class="card-value {'good' if summary['avg_latency_ms'] < 5000 else 'warn'}">{summary['avg_latency_ms']:.0f}ms</div>
        </div>
        <div class="card">
            <div class="card-title">Total Tokens</div>
            <div class="card-value good">{summary['total_tokens']}</div>
        </div>
    </div>

    <h2 class="section-title">📊 Per-Suite Breakdown</h2>
    <div class="suite-overview">
        {suite_cards_html}
    </div>

    <div class="recs">
        <h3>💡 Recommendations & Improvement Areas</h3>
        <ul>
            {recs_html}
        </ul>
    </div>

    <h2 class="section-title">📋 Detailed Test Results</h2>
    {suite_sections_html}

    {self._build_improvement_html(improvement)}

    <div style="text-align:center;padding:32px;color:#475569;font-size:11px;">
        Nexus Strategic Advisor Evaluation Framework v2.0 — Generated by EvalReportEngine
    </div>
</body>
</html>"""

        with open(path, "w") as f:
            f.write(html)
        return path

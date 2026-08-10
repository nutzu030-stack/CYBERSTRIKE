from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database of distinct attack scenarios
SCENARIOS = {
    "m365_phish": {
        "title": "Microsoft 365 Password Expiration",
        "description": "Standard credential harvesting phish targeting enterprise identity.",
        "start_node": "m365_inbox",
        "nodes": {
            "m365_inbox": {
                "id": "m365_inbox",
                "title": "Suspicious Email Received",
                "email_headers": {
                    "from": "IT Security <support@sec-update-portal.com>",
                    "reply_to": "admin-verify@net-check.xyz",
                    "subject": "URGENT: Password Expiration in 2 Hours",
                    "spf_pass": False,
                    "dkim_pass": False
                },
                "email_body": "Your corporate access expires in 2 hours. Click below to verify your credentials immediately.",
                "options": [
                    {"id": "inspect", "text": "🔍 Inspect Headers", "next_node": "m365_inspect", "risk_delta": 0, "log": "Inspected headers."},
                    {"id": "click", "text": "🔗 Click Link", "next_node": "m365_phish_page", "risk_delta": 25, "log": "Clicked unverified link."},
                    {"id": "report", "text": "🛡️ Report to SOC", "next_node": "node_summary", "risk_delta": -10, "log": "Reported phish immediately."}
                ]
            },
            "m365_inspect": {
                "id": "m365_inspect",
                "title": "Header Inspection",
                "email_body": "⚠️ SPF/DKIM Failed! Sender domain 'sec-update-portal.com' is unverified.",
                "options": [
                    {"id": "report_after", "text": "🛡️ Report to SOC", "next_node": "node_summary", "risk_delta": -20, "log": "Confirmed phish via headers and reported."},
                    {"id": "click_override", "text": "⚠️ Click Link Anyway", "next_node": "m365_phish_page", "risk_delta": 40, "log": "Overrode header warning."}
                ]
            },
            "m365_phish_page": {
                "id": "m365_phish_page",
                "title": "Fake Login Portal",
                "url_bar": "https://login.microsoft.sec-update-portal.com",
                "email_body": "You were navigated to a fake single sign-on page.",
                "options": [
                    {"id": "enter_creds", "text": "🔑 Enter Credentials", "next_node": "node_summary", "risk_delta": 50, "log": "Submitted credentials to phishing site."},
                    {"id": "close", "text": "❌ Abort & Report", "next_node": "node_summary", "risk_delta": 0, "log": "Aborted on landing page."}
                ]
            }
        }
    },
    "bec_fraud": {
        "title": "CEO Urgent Wire Transfer (BEC)",
        "description": "Business Email Compromise targeting finance personnel with high urgency.",
        "start_node": "bec_inbox",
        "nodes": {
            "bec_inbox": {
                "id": "bec_inbox",
                "title": "Direct Message from CEO",
                "email_headers": {
                    "from": "CEO John Doe <john.doe.exec@gmail.com>",
                    "reply_to": "john.doe.exec@gmail.com",
                    "subject": "Confidential Acquisition - Urgent Wire Needed",
                    "spf_pass": True,
                    "dkim_pass": True
                },
                "email_body": "I am in a private meeting. I need an urgent $45,000 wire transfer executed before 5 PM for an NDA acquisition. Do not call my phone.",
                "options": [
                    {"id": "execute", "text": "💸 Process Wire Immediately", "next_node": "node_summary", "risk_delta": 80, "log": "Executed unauthorized financial wire without out-of-band verification."},
                    {"id": "verify_phone", "text": "📞 Call CEO via Internal Directory Number", "next_node": "node_summary", "risk_delta": -20, "log": "Used secondary channel to verify wire request."},
                    {"id": "check_email", "text": "🔍 Inspect Sender Address", "next_node": "bec_inspect", "risk_delta": 0, "log": "Noticed external @gmail.com address."}
                ]
            },
            "bec_inspect": {
                "id": "bec_inspect",
                "title": "Sender Address Analysis",
                "email_body": "⚠️ Notice: Email originated from an external @gmail.com address, not @company.com.",
                "options": [
                    {"id": "report_bec", "text": "🛡️ Flag as Impersonation / BEC", "next_node": "node_summary", "risk_delta": -20, "log": "Caught executive impersonation attack."}
                ]
            }
        }
    }
}

SUMMARY_NODE = {
    "id": "node_summary",
    "title": "SOC Simulation Debrief",
    "email_body": "Simulation concluded. Review your audit telemetry log.",
    "options": []
}

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Returns list of available scenarios for the frontend menu."""
    return jsonify([
        {"key": key, "title": data["title"], "description": data["description"]}
        for key, data in SCENARIOS.items()
    ])

@app.route('/api/start', methods=['GET', 'POST'])
def start_simulation():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
    else:
        data = request.args.to_dict()

    scenario_key = data.get("scenario", "m365_phish")
    
    scenario = SCENARIOS.get(scenario_key, SCENARIOS["m365_phish"])
    start_node_id = scenario["start_node"]
    first_node = scenario["nodes"][start_node_id]

    return jsonify({
        "scenario_key": scenario_key,
        "current_node": first_node,
        "risk_score": 0,
        "history": [],
        "is_completed": False
    })

@app.route('/api/next', methods=['GET', 'POST'])
def next_stage():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
    else:
        data = request.args.to_dict()
    
    scenario_key = data.get("scenario_key", "m365_phish")
    current_node_id = data.get("current_node_id", "")
    option_id = data.get("option_id", "")
    current_risk = int(data.get("risk_score", 0))
    history = data.get("history", [])

    scenario = SCENARIOS.get(scenario_key, SCENARIOS["m365_phish"])
    current_node = scenario["nodes"].get(current_node_id, {})
    
    selected_option = next((opt for opt in current_node.get("options", []) if opt["id"] == option_id), None)

    if selected_option:
        current_risk = max(0, min(100, current_risk + selected_option["risk_delta"]))
        history.append({
            "step": len(history) + 1,
            "action": selected_option["text"],
            "log": selected_option["log"],
            "risk_impact": selected_option["risk_delta"]
        })
        next_node_id = selected_option["next_node"]
    else:
        next_node_id = current_node_id

    if next_node_id == "node_summary":
        next_node = SUMMARY_NODE
        is_completed = True
    else:
        next_node = scenario["nodes"].get(next_node_id, SUMMARY_NODE)
        is_completed = False

    return jsonify({
        "scenario_key": scenario_key,
        "current_node": next_node,
        "risk_score": current_risk,
        "history": history,
        "is_completed": is_completed
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
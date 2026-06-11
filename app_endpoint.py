import os
from flask import Flask, request, jsonify
from database_freemium_methods import db
from typeform_webhook import parse_typeform_lead, parse_tally_lead

app = Flask(__name__)

try:
    db.init_table()
except Exception as e:
    print(f"DB init deferred: {e}")


# ── Health check ─────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "aura-freemium"}), 200


# ── Tally.so webhook ──────────────────────────────────────────────────────────

@app.route("/tally-lead", methods=["POST"])
def tally_lead():
    payload = request.get_json(force=True, silent=True) or {}
    lead = parse_tally_lead(payload)
    if not lead.get("email"):
        return jsonify({"error": "no email in payload"}), 400
    lead_id = db.save_lead(lead)
    return jsonify({"ok": True, "lead_id": lead_id}), 200


# ── Typeform webhook (kept for reference) ────────────────────────────────────

@app.route("/typeform-lead", methods=["POST"])
def typeform_lead():
    payload = request.get_json(force=True, silent=True) or {}
    lead = parse_typeform_lead(payload)
    if not lead.get("email"):
        return jsonify({"error": "no email in payload"}), 400
    lead_id = db.save_lead(lead)
    return jsonify({"ok": True, "lead_id": lead_id}), 200


# ── Agent App polling endpoints ───────────────────────────────────────────────

@app.route("/admin/pending-leads", methods=["GET"])
def pending_leads():
    leads = db.get_pending_leads()
    return jsonify([dict(r) for r in leads]), 200


@app.route("/admin/lead-status/<int:lead_id>", methods=["PATCH"])
def update_lead_status(lead_id):
    body = request.get_json(force=True, silent=True) or {}
    status = body.get("status")
    if not status:
        return jsonify({"error": "status required"}), 400
    db.update_status(lead_id, status)
    return jsonify({"ok": True}), 200


@app.route("/admin/all-leads", methods=["GET"])
def all_leads():
    limit = int(request.args.get("limit", 100))
    leads = db.get_all_leads(limit=limit)
    return jsonify([dict(r) for r in leads]), 200


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
